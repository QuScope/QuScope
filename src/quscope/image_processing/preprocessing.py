"""Image preprocessing utilities for quantum image processing."""

import numpy as np
from PIL import Image


def preprocess_image(image_path, size=(8, 8)):
    """Preprocess an image for quantum encoding.

    Args:
        image_path (str): Path to the image file.
        size (tuple): Target size for the image (width, height).

    Returns:
        numpy.ndarray: Preprocessed image as a normalized numpy array.
    """
    # Load the image
    img = Image.open(image_path).convert("L")

    # Resize the image
    img_resized = img.resize(size)

    # Convert to numpy array and normalize
    img_array = np.array(img_resized) / 255.0

    return img_array


def binarize_image(img_array, threshold=0.5):
    """Convert a grayscale image to binary based on a threshold.

    Args:
        img_array (numpy.ndarray): Input grayscale image array.
        threshold (float): Threshold value for binarization (0-1).

    Returns:
        numpy.ndarray: Binary image array with values 0 and 1.
    """
    return (img_array > threshold).astype(int)
