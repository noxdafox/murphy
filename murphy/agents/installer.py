"""MrMurphy Agent for Installing simple applications.

This module acts as an example of an Agent capable of installing
any kind of application which do not require complex input from the user.

Any installation which can be driven by simply clicking over buttons
will be explored aiming to optimize the path towards a successful installation.

The Agent loops over the current state until either all possible paths
have been explored or a timeout is reached.

To limit the exploration, a maximum depth parameter is set.
If the travelled path reaches the maximum depth, the Agent will start
from the beginning exploring another one.

The following heuristics are applied when choosing a possible path:

  * Avoid actions heading backward (Back, Cancel etc.). English only.
  * Prefer actions which buttons are in the lower-right corner of the GUI.
  * Prefer actions which have not been performed yet.

The logic tries also to tackle issues and corner cases such as windows
going out of focus or long lasting installations.

"""

import time
import random
import logging

from murphy.journal import Node
from murphy.model import State, Action, Button, Coordinates


MAX_DEPTH = 8
FREQUENCY = 6
FOCUS_TIMEOUT = 30
BUSY_TIMEOUT = 300
"""How many seconds to wait device is busy or
the installer window is out of focus.

"""


class MaxDepthReachedError(RuntimeError):
    """Raised when the max exploration depth has been reached."""
    pass


class ApplicationInstaller:
    """Installer Agent.

    Drives generic application installers.

    The max_depth controls how many buttons the installer will click
    before resetting. A too high value of max_depth might cause the installer
    to start using the application itself.

    The frequency parameter controls how frequently in seconds the window
    content is scanned. If the frequency is too high, the window content
    might not be rendered completely affecting the results.

    """
    action = None
    resetted = False
    wait_time = 0
    start_time = 0
    max_depth = MAX_DEPTH
    frequency = FREQUENCY

    def __init__(self, interpreter, journal,
                 max_depth: int = MAX_DEPTH, frequency: int = FREQUENCY):
        self.journal = journal
        self.interpreter = interpreter
        self.max_depth = max_depth
        self.frequency = frequency

    def explore(self, timeout: int):
        """Explore the application installer.

        The explorer will stop when either timeout seconds have passed
        or no buttons to explore are available.

        """
        action = None

        while self.continue_exploring(timeout, self.frequency):
            action = None if self.resetted else action

            try:
                state = self.current_state()
            except RuntimeError:
                continue

            node = self.journal_position(state)
            if node is not None:
                self.wait_time = 0

                try:
                    self.update_journal(node, action, self.max_depth)
                except MaxDepthReachedError:
                    action = None
                    continue

                if available_actions(self.journal.current_node.state):
                    action = self.choose_new_action()
                    action.perform()
                    logging.info(
                        "Performed %s, score %d", action.text, action.score)
                elif self.journal.current_node == self.journal.initial_node:
                    logging.info("All possible paths have been explored.")
                    return
                else:
                    logging.info("No available actions for this node.")
                    self.reset()
            elif state.busy:
                logging.info("State Busy.")

                if out_of_focus(state):
                    self.switch_focus()
                    self.reset_if_timeout(FOCUS_TIMEOUT)
                else:
                    self.reset_if_timeout(BUSY_TIMEOUT)
            else:
                logging.info("Nowere to go!")

                self.switch_focus()
                self.reset_if_timeout(FOCUS_TIMEOUT)

    def current_state(self):
        """Interpret the current state."""
        if self.resetted:
            self.resetted = False
            return self.journal.initial_node.state

        try:
            return self.interpreter.interpret_state()
        except RuntimeError as error:
            logging.warning("Unable to scrape window: %s", error)
            self.switch_focus()
            self.reset_if_timeout(FOCUS_TIMEOUT)

            raise error

    def journal_position(self, state: State) -> (Node, None):
        """Find state in the journal.

        If not found, ensure there are Links to explore and
        add the new state to the journal.

        """
        node = None

        logging.debug("%r", state)

        if state in self.journal:
            node = self.journal.find_node(state)
            logging.info("Old Node: %s", node)
        elif not out_of_focus(state) and available_actions(state):
            node = self.journal.new_node(state)
            logging.info("New Node: %s", node)

        return node

    def reset_if_timeout(self, timeout):
        self.wait_time = self.wait_time if self.wait_time > 0 else time.time()
        waited_time = time.time() - self.wait_time

        if waited_time > timeout:
            logging.warning(
                "Timeout (%ds) when waiting for %s.", waited_time,
                'window focus' if timeout == FOCUS_TIMEOUT else 'device idle')
            self.reset()

    def reset(self):
        """Reset the explorer to the initial state."""
        self.wait_time = 0
        self.resetted = True
        self.journal.initial_node.state.restore()

        logging.info("Reset to initial state.")

    def update_journal(self, node: Node, action: Action, max_depth: int):
        """Update the current position within the Journal and render it.

        Check if the max depth has been reached and raise
        MaxDepthReachedError if so.

        """
        if len(self.journal.nodes) == 1:
            # First node in journal, save state so it can be reverted to
            try:
                self.journal.initial_node.state.save()
            except RuntimeError:  # state already saved
                pass
        elif action is not None:
            if action not in self.journal.current_node:
                # Draw a new edge between the old and the new node
                self.journal.current_node.new_edge(action, node)
            else:
                # An already performed action led to a new node,
                # this may happen if windows have dynamic content
                # or highlighing effects are placed on different objects
                edge = self.journal.current_node.find_edge(action)
                if edge.tail != node:
                    logging.debug(
                        "Expecting Edge %s to lead to Node %s, got %s instead.",
                        edge, edge.tail, node)

                    self.journal.current_node.new_edge(action, node)

        self.journal.current_node = node
        self.journal.render(format='html_embedded')

        if self.journal.initial_node.distance(node) >= max_depth:
            logging.info("Max depth %d reached", max_depth)

            self.reset()

            raise MaxDepthReachedError("Max depth %d reached" % max_depth)

    def choose_new_action(self) -> Action:
        """Return the new action to be performed.

        Actions are chosen based on their score (highest score first).

        The chosen action will have its score reduced by one unit.

        """
        actions = available_actions(self.journal.current_node.state)
        candidate = max(actions, key=lambda a: a.score)
        candidates = [a for a in actions if a.score == candidate.score]
        action = random.choice(candidates)

        action.score -= 1

        return action

    def continue_exploring(self, timeout: int, frequency: int) -> bool:
        if self.start_time == 0:
            self.start_time = time.time()

        if time.time() - self.start_time < timeout:
            time.sleep(frequency)
            return True

        logging.info("Exploration timeout (%ds) reached.", timeout)

        return False

    def switch_focus(self):
        """Issue an ALT+ESC command to switch focus to the next window."""
        with self.interpreter.control.keyboard.hold('alt'):
            self.interpreter.control.keyboard.press('esc')

        logging.info("Issued ALT+ESC.")


