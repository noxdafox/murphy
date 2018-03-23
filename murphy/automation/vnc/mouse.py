import time
import random

from murphy.automation import MurphyFactory, Mouse


class VNCMouse(Mouse):
    """VNCDoTool based implementation of a Mouse controller.

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

    def move(self, xcoord: int, ycoord: int):
        self._client.mouseMove(xcoord, ycoord)
        time.sleep(random.uniform(*MOUSE_DELAY))

    def click(self, button=1):
        self._client.mousePress(button)
        time.sleep(random.uniform(*MOUSE_DELAY))


MOUSE_DELAY = 0.04, 0.12
