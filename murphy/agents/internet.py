"""MrMurphy Agent for exploring "The Internet®".

This module acts as an example of an Agent interacting with a browser
application in order to explore the Internet from a given starting URL.

The Agent loops over the current state until either all possible paths
have been explored or a timeout is reached.

To limit the exploration, a maximum depth parameter is set.
If the travelled path reaches the maximum depth, the Agent will start
from the beginning exploring another one.

"""

import time
import random
import logging

from murphy.journal import Node
from murphy.model import State, Action, Link


MAX_DEPTH = 6
FREQUENCY = 10
STATE_TIMEOUT = 30
"""How many seconds to wait if the browser window is out of focus."""


class MaxDepthReachedError(RuntimeError):
    """Raised when the max exploration depth has been reached."""
    pass


class InternetExplorer:
    """Not the Internet Explorer you are thinking about.

    The max_depth controls how many links the explorer will follow
    before resetting. A too high value of max_depth might cause the explorer
    to visit the entire Internet.

    The frequency parameter controls how frequently in seconds the browser
    content is scanned. If the frequency is too high, the web content
    might not be dowloaded/rendered completely affecting the results.

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
        """Explore "The Internet®" but just for a while.

        The explorer will stop when either timeout seconds have passed
        or no available links to explore are available.

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
                    logging.info("Performed %s", action.text)
                elif self.journal.current_node == self.journal.initial_node:
                    logging.info("All possible paths have been explored.")
                    return
            else:
                logging.info("Nowere to go!")

                self.switch_focus()
                self.reset_if_timeout(STATE_TIMEOUT)

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
            self.reset_if_timeout(STATE_TIMEOUT)

            raise error

    def journal_position(self, state: State) -> (Node, None):
        """Find state in the journal.

        If not found, ensure there are Links to explore and
        add the new state to the journal.

        """
        node = None

        logging.debug(state.raw_feedback.scraped)

        if state in self.journal:
            node = self.journal.find_node(state)
            logging.info("Old Node: %s", node.state.window.title)
        elif available_actions(state):
            node = self.journal.new_node(state)
            logging.info("New Node: %s", node.state.window.title)

        return node

    def reset_if_timeout(self, timeout):
        self.wait_time = self.wait_time if self.wait_time > 0 else time.time()
        waited_time = time.time() - self.wait_time

        if waited_time > timeout:
            logging.warning(
                "Timeout (%ds) when waiting for window focus.", waited_time)
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
                # this may happen if websites have dynamic content
                edge = self.journal.current_node.find_edge(action)
                if edge.tail != node:
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
    title = state.window.title.lower()

    if any(b in title for b in BROWSERS):
        return False

    logging.warning(
        "Window %s is not recognised as a valid browser.", state.window.title)

    return True


def available_actions(state: State) -> list:
    """Return a list of actions which can be performed.

    Each time an action is performed, its score is reduced by one unit.

    """
    actions = []

    for action in (a for a in state.actions if isinstance(a, Link)):
        if not hasattr(action, 'score'):
            action.score = DEFAULT_ACTION_SCORE

        if action.score > 0:
            actions.append(action)

    return actions


DEFAULT_ACTION_SCORE = 2
BROWSERS = 'chrome', 'chromium', 'firefox', 'internet explorer', 'safari'
