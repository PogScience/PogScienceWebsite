import binascii
from itertools import zip_longest

import numpy as np
import scipy.cluster

from PIL import Image


def grouper(iterable, n, fillvalue=None):
    """
    Yields the given iterator by chunks of length n.

    :param iterable: The iterable.
    :param n: The chunks length.
    :param fillvalue: If the size of the iterable is not a multiple of n, this
                      value will be used to fill the last chunk.
    :return: Chunked iterator.
    """
    args = [iter(iterable)] * n
    return zip_longest(*args, fillvalue=fillvalue)


def extract_main_colours(image_path: str, colours_count: int = 3, discriminate_grays: bool = True):
    """
    Analyses an image, and extracts the main colours using the k-means
    algorithm.

    :param image_path: The path to the image to analyze.
    :param colours_count: The amount of colours to extract.
    :param discriminate_grays: If True, extracted white, gray, and blacks (or
                                close) colours will be placed at the end of the
                                colours, as such colours are not perceived as
                                important even if they are the most present
                                ones.
    :return: A list of the (r, g, b) tuples corresponding to the main colors,
             ordered.
    """
    # Loads the image into a numpy array
    im = Image.open(image_path)
    ar = np.asarray(im)

    # Transforms the loaded image into a list of pixels by reshaping the data to
    # only two dimensions.
    shape = ar.shape
    ar = ar.reshape(np.product(shape[:2]), shape[2]).astype(float)

    # For images with transparency, removes transparent pixels for more accurate
    # result.
    if shape[2] == 4:
        ar = ar[ar[:, 3] > 5.0]

    # Analyses the image pixels colors to separate them into `colours_count`
    # clusters, using the k-means algorithm.
    codes, _ = scipy.cluster.vq.kmeans(ar, colours_count)

    # Assigns each extracted color to the pixels in the original image, to be able
    # to order the colors per occurrences, so we can return sorted colors. Then
    # counts the number of pixels per cluster.
    pixel_to_cluster, _ = scipy.cluster.vq.vq(ar, codes)
    counts, _ = np.histogram(pixel_to_cluster, len(codes))

    # Creates a list with the ordered top colors.
    colours = []
    for index in reversed(np.argsort(counts)):
        colour = codes[index]
        colours.append(np.around(colour[:3], decimals=3))

    # Of the top colors, we push back the white ones, as even if it's technically a
    # top color, it is not as important as the other ones.
    if discriminate_grays:
        for index in range(len(colours)):
            colour = colours[index]
            # check if the coordinates are close enough to be sure it's some
            # kind of gray
            xv, yv = np.meshgrid(colour, colour)
            distances = np.absolute((xv - yv).flatten())
            max_distance = distances[np.argmax(distances)]
            if max_distance < 12:
                del colours[index]
                colours.append(colour)

    return list(map(tuple, colours))
