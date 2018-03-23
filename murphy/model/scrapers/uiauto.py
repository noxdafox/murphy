"""Scraper interface implementation based on the Windows UI Automation agent."""

from enum import IntEnum

import requests

from murphy.model import WindowNotFoundError
from murphy.model.utils import window_coordinates
from murphy.model.utils import relative_coordinates, valid_coordinates
from murphy.model.scrapers import WindowScraper, Window, Object, ObjectType


class WinUIAutomationScraper(WindowScraper):
    full_scrape = False
    """A full scrape recursively scans the GUI.
    It yields more information but takes longer.
    """

    scraper_timeout = 30
    """Maximum amount of seconds to wait for a GUI scrape."""

    def __init__(self, host: str, port: int, full_scrape: bool = False):
        self.host = host
        self.port = port
        self.full_scrape = full_scrape

    def scrape_current_window(self) -> Window:
        objects = []
        result, scraper = remote_scrape(
            self.host, self.port,
            recursive=self.full_scrape, timeout=self.scraper_timeout)

        coordinates = window_coordinates(
            result['coordinates'], result['frame_coordinates'])

        for child in result.get('children', ()):
            objects = children(child, coordinates, objects)

        return Window(result['text'],
                      objects,
                      coordinates,
                      scraper,
                      result)


def children(child: dict, window: tuple, objects: list) -> list:
    if child['type'] != UIAControlType.UIA_ComboBoxControlTypeId:
        for element in child.get('children', ()):
            children(element, window, objects)

    try:
        coordinates = fix_coordinates(child['coordinates'], window)
        coordinates = relative_coordinates(coordinates, window)

        if valid_child(child, coordinates):
            objects.append(Object(child['text'],
                                  TYPE_MAP[child['type']],
                                  coordinates,
                                  child_properties(child)))
    except WindowNotFoundError:
        pass

    return objects


def valid_child(child: dict, coordinates: tuple) -> bool:
    return (child['type'] in TYPE_MAP and
            rectangle_area(coordinates) > 0 and
            child.get('clickable', False))


def child_properties(child: dict) -> dict:
    return {'toggled': child['toggled']} if 'toggled' in child else {}


def fix_coordinates(child: tuple, window: tuple) -> tuple:
    """Some child seems to be placed outside the window."""
    left = child[0] if window[0] < child[0] else window[0]
    top = child[1] if window[1] < child[1] else window[1]
    right = child[2] if window[2] > child[2] else window[2]
    bottom = child[3] if window[3] > child[3] else window[3]

    return valid_coordinates(left, top, right, bottom)


def rectangle_area(rectangle):
    return (((rectangle[2] - 1) - rectangle[0]) *
            ((rectangle[3] - 1) - rectangle[1]))


def remote_scrape(host: str, port: int,
                  recursive: bool = False, timeout: int = 10) -> tuple:
    """Call the remote scraper and retrieve its results."""
    url = 'http://%s:%d' % (host, port)
    parameters = {'recursive': int(recursive), 'timeout': timeout}
    response = requests.get(url, params=parameters)

    response.raise_for_status()
    result = response.json()

    if result['status'] == 'failure':
        raise RuntimeError(result['error'])

    return result['result'], result['type']


