from datetime import datetime

from murphy.automation import MurphyFactory, DeviceState


class VirtualBoxState(DeviceState):
    """VirtualBox based implementation of DeviceState."""
    def __init__(self, factory: MurphyFactory):
        self._machine = factory()

    def save(self) -> str:
        """Take a libvirt snapshot of the device state."""
        snapshot_name = datetime.now().isoformat()

        with self._machine.create_session() as _session:
            progress = self._machine.take_snapshot(
                snapshot_name, 'Disk Checkpoint', True)

            progress.wait_for_completion()

        return snapshot_name

    def restore(self, state: str):
        """Restore the device state to the given snapshot."""
        with self._machine.create_session() as _session:
            snapshot = self._machine.find_snapshot(state)
            progress = self._machine.restore_snapshot(snapshot)

            progress.wait_for_completion()
