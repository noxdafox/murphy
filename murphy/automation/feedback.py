from murphy.automation import Feedback

from murphy.automation.vnc import VNCFactory, VNCScreen
from murphy.automation.libvirt import LibvirtFactory, LibvirtLoad


class LibvirtFeedback(Feedback):
    """Libvirt based Feedback implementation."""
    def __init__(self, vnc_server: str, domain_identifier: (int, str)):
        self._load = None
        self._screen = None
        self._vnc = VNCFactory(vnc_server)
        self._libvirt = LibvirtFactory(domain_identifier)

    @property
    def screen(self) -> VNCScreen:
        if self._screen is None:
            self._screen = VNCScreen(self._vnc)

        return self._screen

    @property
    def load(self) -> LibvirtLoad:
        if self._load is None:
            self._load = LibvirtLoad(self._libvirt)

        return self._load
