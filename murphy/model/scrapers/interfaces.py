"""Client-side interfaces for MrMurphy GUI scrapers."""


from enum import IntEnum
from typing import Any, NamedTuple

from murphy.model.interfaces import Coordinates


class ObjectType(IntEnum):
    BUTTON = 0
    TEXTBOX = 1
    COMBOBOX = 2
    LINK = 3
    STATIC = 4


Window = NamedTuple('Window',
                    (('text', str),                 # Window title
                     ('objects', list),             # List of contained objects
                     ('coordinates', Coordinates),  # Absolute co-ordinates
                     ('scraper', str),              # Adopted scraper
                     ('raw', Any)))                 # Scraper dump of the window

Object = NamedTuple('Object',
                    (('text', str),                 # Object text
                     ('type', ObjectType),          # Object type
                     ('coordinates', Coordinates),  # Relative co-ordinates
                     ('properties', dict)))         # Object extra properties


class WindowScraper:
    """Interface for collecting the content of a UI."""
    def scrape_current_window(self) -> Window:
        """Return the representation of the window under focus."""
        raise NotImplementedError()
