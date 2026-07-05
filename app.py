"""
app.py
------
Entry point for the Vision Toolkit application.

Run with:
    python app.py
"""

import os
import sys
import tkinter as tk

# Make the src/ folder importable as flat modules (gui, image_processing, ...)
SRC_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "src")
sys.path.insert(0, SRC_DIR)

from gui import VisionToolkitApp  # noqa: E402


def main():
    root = tk.Tk()
    app = VisionToolkitApp(root)
    root.protocol("WM_DELETE_WINDOW", app.on_close)
    root.mainloop()


if __name__ == "__main__":
    main()
