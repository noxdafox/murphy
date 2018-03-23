from io import BytesIO
from pathlib import Path
from tempfile import NamedTemporaryFile

import libvirt
from PIL import Image

from murphy.automation import MurphyFactory, Screen


class LibvirtScreen(Screen):
    """Libvirt based implementation of Screen."""
    def __init__(self, factory: MurphyFactory):
        self._domain = factory()

    def screenshot(self, path: Path=None) -> Path:
        if path is not None:
            screenshot = str(path)
        else:
            screenshot = NamedTemporaryFile(delete=False, suffix='.png').name

        stream = libvirt_screenshot(self._domain)
        stream.seek(0)
        image = Image.open(stream)
        image.save(str(screenshot))

        return Path(screenshot)


def libvirt_screenshot(domain: libvirt.virDomain) -> BytesIO:
    """Takes a screenshot of the vnc connection of the guest.
    The resulting image file will be in Portable Pixmap format (PPM).

    """
    def handler(_, buff, file_handler):
        file_handler.write(buff)

    string = BytesIO()
    stream = domain.connect().newStream(0)

    try:
        domain.screenshot(stream, 0, 0)
        stream.recvAll(handler, string)
    except Exception as error:
        stream.abort()

        raise RuntimeError("Unable to take screenshot") from error
    else:
        stream.finish()

    return string
