# Vision Toolkit — Computer Vision Fellowship 2026

A desktop image-processing application built with **Python, OpenCV, Pillow,
and Tkinter**. Upload any image and interactively apply filters, adjustments,
drawing tools, and geometric transforms, then save the result.

![Python](https://img.shields.io/badge/python-3.9%2B-blue)
![OpenCV](https://img.shields.io/badge/OpenCV-4.x-green)
![License](https://img.shields.io/badge/license-MIT-lightgrey)

---

## Features

### Core (Assignment Requirements)
| Category | Features |
|---|---|
| **Upload** | Load `.jpg`, `.jpeg`, `.png`, `.bmp`, `.tiff` images via a native file dialog |
| **Image Info** | Live width, height, resolution, channel count, file size, and file type |
| **Filters** | Grayscale, Gaussian Blur, Median Blur, Binary Threshold, Adaptive Threshold, Canny Edge Detection |
| **Drawing Tools** | Rectangle, Circle, Line, Text — drawn interactively by clicking/dragging on the canvas |
| **Save** | Export the processed image to disk as PNG/JPG/BMP |

### Bonus
- Histogram (live matplotlib plot of pixel intensity per channel)
- Brightness & Contrast adjustment (live-preview sliders)
- Rotate (any angle, auto-expanding canvas so nothing is clipped)
- Resize (exact width/height)
- Crop (interactive drag-to-select on the canvas)
- Flip (horizontal / vertical)
- Live Webcam capture (start, freeze a frame, stop)
- Reset to original image at any time

All parameterized tools (blur kernel size, threshold values, brightness,
contrast, rotation angle, Canny thresholds) open a small dialog with a
**live-updating preview** before you commit the change.

---

## Project Structure

```
Computer-Vision-Fellowship-2026/
│
├── app.py                     # Entry point — run this
├── requirements.txt
├── README.md
├── .gitignore
│
├── src/
│   ├── gui.py                  # Main Tkinter window & all UI wiring
│   ├── image_processing.py     # Pure OpenCV functions (no Tkinter dependency)
│   ├── drawing.py              # Interactive canvas drawing tools + coordinate mapping
│   ├── file_manager.py         # Open/save dialogs, file metadata
│   └── utils.py                # Image<->Tkinter conversion, canvas fitting/scaling
│
├── assets/
│   ├── input/                  # Put sample images here for testing
│   └── output/                 # Saved/processed images land here
│
├── notebook/
│   └── OpenCV_Experiments.ipynb   # Same functions, explored interactively
│
├── reports/                    # Written project reports
├── screenshots/                # App screenshots for documentation
└── docs/                       # Additional documentation
```

**Design note:** `image_processing.py` has zero Tkinter/GUI dependencies —
every function takes a NumPy array in, returns a NumPy array out. This is
what makes the same functions reusable from both the GUI (`gui.py`) and the
Jupyter notebook, and makes them straightforward to unit test.

---

## Installation

```bash
git clone <your-repo-url>
cd Computer-Vision-Fellowship-2026
pip install -r requirements.txt
```

> **Note (Linux):** Tkinter isn't installed by pip. If `import tkinter` fails, run:
> `sudo apt-get install python3-tk`

## Running the App

```bash
python app.py
```

1. Click **Upload Image** and choose a photo.
2. Use the left-hand panel to apply filters, adjustments, or drawing tools.
3. Sliders open a live preview — click **Apply** to keep the change or
   **Cancel** to discard it.
4. Click **Save Image** to export the result, or **Reset Image** to start
   over from the original.

---

## How It Works

### Coordinate Mapping (Drawing & Crop)
The canvas is a fixed 850×600 area, but uploaded images can be any
resolution and are displayed scaled-to-fit and centered. `utils.py`
computes the scale factor and centering offset every time an image is
rendered; `drawing.py` uses that same mapping to convert a mouse click on
the canvas into the correct pixel coordinate on the *original* image before
drawing a shape or cropping — so shapes land exactly where you click
regardless of zoom level.

### Non-Destructive Original
`original_image` is loaded once and never mutated. `display_image` is the
working copy that every filter/edit applies to. **Reset Image** simply
copies `original_image` back into `display_image`.

### Live Preview Dialogs
Parameterized effects (blur kernel size, thresholds, brightness, contrast,
rotation, Canny) use a shared `_open_param_dialog()` helper in `gui.py` — a
modal window with one or more sliders. Every slider move recomputes the
effect from a clean snapshot and renders it to the canvas *without*
committing, so **Cancel** always returns you to the prior state.

### Webcam
`cv2.VideoCapture(0)` is polled every 30ms via `root.after()` so it never
blocks the Tkinter event loop. **Capture Frame** freezes the current frame
into `display_image`/`original_image` as if it had been uploaded from disk.

---

## Testing

Every function in `image_processing.py` and `utils.py` is pure and has been
exercised with synthetic NumPy arrays (see `reports/` for the test log),
and the full GUI flow (upload → filter → draw → crop → histogram) has been
smoke-tested end-to-end under a virtual display.

---

## Roadmap / Possible Extensions
- Undo/redo history stack
- Batch processing of a folder of images
- Additional filters (sharpen, sepia, emboss)
- Drag handles to resize/move shapes after drawing

---

## Author
Computer Vision Fellowship 2026 — Internship Project (Assignment 3)
