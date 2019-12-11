import time

from datetime import datetime

from murphy.automation import MurphyFactory, DeviceState


class VirtualboxState(DeviceState):
    """VirtualBox based implementation of DeviceState."""
    def __init__(self, factory: MurphyFactory):
        self._machine = factory()

    def save(self) -> str:
        """Take a snapshot of the device state."""
        snapshot_name = datetime.now().isoformat()

        with self._machine.create_session() as session:
            progress, _snapshot_id = session.machine.take_snapshot(
                snapshot_name, 'Disk Checkpoint', True)
            progress.wait_for_completion()

        return snapshot_name

    def restore(self, state: str):
        """Restore the device state to the given snapshot."""
        with self._machine.create_session() as session:
            snapshot = session.machine.find_snapshot(state)

            progress = session.console.power_down()
            progress.wait_for_completion()

        with self._machine.create_session() as session:
            progress = session.machine.restore_snapshot(snapshot)
            progress.wait_for_completion()

        # Snapshot restoring progress does not block properly
        time.sleep(3)

        progress = self._machine.launch_vm_process()
        progress.wait_for_completion()

    def discard(self, state: str):
        """Discard the given device state deleting its virtualbox snapshot."""
        with self._machine.create_session() as session:
            snapshot = session.machine.find_snapshot(state)
            session.machine.delete_snapshot(snapshot.id_p)
