"""Scraper interface implementation based on the WinAPI agent."""

import requests

from murphy.model.utils import relative_coordinates, window_coordinates
from murphy.model.scrapers import WindowScraper, Window, Object, ObjectType


class WinAPIScraper(WindowScraper):
    def __init__(self, host: str, port: int):
        self.host = host
        self.port = port

    def scrape_current_window(self) -> Window:
        objects = []
        result, scraper = remote_scrape(self.host, self.port)

        coordinates = window_coordinates(
            result['coordinates'], result['frame_coordinates'])

        for child in result['children']:
            child_coordinates = fix_coordinates(
                child['coordinates'], coordinates)
            child_coordinates = relative_coordinates(
                coordinates, coordinates)

            if child['enabled'] and rectangle_area(coordinates) > 0:
                obj_type = object_type(child)

                if obj_type is not None:
                    objects.append(Object(child['text'],
                                          obj_type,
                                          child_coordinates,
                                          child_properties(child)))

        return Window(result['text'],
                      objects,
                      coordinates,
                      scraper,
                      result)


def fix_coordinates(child: tuple, window: tuple) -> tuple:
    """Some child seems to be placed outside the window."""
    left = child[0] if window[0] < child[0] else window[0]
    top = child[1] if window[1] < child[1] else window[1]
    right = child[2] if window[2] > child[2] else window[2]
    bottom = child[3] if window[3] > child[3] else window[3]

    return left, top, right, bottom


def rectangle_area(rectangle):
    return (((rectangle[2] - 1) - rectangle[0]) *
            ((rectangle[3] - 1) - rectangle[1]))


def child_properties(child: dict) -> dict:
    return {'items': child['items']} if 'items' in child else {}


def object_type(child: dict) -> (str, None):
    child_class = child['class'].lower()

    if 'button' in child_class:
        return ObjectType.BUTTON
    elif 'edit' in child_class:
        return ObjectType.TEXTBOX
    elif 'combobox' in child_class:
        return ObjectType.COMBOBOX
    elif 'syslink' in child_class:
        return ObjectType.LINK
    elif 'static' in child_class:
        return ObjectType.STATIC


def remote_scrape(host: str, port: int) -> tuple:
    """Call the remote scraper and retrieve its results."""
    url = 'http://%s:%d' % (host, port)
    response = requests.get(url)

    response.raise_for_status()
    result = response.json()

    if result['status'] == 'failure':
        raise RuntimeError(result['error'])

    return result['result'], result['type']
