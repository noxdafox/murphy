from pathlib import Path
from tempfile import NamedTemporaryFile

from murphy.automation import MurphyFactory, Screen


class VNCScreen(Screen):
    """VNCDoTool based implementation of Screen."""
    def __init__(self, factory: MurphyFactory):
        self._client = factory()

    @property
    def timeout(self) -> int:
        return self._client.timeout

    @timeout.setter
    def timeout(self, value: int):
        self._client.timeout = value

    def screenshot(self, path: Path=None) -> Path:
        if path is not None:
            screenshot = str(path)
        else:
            screenshot = NamedTemporaryFile(delete=False, suffix='.png').name

        self._client.captureScreen(screenshot)

        return Path(screenshot)
