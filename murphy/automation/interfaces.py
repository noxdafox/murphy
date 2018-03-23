"""Interface API for Murphy feedback."""


from typing import Any
from pathlib import Path
from contextlib import contextmanager


class Control:
    """Group control-related interfaces."""
    mouse = NotImplemented   # Type: Mouse
    """The Mouse Control interface."""

    keyboard = NotImplemented  # Type: Keyboard
    """The Keyboard Control interface."""

    state = NotImplemented  # Type: DeviceState
    """The DeviceState Control interface."""


class Feedback:
    """Group feedback-related interfaces."""
    screen = NotImplemented   # Type: Screen
    """The Screen Feedback interface."""

    load = NotImplemented  # Type: Load
    """The Load Feedback interface."""


class Mouse:
    """Class representing the mouse of the device."""
    def __init__(self, factory: 'MurphyFactory'):
        pass

    def move(self, xcoord: int, ycoord: int):
        """Move the cursor to the given co-ordinates."""
        raise NotImplementedError()

    def click(self, button: Any ='left-click'):
        """Click the given button.
        The button representation is implementation specific.

        Default to left button.

        """
        raise NotImplementedError()


class Keyboard:
    """Class representing the keyboard of the device.

    The key mapping is implementation dependent.

    """
    def __init__(self, factory: 'MurphyFactory'):
        pass

    def type(self, text: str):
        """Input text on the keyboard.
        Capital letters are dealt transparently.

        """
        raise NotImplementedError()

    def press(self, key: Any):
        """Press a key.
        Special keys representation is implementation specific.

        """
        raise NotImplementedError()

    @contextmanager
    def hold(self, key: (Any, list, tuple)):
        """Keep one or more keys pressed within the context manager."""
        raise NotImplementedError()


class DeviceState:
    """Class encapsulating the Device State.

    Useful for taking checkpoints during execution.

    The state representation is opaque to the interface.

    """
    def __init__(self, factory: 'MurphyFactory'):
        pass

    def save(self) -> Any:
        """Save the state of the device.

        The returned type is opaque.

        """
        raise NotImplementedError()

    def restore(self, state: Any):
        """Restore the device to the saved state.

        The state type is opaque.

        """
        raise NotImplementedError()


class Screen:
    """Class representing the screen of the device."""
    def __init__(self, factory: 'MurphyFactory'):
        pass

    def screenshot(self, path: Path=None) -> Path:
        """Take a frame of the screen and store it as screenshot
        in a file at the given path.

        If Path is not given, a unique one is generated in TMPDIR.

        """
        pass


class LoadAverage:
    """Class representing the average load of the device.

    Load is expressed in percentage as float value.

    Values should range from 0.0 (idle) to 1.0 (busy).

    """
    cpu = NotImplemented   # Type: float
    """The CPU load average in percentage."""

    disk = NotImplemented  # Type: float
    """The Disk load average in percentage."""

    network = NotImplemented  # Type: float
    """The Network load average in percentage."""

    def __init__(self, factory: 'MurphyFactory'):
        pass


class MurphyFactory:
    """Factory class for the interfaces."""
    def __call__(self):
        """Execute the Factory logic."""
        raise NotImplementedError()