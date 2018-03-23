"""Windows API based GUI Scraping Agent.

HTTP server acting as Scraping Agent within the guest OS.

Execution:

  server.py <host> <port>

Protocol:

  HTTP GET /

  Scrape the current window and collect the output.

The response is application/json MIME encoded in the format:

{"type": "scraper type",
 "status": "success|failure"
 "error": "error message"
 "result": "scraper output"}

"""

import json
import ctypes
import logging
import argparse

from http.server import BaseHTTPRequestHandler, HTTPServer


SMALL_BUFFER = 1024
LARGE_BUFFER = 128 * SMALL_BUFFER
WM_GETTEXT = 0x000d
WM_GETTEXTLENGTH = 0x000e
CB_GETCOUNT = 0x0146
CB_GETLBTEXT = 0x0148
SCRAPER_TYPE = 'windows_api'


class ScraperAgent(BaseHTTPRequestHandler):
    """Serves HTTP requests allowing to Scrape the current Window."""
    def do_GET(self):
        """Scrape the current Window."""
        scraper = WindowScraper()
        response = {'type': SCRAPER_TYPE}

        try:
            hwnd = ctypes.windll.user32.GetForegroundWindow()
            response['result'] = scraper.scrape(hwnd)
            response['status'] = 'success'
            logging.info("Window successfully scraped")
            logging.debug(response['result'])
        except Exception as error:
            logging.exception(error)
            response['error'] = "%r" % error
            response['status'] = 'failure'

        self.send_response(200)
        self.send_header('Content-type', 'application/json')
        self.end_headers()

        self.wfile.write(bytes(json.dumps(response), "utf8"))


class WindowScraper:
    """Wrapper class for collecting the content of a Window."""
    def __init__(self):
        self._children = []

    def scrape(self, hwnd: int) -> dict:
        """Scrape the given window returning its content."""
        window = window_info(hwnd)
        windows = self.children_windows(hwnd)

        window['children'] = windows

        return window

    def children_windows(self, hwnd: int) -> list:
        """Iterates over the children windows."""
        proc = EnumWindowsProc(self.window_callback)
        ctypes.windll.user32.EnumChildWindows(hwnd, proc, 0)

        return self._children

    def window_callback(self, hwnd: int, _):
        """Called by EnumChildWindows."""
        if ctypes.windll.user32.IsWindowVisible(hwnd):
            self._children.append(window_info(hwnd))


def window_info(hwnd: int) -> str:
    """Aggregates all the information contained within the given Window."""
    text = window_text(hwnd)
    text = text if text != '' else window_wm_text(hwnd)

    window = {'hwnd': hwnd,
              'text': text,
              'class': window_class(hwnd),
              'coordinates': window_coordinates(hwnd),
              'frame_coordinates': window_coordinates(hwnd),
              'enabled': ctypes.windll.user32.IsWindowEnabled(hwnd) != 0}

    if window['class'] == 'ComboBox':
        window['items'] = combobox_items(hwnd)

    return window


def window_coordinates(hwnd: int) -> tuple:
    """Coordinates as tuple of a Window.

    left, top, right, bottom

    """
    rectangle = RECT()
    result = ctypes.windll.user32.GetWindowRect(
        hwnd, ctypes.pointer(rectangle))

    if result == 0:
        raise RuntimeError("Failed GetWindowRect for %s" % hwnd)
    else:
        return rectangle.coordinates


def frame_coordinates(hwnd: int) -> tuple:
    """Coordinates as tuple of a Window frame.

    left, top, right, bottom

    """
    rectangle = RECT()
    result = ctypes.windll.user32.GetClientRect(
        hwnd, ctypes.pointer(rectangle))

    if result == 0:
        raise RuntimeError("Failed GetClientRect for %s" % hwnd)
    else:
        return rectangle.coordinates


def window_class(hwnd: int) -> str:
    text = ctypes.create_unicode_buffer(SMALL_BUFFER)
    result = ctypes.windll.user32.GetClassNameW(
        hwnd, ctypes.pointer(text), SMALL_BUFFER)

    if result == 0:
        raise RuntimeError("Failed GetClassNameW for %s" % hwnd)
    else:
        return ctypes.wstring_at(text)


def window_text(hwnd: int) -> str:
    """Collect the text of a window element."""
    text = ctypes.create_unicode_buffer(LARGE_BUFFER)
    length = ctypes.windll.user32.GetWindowTextW(hwnd, text, LARGE_BUFFER)
    wstring = ctypes.wstring_at(text, length)

    return wstring.replace('\00', ' ').strip() if length > 0 else ''


def window_wm_text(hwnd: int) -> str:
    """Collects the text contained within a Window."""
    message = WM_GETTEXT
    text = ctypes.create_unicode_buffer(LARGE_BUFFER)
    length = ctypes.windll.user32.SendMessageW(
        hwnd, message, LARGE_BUFFER, ctypes.pointer(text))
    wstring = ctypes.wstring_at(text, length)

    return wstring.replace('\00', ' ').strip() if length > 0 else ''


def combobox_items(hwnd: int) -> str:
    items = []
    message = CB_GETCOUNT
    count = ctypes.windll.user32.SendMessageW(hwnd, CB_GETCOUNT, 0, 0)

    for index in range(count):
        message = CB_GETLBTEXT
        text = ctypes.create_unicode_buffer(SMALL_BUFFER)
        length = ctypes.windll.user32.SendMessageW(
            hwnd, message, index, ctypes.pointer(text))

        if length != -1:
            items.append(ctypes.wstring_at(text))

    return items


def main():
    arguments = parse_arguments()

    logging.basicConfig(level=arguments.debug and 10 or 20)

    logging.info("Serving requests at %s %d.", arguments.host, arguments.port)

    try:
        run_server(arguments.host, arguments.port)
    except KeyboardInterrupt:
        logging.info("Termination request.")


def run_server(host: str, port: int):
    server = HTTPServer((host, port), ScraperAgent)
    server.serve_forever()


def parse_arguments() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description='Windows API GUI Scraper Agent.')
    parser.add_argument('host', type=str, help='Server address')
    parser.add_argument('port', type=int, help='Server port')
    parser.add_argument(
        '-d', '--debug', action='store_true', default=False, help='debug log')

    return parser.parse_args()


class RECT(ctypes.Structure):
    """WinAPI RECT structure."""
    _fields_ = [("left", ctypes.c_long),
                ("top", ctypes.c_long),
                ("right", ctypes.c_long),
                ("bottom", ctypes.c_long)]

    @property
    def coordinates(self):
        return self.left, self.top, self.right, self.bottom


EnumWindowsProc = ctypes.WINFUNCTYPE(ctypes.c_bool,
                                     ctypes.c_int,
                                     ctypes.POINTER(ctypes.c_int))


if __name__ == '__main__':
    main()
