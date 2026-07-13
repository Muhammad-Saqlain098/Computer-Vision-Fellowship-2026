"""
drawing.py
----------
Interactive drawing tools bound to the Tkinter canvas.

The GUI owns the canvas and the "working" image (a NumPy array). This
module implements mouse-driven Rectangle / Circle / Line / Text tools plus
an interactive Crop tool, all operating through a small set of callbacks so
this file has zero direct dependency on the rest of the GUI class:

    get_mapping()   -> (offset_x, offset_y, scale, orig_w, orig_h)
                        describes how the *original* image maps onto the
                        canvas right now (see utils.fit_image_to_canvas).
    get_image()     -> returns the current working NumPy image
    set_image(img)  -> commits a new working image and redraws the canvas
    set_status(text)-> optional, updates the status bar

Only one tool is "armed" at a time via `activate(tool_name)`.
"""

import cv2
from tkinter import simpledialog

VALID_TOOLS = ("rectangle", "circle", "line", "text", "crop")


class DrawingManager:
    def __init__(self, canvas, get_mapping, get_image, set_image, set_status=None,
                 color=(0, 255, 0), thickness=2):
        self.canvas = canvas
        self.get_mapping = get_mapping
        self.get_image = get_image
        self.set_image = set_image
        self.set_status = set_status or (lambda text: None)

        self.color = color          # BGR, used directly by OpenCV
        self.thickness = thickness

        self.tool = None
        self.start_xy = None        # canvas-space start point
        self.preview_id = None      # id of the temporary shape on canvas

        self.canvas.bind("<ButtonPress-1>", self._on_press)
        self.canvas.bind("<B1-Motion>", self._on_drag)
        self.canvas.bind("<ButtonRelease-1>", self._on_release)

    # ------------------------------------------------------------------
    def activate(self, tool_name):
        """Arm a tool. Pass None to disable drawing mode entirely."""
        if tool_name is not None and tool_name not in VALID_TOOLS:
            raise ValueError(f"Unknown tool: {tool_name}")
        self.tool = tool_name
        self.start_xy = None
        self._clear_preview()
        if tool_name:
            self.set_status(f"{tool_name.capitalize()} tool active — click and drag on the image")

    def is_active(self):
        return self.tool is not None

    # ------------------------------------------------------------------
    def _clear_preview(self):
        if self.preview_id is not None:
            try:
                self.canvas.delete(self.preview_id)
            except Exception:
                pass
            self.preview_id = None

    def _hex_color(self):
        b, g, r = self.color
        return f"#{r:02x}{g:02x}{b:02x}"

    # ------------------------------------------------------------------
    def _on_press(self, event):
        if not self.tool:
            return
        self.start_xy = (event.x, event.y)

        if self.tool == "text":
            self._handle_text(event)
            self.start_xy = None

    def _on_drag(self, event):
        if not self.tool or self.start_xy is None or self.tool == "text":
            return

        self._clear_preview()
        x0, y0 = self.start_xy
        x1, y1 = event.x, event.y
        col = self._hex_color()

        if self.tool in ("rectangle", "crop"):
            self.preview_id = self.canvas.create_rectangle(x0, y0, x1, y1, outline=col, width=2)
        elif self.tool == "circle":
            self.preview_id = self.canvas.create_oval(x0, y0, x1, y1, outline=col, width=2)
        elif self.tool == "line":
            self.preview_id = self.canvas.create_line(x0, y0, x1, y1, fill=col, width=2)

    def _on_release(self, event):
        if not self.tool or self.start_xy is None or self.tool == "text":
            return

        self._clear_preview()
        x0, y0 = self.start_xy
        x1, y1 = event.x, event.y
        self.start_xy = None

        offset_x, offset_y, scale, orig_w, orig_h = self.get_mapping()
        p0 = self._to_image_coords(x0, y0, offset_x, offset_y, scale, orig_w, orig_h)
        p1 = self._to_image_coords(x1, y1, offset_x, offset_y, scale, orig_w, orig_h)

        # Ignore accidental zero-size clicks
        if abs(p1[0] - p0[0]) < 2 and abs(p1[1] - p0[1]) < 2:
            return

        img = self.get_image()
        if img is None:
            return

        if self.tool == "rectangle":
            out = img.copy()
            cv2.rectangle(out, p0, p1, self.color, self.thickness)
            self.set_image(out)
            self.set_status("Rectangle added")

        elif self.tool == "circle":
            center = ((p0[0] + p1[0]) // 2, (p0[1] + p1[1]) // 2)
            radius = int(max(abs(p1[0] - p0[0]), abs(p1[1] - p0[1])) / 2)
            out = img.copy()
            cv2.circle(out, center, max(radius, 1), self.color, self.thickness)
            self.set_image(out)
            self.set_status("Circle added")

        elif self.tool == "line":
            out = img.copy()
            cv2.line(out, p0, p1, self.color, self.thickness)
            self.set_image(out)
            self.set_status("Line added")

        elif self.tool == "crop":
            from image_processing import crop_image
            out = crop_image(img, p0[0], p0[1], p1[0], p1[1])
            self.set_image(out)
            self.set_status("Image cropped")
            self.tool = None  # crop is a one-shot action

    # ------------------------------------------------------------------
    def _handle_text(self, event):
        offset_x, offset_y, scale, orig_w, orig_h = self.get_mapping()
        img = self.get_image()
        if img is None:
            return

        text = simpledialog.askstring("Add Text", "Enter the text to draw on the image:")
        if not text:
            return

        px, py = self._to_image_coords(event.x, event.y, offset_x, offset_y, scale, orig_w, orig_h)
        out = img.copy()
        cv2.putText(out, text, (px, py), cv2.FONT_HERSHEY_SIMPLEX, 1.0, self.color, 2, cv2.LINE_AA)
        self.set_image(out)
        self.set_status(f"Text '{text}' added")

    # ------------------------------------------------------------------
    @staticmethod
    def _to_image_coords(cx, cy, offset_x, offset_y, scale, orig_w, orig_h):
        ix = int(max(0, min(orig_w - 1, (cx - offset_x) / scale)))
        iy = int(max(0, min(orig_h - 1, (cy - offset_y) / scale)))
        return ix, iy