def out_of_focus(state: State) -> bool:
    """Check if the State Window is out of focus."""
    # Windows OS specific
    if state.window.title == 'Program Manager' and not state.actions:
        return True
    elif state.window.title == '':
        actions = (a.text.lower() for a in state.actions)
        if set(('start', 'show desktop')) <= set(actions):
            return True

    return False


def available_actions(state: State) -> list:
    """Return a list of actions which can be performed.

    To improve the action selection logic, a score system is implemented.
    Each action receives a score based on its label
    and position within the Window.

    Each time an action is performed, its score is decreased by one unit.
    Actions reaching a score lesser or equal than zero won't be performed.

    """
    actions = []

    for action in (a for a in state.actions if isinstance(a, Button)):
        if not hasattr(action, 'score'):
            if is_blacklisted(action):
                action.score = BLACKLISTED_ACTION_SCORE
            elif is_graylisted(action):
                action.score = GRAYLISTED_ACTION_SCORE
            else:
                action.score = DEFAULT_ACTION_SCORE

            action.score += position_score(
                action.coordinates, state.window.coordinates)

        if action.score > 0:
            actions.append(action)

    return actions


def position_score(action: Coordinates, window: Coordinates):
    """The position-based scoring is based on the observation that most
    of the interesting buttons are placed in the lower half of the Window.

    """
    center = ((window.right - window.left) / 2,
              (window.top - window.bottom) / 2)

    if action.left > center[0] and action.top > center[1]:
        return BOTTOM_RIGHT
    if action.bottom > center[1]:
        return BOTTOM
    if action.bottom < center[1]:
        return TOP


def is_blacklisted(action: Action) -> bool:
    action_label = action.text.lower()
    if any(l in action_label for l in BLACKLISTED_LABELS):
        return True

    return False


def is_graylisted(action: Action) -> bool:
    action_label = action.text.lower()
    if any(l in action_label for l in GRAYLISTED_LABELS):
        return True

    return False


# position based scores
TOP = -1
BOTTOM = 1
BOTTOM_RIGHT = 2
# initial score
DEFAULT_ACTION_SCORE = 2
GRAYLISTED_ACTION_SCORE = 0
BLACKLISTED_ACTION_SCORE = -10
# action labels
GRAYLISTED_LABELS = 'do not accept', 'new folder'
BLACKLISTED_LABELS = (
    'back', 'cancel', 'previous', 'close',  # Don't move backward
    'minimize', 'maximize',                 # Don't change window size
    'down', 'up', 'left', 'right',          # Don't scroll
    'print', 'home'                         # Avoid useless paths
)
