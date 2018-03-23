"""Model implementation for Windows."""


import os
import json
import logging
from pathlib import Path
from random import randint
from collections import Counter
from typing import Any, NamedTuple

from PIL import Image

from murphy.model.utils import absolute_coordinates
from murphy.model import scrapers, Interpreter, State, Window
from murphy.model import Action, Button, TextBox, Link, ComboBox
from murphy.model.interpreters.windows_image import compare_images


Tolerance = NamedTuple('Tolerance', (('image', float),  # image comparison
                                     ('load', tuple)))  # device load comparison
DEFAULT_TOLERANCE = Tolerance(1.0, (0.10, 0.1, 0.1))


class WindowsInterpreter(Interpreter):
    """The WindowsState Interpreter allows to construct the State
    of a Windows-based GUI application.

    A tolerance attribute is provided for tuning State comparison logic.

    Check the WindowsState documentation for further information.

    """
    tolerance = DEFAULT_TOLERANCE  # Type: Tolerance
    """Maximum tolerance for window image comparison and device load."""

    _screen_size = None            # Type: tuple
    """Screen resolution in pixels."""

    def __init__(self, feedback: Any, control: Any,
                 scraper: scrapers.WindowScraper):
        self.control = control
        self.scraper = scraper
        self.feedback = feedback
        self.logger = logging.getLogger("%s.%s" % (self.__module__,
                                                   self.__class__.__name__))

    def interpret_state(self) -> 'WinState':
        self._move_cursor_away()

        feedback = self._raw_feedback()
        image = Image.open(feedback.image).crop(feedback.scraped.coordinates)
        window = WindowsWindow(feedback.scraped, image)
        actions = tuple(ACTIONS[o.type](self.control, o, window)
                        for o in feedback.scraped.objects if o.type in ACTIONS)

        return WindowsState(
            self.control, window, actions, feedback, self.tolerance)

    def load_state(self, path: Path) -> 'WinState':
        feedback = self._raw_feedback(path)
        image = Image.open(feedback.image)
        window = WindowsWindow(feedback.scraped, image)
        actions = tuple(ACTIONS[o.type](self.control, o, window)
                        for o in feedback.scraped.objects if o.type in ACTIONS)

        return WindowsState(
            self.control, window, actions, feedback, self.tolerance)

    def _raw_feedback(self, path: Path = None) -> 'RawFeedback':
        """Retrieve raw information from the Feedback class
        or from a previously dumped state.

        Order of calls matters.

        """
        saved = None

        if path is not None:
            with path.open() as state_file:
                state = json.load(state_file)

            screenshot = state['window']
            saved = state['state']
            device_load = state['load']
            scraped = load_scraped_window(state['scraped'])
        else:
            load = self.feedback.load
            device_load = load.cpu, load.disk, load.network
            scraped = self.scraper.scrape_current_window()
            screenshot = self.feedback.screen.screenshot()

        return RawFeedback(device_load, screenshot, scraped, saved)

    def _move_cursor_away(self):
        """Move the mouse cursor away from the screen
        to avoid it interfering with the screenshot.

        """
        if self._screen_size is None:
            screeshot_path = self.feedback.screen.screenshot()
            self._screen_size = Image.open(screeshot_path).size

        self.control.mouse.move(self._screen_size[0] - 1,
                                self._screen_size[1] - 1)


class WindowsState(State):
    """Class representing the State of a Windows-based GUI application.

    Comparison against other states is done via comparing the window title,
    the list of available actions and computing the root mean squared distance
    between the images of the two windows.

    A tolerance attribute is provided for tuning the State comparison logic.
    If the Root Mean Squared Distance of the State images
    exceeds the image Tolerance, the two images are considered different.
    If the cpu, disk or network loads exceed the load Tolerance, the device
    is considered busy at the moment the State was analysed.

    """
    _saved_state = None  # Type: Any

    def __init__(self, control: Any, window: Window, actions: list,
                 feedback: 'RawFeedback', tolerance: Tolerance):
        self._control = control

        self.window = window
        self.actions = actions
        self.tolerance = tolerance
        self.raw_feedback = feedback
        self.logger = logging.getLogger("%s.%s" % (self.__module__,
                                                   self.__class__.__name__))

    def __str__(self) -> str:
        return self.window.title

    def __repr__(self) -> str:
        return repr(self.raw_feedback.scraped)

    def __eq__(self, state: State) -> bool:
        """Compare the current state with the given one.

        If the window titles, the actions or the window images differ,
        then the States are considered different.

        """
        if self.window.title != state.window.title:
            return False

        if Counter(self.actions) != Counter(state.actions):
            return False

        return compare_images(
            self.window.image, state.window.image,
            self.tolerance.image, (a.coordinates for a in self.actions))

    @property
    def busy(self) -> bool:
        """The device is considered busy when the cpu, disk or network loads
        exceed the load Tolerance.

        """
        self.logger.info(
            "Load: CPU %f - Disk %f - Network %f", *self.raw_feedback.load)

        for load, tolerance in zip(self.raw_feedback.load, self.tolerance.load):
            if load > tolerance:
                return True

        return False

    def save(self):
        if self._saved_state is None:
            self._saved_state = self._control.state.save()
            self.logger.info("State %s saved", self.window.title)
        else:
            raise RuntimeError("State already saved")

    def restore(self):
        if self._saved_state is not None:
            self._control.state.restore(self._saved_state)
            self.logger.info("State %s restored", self.window.title)
        else:
            raise RuntimeError("State was not saved")

    def dump(self, path: Path):
        image_path = path.joinpath('window.png')
        state_path = path.joinpath('state.json')

        path.mkdir(parents=True, exist_ok=True)
        self.window.image.save(image_path)

        state = {'window': str(image_path),
                 'state': self._saved_state,
                 'load': self.raw_feedback.load,
                 'scraped': self.raw_feedback.scraped._asdict()}

        with state_path.open('w') as state_file:
            json.dump(state, state_file)

        self.logger.info("State %s dumped at %s", self.window.title, state_path)


