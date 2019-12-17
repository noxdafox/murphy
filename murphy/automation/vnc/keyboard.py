import time
import random
from contextlib import contextmanager

from murphy.automation import MurphyFactory, Keyboard


class VNCKeyboard(Keyboard):
    """VNCDoTool based implementation of a Keyboard controller.

    Random delay is injected between the actions to simulate a real user
    and to reduce out-of-order actions.

    """
    def __init__(self, factory: MurphyFactory):
        self._client = factory()

    @property
    def timeout(self) -> int:
        return self._client.timeout

    @timeout.setter
    def timeout(self, value: int):
        self._client.timeout = value

    def type(self, text: str):
        for char in text:
            if char.isupper():
                with self.hold('shift'):
                    self.press(char)
            else:
                self.press(char)

            time.sleep(random.uniform(*TYPING_DELAY))

    def press(self, key: str):
        self._client.keyPress(key.lower())

    @contextmanager
    def hold(self, keys: (str, list, tuple)):
        keys = [keys] if isinstance(keys, str) else keys

        for key in keys:
            self._client.keyDown(key.lower())
            time.sleep(random.uniform(*TYPING_DELAY))

        try:
            yield
        finally:
            for key in keys:
                self._client.keyUp(key.lower())


TYPING_DELAY = 0.04, 0.16
