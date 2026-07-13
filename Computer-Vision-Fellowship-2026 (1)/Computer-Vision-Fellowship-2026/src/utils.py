"""
utils.py
--------
Small, reusable helper functions used across the Vision Toolkit project.

Responsibilities:
    * Convert OpenCV (NumPy / BGR) images into Tkinter-displayable PhotoImage
      objects while preserving aspect ratio.
    * Track the scale factor + offsets used to fit an image inside a fixed
      canvas so that mouse clicks on the canvas can be mapped back to real
      pixel coordinates on the *original* image (needed for drawing tools
      and cropping).
"""

import cv2
import numpy as np
from PIL import Image, ImageTk


def cv2_to_pil(image: np.ndarray) -> Image.Image:
    """Convert a BGR or grayscale OpenCV image to a PIL Image (RGB)."""
    if image is None:
        raise ValueError("cv2_to_pil received None instead of an image")

    if len(image.shape) == 2:  # grayscale / single channel
        rgb = cv2.cvtColor(image, cv2.COLOR_GRAY2RGB)
    else:
        rgb = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)

    return Image.fromarray(rgb)


def fit_image_to_canvas(image: np.ndarray, canvas_w: int, canvas_h: int):
    """
    Resize `image` (OpenCV array) so that it fits within canvas_w x canvas_h
    while preserving its aspect ratio.

    Returns:
        photo       - a Tkinter PhotoImage ready to draw on a canvas
        disp_w      - displayed width in pixels
        disp_h      - displayed height in pixels
        offset_x    - left edge of the image on the canvas (for centering)
        offset_y    - top edge of the image on the canvas (for centering)
        scale       - disp_w / original_w  (== disp_h / original_h)
    """
    orig_h, orig_w = image.shape[:2]

    scale = min(canvas_w / orig_w, canvas_h / orig_h, 1.0)
    disp_w = max(1, int(orig_w * scale))
    disp_h = max(1, int(orig_h * scale))

    pil_img = cv2_to_pil(image)
    pil_img = pil_img.resize((disp_w, disp_h), Image.LANCZOS)
    photo = ImageTk.PhotoImage(pil_img)

    offset_x = (canvas_w - disp_w) // 2
    offset_y = (canvas_h - disp_h) // 2

    return photo, disp_w, disp_h, offset_x, offset_y, scale


def canvas_to_image_coords(cx, cy, offset_x, offset_y, scale, orig_w, orig_h):
    """
    Convert a click/drag coordinate on the Tkinter canvas into a pixel
    coordinate on the original (full resolution) image. Clamps to bounds.
    """
    ix = (cx - offset_x) / scale
    iy = (cy - offset_y) / scale

    ix = int(max(0, min(orig_w - 1, ix)))
    iy = int(max(0, min(orig_h - 1, iy)))

    return ix, iy


def format_file_size(num_bytes: float) -> str:
    """Human readable file size, e.g. 512.00 KB or 2.34 MB."""
    size_kb = num_bytes / 1024
    if size_kb < 1024:
        return f"{size_kb:.2f} KB"
    return f"{size_kb / 1024:.2f} MB"
