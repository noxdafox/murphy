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
        self._client.keyPress(key)

    @contextmanager
    def hold(self, key: (str, list, tuple)):
        keys = [key] if isinstance(key, str) else key

        for char in keys:
            self._client.keyDown(char)
            time.sleep(random.uniform(*TYPING_DELAY))

        try:
            yield
        finally:
            for char in keys:
                self._client.keyUp(char)


TYPING_DELAY = 0.04, 0.16