class UIAControlType(IntEnum):
    """
    msdn.microsoft.com/en-us/library/windows/desktop/ee671198(v=vs.85).aspx
    """
    UIA_ButtonControlTypeId = 50000
    """Identifies the Button control type."""
    UIA_CalendarControlTypeId = 50001
    """Identifies the Calendar control type."""
    UIA_CheckBoxControlTypeId = 50002
    """Identifies the CheckBox control type."""
    UIA_ComboBoxControlTypeId = 50003
    """Identifies the ComboBox control type."""
    UIA_EditControlTypeId = 50004
    """Identifies the Edit control type."""
    UIA_CustomControlTypeId = 50025
    """Identifies the Custom control type."""
    UIA_DataGridControlTypeId = 50028
    """Identifies the DataGrid control type."""
    UIA_DataItemControlTypeId = 50029
    """Identifies the DataItem control type."""
    UIA_DocumentControlTypeId = 50030
    """Identifies the Document control type."""
    UIA_GroupControlTypeId = 50026
    """Identifies the Group control type."""
    UIA_HeaderControlTypeId = 50034
    """Identifies the Header control type."""
    UIA_HeaderItemControlTypeId = 50035
    """Identifies the HeaderItem control type."""
    UIA_HyperlinkControlTypeId = 50005
    """Identifies the Hyperlink control type."""
    UIA_ImageControlTypeId = 50006
    """Identifies the Image control type."""
    UIA_ListControlTypeId = 50008
    """Identifies the List control type."""
    UIA_ListItemControlTypeId = 50007
    """Identifies the ListItem control type."""
    UIA_MenuBarControlTypeId = 50010
    """Identifies the MenuBar control type."""
    UIA_MenuControlTypeId = 50009
    """Identifies the Menu control type."""
    UIA_MenuItemControlTypeId = 50011
    """Identifies the MenuItem control type."""
    UIA_PaneControlTypeId = 50033
    """Identifies the Pane control type."""
    UIA_ProgressBarControlTypeId = 50012
    """Identifies the ProgressBar control type."""
    UIA_RadioButtonControlTypeId = 50013
    """Identifies the RadioButton control type."""
    UIA_ScrollBarControlTypeId = 50014
    """Identifies the ScrollBar control type."""
    UIA_SemanticZoomControlTypeId = 50039
    """Identifies the SemanticZoom control type. Windows > 8."""
    UIA_SeparatorControlTypeId = 50038
    """Identifies the Separator control type."""
    UIA_SliderControlTypeId = 50015
    """Identifies the Slider control type."""
    UIA_SpinnerControlTypeId = 50016
    """Identifies the Spinner control type."""
    UIA_SplitButtonControlTypeId = 50031
    """Identifies the SplitButton control type."""
    UIA_StatusBarControlTypeId = 50017
    """Identifies the StatusBar control type."""
    UIA_TabControlTypeId = 50018
    """Identifies the Tab control type."""
    UIA_TabItemControlTypeId = 50019
    """Identifies the TabItem control type."""
    UIA_TableControlTypeId = 50036
    """Identifies the Table control type."""
    UIA_TextControlTypeId = 50020
    """Identifies the Text control type."""
    UIA_ThumbControlTypeId = 50027
    """Identifies the Thumb control type."""
    UIA_TitleBarControlTypeId = 50037
    """Identifies the TitleBar control type."""
    UIA_ToolBarControlTypeId = 50021
    """Identifies the ToolBar control type."""
    UIA_ToolTipControlTypeId = 50022
    """Identifies the ToolTip control type."""
    UIA_TreeControlTypeId = 50023
    """Identifies the Tree control type."""
    UIA_TreeItemControlTypeId = 50024
    """Identifies the TreeItem control type."""
    UIA_WindowControlTypeId = 50032
    """Identifies the Window control type."""
    UIA_AppBarControlTypeId = 50040
    """Identifies the AppBar control type. Windows > 8.1."""


TYPE_MAP = {UIAControlType.UIA_ButtonControlTypeId: ObjectType.BUTTON,
            UIAControlType.UIA_RadioButtonControlTypeId: ObjectType.BUTTON,
            UIAControlType.UIA_CheckBoxControlTypeId: ObjectType.BUTTON,
            UIAControlType.UIA_EditControlTypeId: ObjectType.TEXTBOX,
            UIAControlType.UIA_ComboBoxControlTypeId: ObjectType.COMBOBOX,
            UIAControlType.UIA_HyperlinkControlTypeId: ObjectType.LINK,
            UIAControlType.UIA_TextControlTypeId: ObjectType.STATIC}
