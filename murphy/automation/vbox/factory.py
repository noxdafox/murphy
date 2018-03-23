from murphy.automation import MurphyFactory


class VirtualboxFactory(MurphyFactory):
    """Factory class for Virtualbox-based automation.

    The machine_identifier must be related to an existing Virtualbox machine.
    It can be either the machine ID, or its name.

    """
    def __init__(self, machine_identifier: str):
        self._machine_itentifier = machine_identifier

    def __call__(self) -> str:
        return self._machine_itentifier
