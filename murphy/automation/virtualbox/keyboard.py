import time
import random
from contextlib import contextmanager

from murphy.automation import MurphyFactory, Keyboard


class VirtualboxKeyboard(Keyboard):
    """VNCDoTool based implementation of a Keyboard controller.

    Random delay is injected between the actions to simulate a real user
    and to reduce out-of-order actions.

    """
    def __init__(self, factory: MurphyFactory):
        self._machine = factory()

    def type(self, text: str):
        for char in text:
            self.press(char)

            time.sleep(random.uniform(*TYPING_DELAY))

    def press(self, key: str):
        with self._machine.create_session() as session:
            keyboard = session.console.keyboard
            press, release = keyboard.SCANCODES[key.upper()]

            keyboard.put_scancodes(press + release)

    @contextmanager
    def hold(self, keys: (str, list, tuple)):
        with self._machine.create_session() as session:
            keys = [keys] if isinstance(keys, str) else keys
            keyboard = session.console.keyboard
            press = [keyboard.SCANCODES[k.upper()][0] for k in keys]
            release = [keyboard.SCANCODES[k.upper()][1] for k in keys]

            for key_press in press:
                keyboard.put_scancodes(key_press)
                time.sleep(random.uniform(*TYPING_DELAY))

            try:
                yield
            finally:
                for key_release in release:
                    keyboard.put_scancodes(key_release)


TYPING_DELAY = 0.04, 0.16
