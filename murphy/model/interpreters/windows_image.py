"""Windows OS images comparison module."""


import logging
from math import sqrt
from typing import Sequence

import numpy
from PIL import Image, ImageChops

from murphy.model.utils import absolute_coordinates


def compare_images(image1: Image, image2: Image,
                   tolerance: float, actions: Sequence) -> bool:
    """Compare the two given images. If their distance is below the tolerance,
    the images are deemed equal otherwise different.

    The actions sequence must contain the list of action coordinates.

    The areas of the image belonging to an action will be checked
    against 3d effects such as highlights.

    """
    differential_image = grayscale_image_difference(image1, image2)
    differential_image = remove_highlights(differential_image, actions)

    distance = root_mean_squared_distance(differential_image)

    LOGGER.debug("Images distance: %f", distance)

    return distance < tolerance


def grayscale_image_difference(image1: Image, image2: Image) -> Image:
    """Difference between the two given images in gray scale."""
    grayscale1 = image1.convert(GRAYSCALE)
    grayscale2 = image2.convert(GRAYSCALE)

    return ImageChops.difference(grayscale1, grayscale2)


def root_mean_squared_distance(image: Image) -> float:
    """Compute the Root Mean Squared Distance of the differential image."""
    histogram = image.histogram()
    square_sum = sum(v * ((i % 256) ** 2) for i, v in enumerate(histogram))

    return sqrt(square_sum / float(image.size[0] * image.size[1]))


def remove_highlights(image: Image, buttons: Sequence) -> Image:
    """Many GUIs highlight the selected/default action.
    The selection can be usually moved with the TAB key.

    This can cause false negatives in which two images belonging
    to the same state are deemed different because the selection highligth
    is on different buttons.

    This function detects if the differential image contains what looks like
    3d button effects and removes them.

    """
    data = numpy.array(image)

    for coord in buttons:
        button_image = image.crop(coord)
        if rectangle_highlighted(button_image, coord):
            data[coord.top:coord.bottom, coord.left:coord.right] = 0

    return Image.fromarray(data)


def rectangle_highlighted(image: Image, coordinates: tuple) -> bool:
    """If the bounding box of the image overlaps with the button coordinates,
    it's likely to be a button 3d effect.

    """
    image_coordinates = image.getbbox()

    if image_coordinates is not None:
        image_coordinates = absolute_coordinates(image_coordinates, coordinates)

        return similar_rectangles(image_coordinates, coordinates)

    return False


def similar_rectangles(coordinates1: tuple, coordinates2: tuple) -> bool:
    """Compare two sets of coordinates to check if they are similar."""
    for coord1, coord2 in zip(coordinates1, coordinates2):
        if abs(coord2 - coord1) > COORDINATES_TOLERANCE:
            return False

    return True


GRAYSCALE = 'L'
COORDINATES_TOLERANCE = 10
LOGGER = logging.getLogger("%s" % __name__)
