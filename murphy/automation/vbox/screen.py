import os
import subprocess
from pathlib import Path
from tempfile import NamedTemporaryFile

from murphy.automation import MurphyFactory, Screen


class VirtualboxScreen(Screen):
    """VirtualboxScreen based implementation of Screen."""
    def __init__(self, factory: MurphyFactory):
        self._machine_id = factory()

    def screenshot(self, path: Path=None) -> Path:
        if path is not None:
            screenshot = str(path)
        else:
            screenshot = NamedTemporaryFile(delete=False, suffix='.png').name

        vbox_screenshot(self._machine_id, screenshot)

        return Path(screenshot)


def vbox_screenshot(machine: str, path: Path):
    command = (VBOX_MANAGER, 'controlvm', machine, 'screenshotpng', str(path))
    process = subprocess.Popen(
        command, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)

    process.wait(timeout=TIMEOUT)


TIMEOUT = 3
VBOX_MANAGER = os.getenv('VBOX_MANAGER', default='vboxmanage')
