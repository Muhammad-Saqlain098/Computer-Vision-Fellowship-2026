"""
image_processing.py
--------------------
Pure image-processing functions built on OpenCV. Every function takes a
NumPy array (the OpenCV image) plus optional parameters and returns a NEW
NumPy array. None of these functions mutate the input in place, and none of
them touch Tkinter -- that keeps this module easy to unit test and reuse
(e.g. from the Jupyter notebook).
"""

import cv2
import numpy as np


# ---------------------------------------------------------------------------
# Core filters
# ---------------------------------------------------------------------------

def to_grayscale(img: np.ndarray) -> np.ndarray:
    """Convert a BGR image to single-channel grayscale."""
    if len(img.shape) == 2:
        return img.copy()
    return cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)


def gaussian_blur(img: np.ndarray, ksize: int = 5) -> np.ndarray:
    """Apply Gaussian blur. ksize must be odd and >= 1."""
    ksize = ksize if ksize % 2 == 1 else ksize + 1
    ksize = max(1, ksize)
    return cv2.GaussianBlur(img, (ksize, ksize), 0)


def median_blur(img: np.ndarray, ksize: int = 5) -> np.ndarray:
    """Apply median blur (great for salt & pepper noise). ksize must be odd."""
    ksize = ksize if ksize % 2 == 1 else ksize + 1
    ksize = max(1, ksize)
    return cv2.medianBlur(img, ksize)


def binary_threshold(img: np.ndarray, thresh: int = 127) -> np.ndarray:
    """Simple global binary threshold. Returns a single-channel image."""
    gray = to_grayscale(img)
    _, out = cv2.threshold(gray, thresh, 255, cv2.THRESH_BINARY)
    return out


def adaptive_threshold(img: np.ndarray, block_size: int = 11, c: int = 2) -> np.ndarray:
    """Adaptive (locally-computed) threshold -- good for uneven lighting."""
    gray = to_grayscale(img)
    block_size = block_size if block_size % 2 == 1 else block_size + 1
    block_size = max(3, block_size)
    return cv2.adaptiveThreshold(
        gray, 255,
        cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
        cv2.THRESH_BINARY,
        block_size, c
    )


def canny_edges(img: np.ndarray, t1: int = 100, t2: int = 200) -> np.ndarray:
    """Canny edge detection."""
    gray = to_grayscale(img)
    return cv2.Canny(gray, t1, t2)


# ---------------------------------------------------------------------------
# Brightness / Contrast
# ---------------------------------------------------------------------------

def adjust_brightness(img: np.ndarray, value: int = 0) -> np.ndarray:
    """value in [-100, 100]. Positive brightens, negative darkens."""
    return cv2.convertScaleAbs(img, alpha=1.0, beta=value)


def adjust_contrast(img: np.ndarray, value: float = 1.0) -> np.ndarray:
    """value in [0.1, 3.0]. 1.0 = unchanged, >1 increases contrast."""
    return cv2.convertScaleAbs(img, alpha=value, beta=0)


# ---------------------------------------------------------------------------
# Geometric transforms
# ---------------------------------------------------------------------------

def rotate_image(img: np.ndarray, angle: float) -> np.ndarray:
    """Rotate an image about its center by `angle` degrees, expanding the
    output canvas so nothing gets clipped."""
    h, w = img.shape[:2]
    center = (w / 2, h / 2)

    matrix = cv2.getRotationMatrix2D(center, angle, 1.0)

    cos = abs(matrix[0, 0])
    sin = abs(matrix[0, 1])
    new_w = int((h * sin) + (w * cos))
    new_h = int((h * cos) + (w * sin))

    matrix[0, 2] += (new_w / 2) - center[0]
    matrix[1, 2] += (new_h / 2) - center[1]

    return cv2.warpAffine(img, matrix, (new_w, new_h))


def resize_image(img: np.ndarray, width: int, height: int) -> np.ndarray:
    width = max(1, int(width))
    height = max(1, int(height))
    return cv2.resize(img, (width, height), interpolation=cv2.INTER_AREA)


def crop_image(img: np.ndarray, x1: int, y1: int, x2: int, y2: int) -> np.ndarray:
    """Crop using two opposite corners; corners are auto-sorted."""
    x1, x2 = sorted((int(x1), int(x2)))
    y1, y2 = sorted((int(y1), int(y2)))
    x2 = max(x2, x1 + 1)
    y2 = max(y2, y1 + 1)
    return img[y1:y2, x1:x2].copy()


def flip_image(img: np.ndarray, mode: int) -> np.ndarray:
    """mode: 1 = horizontal, 0 = vertical, -1 = both."""
    return cv2.flip(img, mode)


# ---------------------------------------------------------------------------
# Histogram data (returned as raw numbers; the GUI renders it)
# ---------------------------------------------------------------------------

def compute_histogram(img: np.ndarray):
    """
    Returns a dict of {channel_name: 256-length numpy array of counts}.
    Grayscale images return {'Gray': [...]}.
    Color images return {'Blue': [...], 'Green': [...], 'Red': [...]}.
    """
    if len(img.shape) == 2:
        hist = cv2.calcHist([img], [0], None, [256], [0, 256]).flatten()
        return {"Gray": hist}

    colors = ("Blue", "Green", "Red")
    result = {}
    for i, name in enumerate(colors):
        hist = cv2.calcHist([img], [i], None, [256], [0, 256]).flatten()
        result[name] = hist
    return result
