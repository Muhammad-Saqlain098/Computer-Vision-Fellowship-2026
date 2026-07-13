"""
file_manager.py
----------------
Everything related to talking to the filesystem: opening an image via a
native file dialog, saving the processed image, and reading basic file
metadata (size, extension).
"""

import os
import cv2
from tkinter import filedialog


IMAGE_FILETYPES = [
    ("Image Files", "*.jpg *.jpeg *.png *.bmp *.tiff *.tif"),
    ("JPEG", "*.jpg *.jpeg"),
    ("PNG", "*.png"),
    ("Bitmap", "*.bmp"),
    ("All Files", "*.*"),
]


def open_image_dialog():
    """Show a native 'open file' dialog. Returns the path or '' if cancelled."""
    return filedialog.askopenfilename(
        title="Select an Image",
        filetypes=IMAGE_FILETYPES
    )


def save_image_dialog(image, initial_dir=None, default_name="processed_image.png"):
    """
    Show a native 'save file' dialog and write `image` (a NumPy/OpenCV
    array) to disk. Returns the saved path, or '' if the user cancelled.
    """
    path = filedialog.asksaveasfilename(
        title="Save Image As",
        defaultextension=".png",
        initialdir=initial_dir,
        initialfile=default_name,
        filetypes=[
            ("PNG", "*.png"),
            ("JPEG", "*.jpg"),
            ("Bitmap", "*.bmp"),
            ("All Files", "*.*"),
        ]
    )
    if not path:
        return ""

    cv2.imwrite(path, image)
    return path


def get_file_info(path: str) -> dict:
    """Return {'size_bytes': int, 'extension': str, 'name': str} for a file."""
    return {
        "size_bytes": os.path.getsize(path),
        "extension": os.path.splitext(path)[1].lower(),
        "name": os.path.basename(path),
    }
