import time
import random

from murphy.automation import MurphyFactory, Mouse


class VirtualboxMouse(Mouse):
    """Virtualbox based implementation of a Mouse controller.

    Random delay is injected between the actions to simulate a real user
    and to reduce out-of-order actions.

    """
    def __init__(self, factory: MurphyFactory):
        self._machine = factory()

    def move(self, xcoord: int, ycoord: int):
        with self._machine.create_session() as session:
            mouse = session.console.mouse

            if not mouse.absolute_supported:
                raise RuntimeError("Mouse absolute positioning not supported")

            mouse.put_mouse_event_absolute(xcoord, ycoord, 0, 0, 0)
            mouse.put_mouse_event(0, 0, 0, 0, 0)  # force re-draw of cursor
            time.sleep(random.uniform(*MOUSE_DELAY))

    def click(self, button=1):
        with self._machine.create_session() as session:
            mouse = session.console.mouse

            if not mouse.relative_supported:
                raise RuntimeError("Mouse relative positioning not supported")

            mouse.put_mouse_event(0, 0, 0, 0, button)
            time.sleep(random.uniform(*MOUSE_DELAY))
            mouse.put_mouse_event(0, 0, 0, 0, 0)
            time.sleep(random.uniform(*MOUSE_DELAY))


MOUSE_DELAY = 0.04, 0.12
MOUSE_RELEASE = 0.004, 0.012
