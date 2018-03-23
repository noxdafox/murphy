from murphy.automation import Control

from murphy.automation.libvirt import LibvirtFactory, LibvirtState
from murphy.automation.vnc import VNCFactory, VNCMouse, VNCKeyboard


class LibvirtControl(Control):
    """Libvirt based Control implementation."""
    def __init__(self, vnc_server: str, domain_identifier: (int, str)):
        self._state = None
        self._mouse = None
        self._keyboard = None
        self._vnc = VNCFactory(vnc_server)
        self._libvirt = LibvirtFactory(domain_identifier)

    @property
    def mouse(self) -> VNCMouse:
        if self._mouse is None:
            self._mouse = VNCMouse(self._vnc)

        return self._mouse

    @property
    def keyboard(self) -> VNCKeyboard:
        if self._keyboard is None:
            self._keyboard = VNCKeyboard(self._vnc)

        return self._keyboard

    @property
    def state(self) -> LibvirtState:
        if self._state is None:
            self._state = LibvirtState(self._libvirt)

        return self._state
