from pathlib import Path
from typing import NamedTuple


Coordinates = NamedTuple('Coordinates', (('left', int),
                                         ('top', int),
                                         ('right', int),
                                         ('bottom', int)))
"""Rectangle coordinates."""


class WindowNotFoundError(RuntimeError):
    """Raised if no Window under focus could be found."""
    pass


class Interpreter:
    """The Interpreter class is responsible for interpreting
    the information provided by the automation.Feedback interface
    and provides a formal description of the state of the GUI application.

    """
    control = NotImplemented   # Type: Control
    """The Interpreter Control object."""

    feedback = NotImplemented  # Type: Feedback
    """The Interpreter Feedback object."""

    def interpret_state(self) -> 'State':
        """Interpret the current state and return its description."""
        raise NotImplementedError()

    def load_state(self, path: Path) -> 'State':
        """Load a state from a previous dump."""
        raise NotImplementedError()


class State:
    """The State is the formal description of the GUI application
    at a given moment.

    The State allows to access static information such as
    the window content and device load as well as the available Actions
    a User can perform.

    The State provides comparison facilities to help tracing
    the execution of the GUI application.

    """
    busy = NotImplemented     # Type: bool
    """If the device is busy."""

    window = NotImplemented   # Type: Window
    """Window under focus."""

    actions = NotImplemented  # Type: tuple
    """List of available Actions."""

    def __eq__(self, state: 'State') -> bool:
        """Equality comparison of the current state."""
        raise NotImplementedError()

    def save(self):
        """Save the current GUI application state.

        It is the User's responsibility to ensure the saved state
        is the one represented by the State object.

        """
        pass

    def restore(self):
        """Restore the GUI application state to this State
        if it was previously saved.

        """
        pass

    def dump(self, path: Path):
        """Dump a representation of the State to the given path.

        The State representation is implementation specific.

        The Window Image should be saved as image file with a common format.

        """
        pass


class Window:
    """The Window class encapsulates the static information
    found within the window under focus.

    """
    title = NotImplemented        # Type: str
    """The Window title."""

    text = NotImplemented         # Type: str
    """Aggregated text visible in the Window."""

    image = NotImplemented        # Type: Any
    """The image containing the Window representation."""

    coordinates = NotImplemented  # Type: Coordinates
    """Absolute coordinates of the Window."""


class Action:
    """An action is an object within a Window which can be activated.

    Performing an action is expected to change the State of the GUI.

    """
    text = NotImplemented         # Type: str
    """The visible text within the object."""

    image = NotImplemented        # Type: Any
    """The image containing the object representation."""

    coordinates = NotImplemented  # Type: Coordinates
    """Coordinates of the action relative to its Window."""

    def perform(self):
        """Perform the given action."""
        raise NotImplementedError()


class Button(Action):
    """Single left-click Button.

    Usually, radio and tick buttons fall in this category.

    """
    pass


class TextBox(Action):
    """Editable Text Box."""
    pass


class Link(Action):
    """HyperLink."""
    pass


class ComboBox(Action):
    """Combo Boxes are also referred as drop-down lists.

    The drop-down elements are listed within the items attribute.

    """
    items = None
    """Items listed within the ComboBox."""