class WindowsWindow(Window):
    def __init__(self, scraped_window: scrapers.Window, image: Image):
        self._image = image

        self.title = scraped_window.text
        self.coordinates = scraped_window.coordinates
        self.text = os.linesep.join(o.text for o in scraped_window.objects
                                    if o.type == scrapers.ObjectType.STATIC)

    @property
    def image(self) -> Image:
        return self._image.copy()


class WindowsAction(Action):
    def __init__(self, control: Any, scraped: scrapers.Object, window: Window):
        self._window = window
        self._control = control

        self.text = scraped.text
        self.coordinates = scraped.coordinates

    def __eq__(self, action: Action) -> bool:
        return self.text == action.text

    def __hash__(self):
        return hash(self.__class__.__name__) + hash(self.text)

    @property
    def image(self) -> Image:
        return self._window.image.crop(self.coordinates)

    def _cursor_coordinates(self) -> tuple:
        """Select a random pair of coordinates within the action area.

        The mouse can use the coordinates for performing its actions.

        """
        coordinates = absolute_coordinates(
            self.coordinates, self._window.coordinates)

        return (randint(coordinates.left + 1, coordinates.right - 1),
                randint(coordinates.top + 1, coordinates.bottom - 1))

    def _move_cursor_away(self):
        """Move the mouse cursor away from the Window
        to avoid it interfering with the screenshot.

        """
        self._control.mouse.move(
            self._window.coordinates.right, self.coordinates.bottom)


class WindowsButton(Button, WindowsAction):
    toggled = False
    """Checkboxes and radio buttons will be toggled if ticked."""

    def __init__(self, control: Any, scraped: scrapers.Object, window: Window):
        super().__init__(control, scraped, window)
        self.toggled = scraped.properties.get('toggled', False)

    def __eq__(self, action: Action) -> bool:
        return super().__eq__(action) and self.toggled == action.toggled

    def __hash__(self):
        return super().__hash__() + int(self.toggled)

    def perform(self):
        """Single left-button click with the mouse."""
        self._control.mouse.move(*self._cursor_coordinates())
        self._control.mouse.click()
        self._move_cursor_away()


class WindowsTextBox(TextBox, WindowsAction):
    def perform(self, text: str):
        self._control.mouse.move(*self._cursor_coordinates())
        self._control.mouse.click()
        self._move_cursor_away()

        self._control.keyboard.type(text)


class WindowsLink(Link, WindowsAction):
    def perform(self):
        """Single left-button click with the mouse."""
        self._control.mouse.move(*self._cursor_coordinates())
        self._control.mouse.click()
        self._move_cursor_away()


class WindowsComboBox(ComboBox, WindowsAction):
    """Combo Boxes are also referred as drop-down lists.

    The drop-down elements are listed within the items attribute.

    """
    def __init__(self, control, scraped: scrapers.Object, window: Window):
        super().__init__(control, scraped, window)

        self.items = tuple(scraped.properties.get('items', ()))

    def perform(self, positions: int):
        """Select the drop-down item in the list of items.

        The position parameter chooses how many positions to move the selector.
        Positive numbers move the selector down, negative ones up.

        """
        if abs(positions) > len(self.items):
            raise ValueError("positions out of range")

        self._control.mouse.move(*self._cursor_coordinates())
        self._control.mouse.click()
        self._move_cursor_away()

        key = 'down' if positions > 0 else 'up'
        for _ in range(abs(positions)):
            self._control.keyboard.press(key)

        self._control.keyboard.press('return')


def load_scraped_window(state: dict) -> scrapers.Window:
    """Reconstruct a scraped window from a State dump."""
    objects = tuple(scrapers.Object(*o) for o in state['objects'])

    return scrapers.Window(state['text'], objects, state['coordinates'],
                           state['scraper'], state['raw'])


ACTIONS = {scrapers.ObjectType.BUTTON: WindowsButton,
           scrapers.ObjectType.TEXTBOX: WindowsTextBox,
           scrapers.ObjectType.LINK: WindowsLink,
           scrapers.ObjectType.COMBOBOX: WindowsComboBox}
RawFeedback = NamedTuple('RawFeedback', (('load', tuple),
                                         ('image', Path),
                                         ('scraped', scrapers.Window),
                                         ('saved_state', Any)))
