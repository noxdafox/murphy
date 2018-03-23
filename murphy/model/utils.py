from murphy.model import Coordinates, WindowNotFoundError


def window_coordinates(window: tuple, frame: tuple) -> Coordinates:
    """Return the valid Window coordinates trimming the borders
    based on the frame information.

    """
    border = ((window[2] - window[0]) - (frame[2] - frame[0])) // 2

    return valid_coordinates(window[0] + border, window[1] + border,
                             window[2] - border, window[3] - border)


def valid_coordinates(left: int, top: int, right: int, bot: int) -> Coordinates:
    """Validate captured coordinates and return them."""
    for coordinate in (left, top, right, bot):
        if coordinate < 0:
            raise WindowNotFoundError("Could not find any window: {}".format(
                Coordinates(left, top, right, bot)))

    if right - left <= 0 or bot - top <= 0:
        raise WindowNotFoundError("Could not find any window: {}".format(
            Coordinates(left, top, right, bot)))

    return Coordinates(left, top, right, bot)


def relative_coordinates(obj: tuple, reference: tuple) -> Coordinates:
    """Return the coordinates of the object relative to the reference."""
    return Coordinates(obj[0] - reference[0],
                       obj[1] - reference[1],
                       obj[2] - reference[0],
                       obj[3] - reference[1])


def absolute_coordinates(obj: tuple, reference: tuple) -> Coordinates:
    """Return the coordinates of the object relative to the screen."""
    return Coordinates(reference[0] + obj[0],
                       reference[1] + obj[1],
                       reference[0] + obj[2],
                       reference[1] + obj[3])
