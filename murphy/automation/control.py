from murphy.automation import Control

from murphy.automation.libvirt import LibvirtFactory, LibvirtState
from murphy.automation.vnc import VNCFactory, VNCMouse, VNCKeyboard
from murphy.automation.virtualbox import VirtualboxFactory, VirtualboxState
from murphy.automation.virtualbox import VirtualboxMouse, VirtualboxKeyboard


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


class VirtualboxControl(Control):
    """Virtualbox based Control implementation."""
    def __init__(self, machine_identifier: str):
        self._state = None
        self._mouse = None
        self._keyboard = None
        self._virtualbox = VirtualboxFactory(machine_identifier)

    @property
    def mouse(self) -> VirtualboxMouse:
        if self._mouse is None:
            self._mouse = VirtualboxMouse(self._virtualbox)

        return self._mouse

    @property
    def keyboard(self) -> VirtualboxKeyboard:
        if self._keyboard is None:
            self._keyboard = VirtualboxKeyboard(self._virtualbox)

        return self._keyboard

    @property
    def state(self) -> VirtualboxState:
        if self._state is None:
            self._state = VirtualboxState(self._virtualbox)

        return self._state
