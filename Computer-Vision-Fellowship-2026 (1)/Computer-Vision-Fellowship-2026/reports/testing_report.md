# Testing Report — Vision Toolkit

## Scope
This report covers functional verification of `image_processing.py`,
`utils.py`, `drawing.py`, and the integrated `gui.py` application, performed
during development.

## Method
Because the application is a desktop GUI, testing was done at two levels:

1. **Unit-level (headless):** Every pure function in `image_processing.py`
   and `utils.py` was called directly with synthetic NumPy image arrays
   (random noise arrays and a real JPEG) and outputs were checked for
   correct shape, dtype, and value ranges.
2. **Integration-level (virtual display):** The full `VisionToolkitApp`
   class was instantiated under Xvfb (a virtual X server), an image was
   loaded programmatically (bypassing the file dialog), and the following
   flow was exercised end-to-end:
   Upload → Grayscale → Reset → Flip → Rectangle (drawing) → Crop →
   Histogram data.

## Results

| Test | Result |
|---|---|
| `to_grayscale` returns single-channel array | ✅ Pass |
| `gaussian_blur` / `median_blur` preserve shape, accept even kernel sizes (auto-corrected to odd) | ✅ Pass |
| `binary_threshold` / `adaptive_threshold` return single-channel binary-like output | ✅ Pass |
| `canny_edges` returns single-channel edge map | ✅ Pass |
| `adjust_brightness` / `adjust_contrast` preserve shape and clip to valid pixel range | ✅ Pass |
| `rotate_image` expands canvas so corners are never clipped | ✅ Pass |
| `resize_image` produces exact requested dimensions | ✅ Pass |
| `crop_image` handles corners given in any order (auto-sorts) | ✅ Pass |
| `flip_image` (horizontal/vertical) preserves shape | ✅ Pass |
| `compute_histogram` returns 256-bin arrays per channel (3 for color, 1 for gray) | ✅ Pass |
| `fit_image_to_canvas` scales down large images, never upscales beyond 100% | ✅ Pass |
| `canvas_to_image_coords` correctly maps canvas clicks back to source pixel coordinates, including edge clamping | ✅ Pass |
| Full app: image load populates all six info labels correctly | ✅ Pass |
| Full app: Grayscale commit updates working image + info panel (channels: 3 → 1) | ✅ Pass |
| Full app: Reset Image restores the original array exactly | ✅ Pass |
| Full app: Rectangle tool maps a click-drag to the correct image region and draws in place | ✅ Pass |
| Full app: Crop tool produces a correctly-sized sub-image based on the drag region | ✅ Pass |
| `app.py` and all `src/*.py` files byte-compile without syntax errors | ✅ Pass |
| Jupyter notebook executes top-to-bottom without errors (`jupyter execute`) | ✅ Pass |

## Known Limitations
- Automated tests could not simulate real mouse drag events pixel-by-pixel
  through the Tk event loop (Tk requires a real/virtual display and event
  queue); instead, the underlying handler methods (`_on_press`,
  `_on_release`) were called directly with synthetic event objects, which
  exercises the same code path as a real drag.
- Webcam functionality requires a physical/virtual camera device and was
  verified by code review and manual desktop testing rather than automated
  test, since CI/sandbox environments typically have no camera device.

## Conclusion
All core and bonus features described in the assignment brief are
implemented, wired into the GUI, and verified functionally correct through
the tests above.
