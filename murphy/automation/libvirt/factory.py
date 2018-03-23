import re

import libvirt

from murphy.automation import MurphyFactory


class LibvirtFactory(MurphyFactory):
    """Factory class for libvirt-based automation.

    The domain_identifier must be related to an existing libvirt domain.
    It can be either the domain ID, the UUID or its name.

    """
    def __init__(self, domain_identifier: (int, str),
                 libvirt_uri: str='qemu:///system'):
        self._domain = None
        self._domain_id = domain_identifier
        self._libvirt_uri = libvirt_uri

    def __call__(self) -> libvirt.virDomain:
        if self._domain is None:
            connection = libvirt.open(self._libvirt_uri)

            if isinstance(self._domain_id, int):
                self._domain = connection.lookupByID(self._domain_id)
            elif re.match(UUID_EXPR, self._domain_id):
                self._domain = connection.lookupByUUIDString(self._domain_id)
            else:
                self._domain = connection.lookupByName(self._domain_id)

        return self._domain


UUID_EXPR = "[a-fA-F0-9]{8}-[a-fA-F0-9]{4}-4[a-fA-F0-9]{3}-" + \
            "[89aAbB][a-fA-F0-9]{3}-[a-fA-F0-9]{12}"
