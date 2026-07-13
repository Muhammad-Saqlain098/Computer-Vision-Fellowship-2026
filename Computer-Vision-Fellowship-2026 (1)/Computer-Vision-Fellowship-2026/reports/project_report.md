# Project Report — Assignment 3: Vision Toolkit

## Objective
Build a desktop computer-vision application that lets a user upload an
image, inspect its properties, apply a range of OpenCV-based processing
operations, annotate it with drawing tools, and save the result — as a
professional, portfolio-quality Python project.

## Architecture Decisions

**Separation of concerns.** Image-processing logic (`image_processing.py`)
is completely independent of Tkinter. Every function accepts and returns a
plain NumPy array. This means:
- The same functions power both the GUI and the standalone Jupyter notebook.
- Each function can be tested headlessly without a display.
- New filters can be added without touching any GUI code.

**Coordinate mapping.** The hardest part of this project was making
drawing tools and cropping "just work" regardless of the image's real
resolution vs. how large it's rendered on the fixed-size canvas.
`utils.fit_image_to_canvas()` computes a single scale factor + centering
offset each time an image is displayed; `drawing.py` reuses that exact
mapping to translate a canvas click back into real image-pixel coordinates.
This is why a rectangle drawn near the edge of a 4000×3000 photo lands in
the right spot even though it's shown shrunk to fit an 850×600 canvas.

**Non-destructive editing model.** `original_image` is set once at upload
(or webcam capture) and never modified. `display_image` is the working
copy every tool operates on. This gives a reliable one-click "Reset Image"
and also means every filter naturally *chains* onto the previous one
(e.g. Grayscale → Gaussian Blur → Canny), which matches how real image
pipelines are built.

**Live-preview dialogs.** Rather than applying an effect immediately with a
hardcoded parameter, every parameterized tool (blur kernel size, threshold
values, brightness/contrast, rotation angle, Canny thresholds) opens a
small modal with a slider. Moving the slider re-renders the effect on the
canvas immediately from a clean base image; nothing is committed to the
real working image until "Apply" is clicked. This was implemented as one
reusable helper (`_open_param_dialog`) instead of duplicating dialog code
per feature.

## Challenges & Solutions

| Challenge | Solution |
|---|---|
| Tkinter can't display OpenCV's BGR NumPy arrays directly | Convert BGR→RGB, wrap in a PIL `Image`, then `ImageTk.PhotoImage` |
| Rotating an image by an arbitrary angle clips the corners | Compute the new bounding box size from the rotation matrix and expand the output canvas before warping |
| Mapping a canvas click to the right image pixel after scaling | Single shared scale/offset calculation reused by both rendering and click-handling code |
| Webcam feed must not freeze the UI | Poll the camera every 30ms using `root.after()` instead of a blocking loop |
| Avoiding duplicate dialog code for 6+ parameterized tools | One generic `_open_param_dialog()` helper takes a list of slider configs and a compute function |

## Outcome
A fully working, tested, and documented desktop application covering every
required and bonus feature in the assignment brief, organized as a clean,
extensible codebase suitable for a fellowship portfolio.
