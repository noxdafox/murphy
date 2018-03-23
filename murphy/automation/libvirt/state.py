from datetime import datetime

from murphy.automation import MurphyFactory, DeviceState


class LibvirtState(DeviceState):
    """Libvirt based implementation of DeviceState."""
    SNAPSHOT_XML = """
    <domainsnapshot>
      <name>{0}</name>
      <description>{1}</description>
    </domainsnapshot>
    """

    def __init__(self, factory: MurphyFactory):
        self._domain = factory()

    def save(self) -> str:
        """Take a libvirt snapshot of the device state."""
        snapshot_name = datetime.now().isoformat()

        snapshot_xml = self.SNAPSHOT_XML.format(
            snapshot_name, 'Disk Checkpoint')
        snapshot = self._domain.snapshotCreateXML(snapshot_xml)

        return snapshot.getName()

    def restore(self, state: str):
        """Restore the device state to the given libvirt snapshot."""
        snapshot = self._domain.snapshotLookupByName(state)
        self._domain.revertToSnapshot(snapshot)
