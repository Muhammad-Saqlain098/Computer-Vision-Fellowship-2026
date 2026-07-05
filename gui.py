"""
gui.py
------
Main application window for the Computer Vision Fellowship 2026 "Vision
Toolkit". Builds the layout (button panel, image canvas, information
panel, status bar) and wires every button to real functionality from
image_processing.py, drawing.py and file_manager.py.
"""

import os
import cv2
import tkinter as tk
from tkinter import ttk, messagebox, simpledialog

import image_processing as ip
import file_manager as fm
from drawing import DrawingManager
from utils import fit_image_to_canvas, format_file_size

import matplotlib
matplotlib.use("TkAgg")
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg


CANVAS_W, CANVAS_H = 850, 600

BUTTON_SECTIONS = [
    ("File", ["Upload Image", "Save Image", "Reset Image"]),
    ("Filters", ["Grayscale", "Gaussian Blur", "Median Blur",
                 "Binary Threshold", "Adaptive Threshold", "Canny Edge Detection"]),
    ("Adjust", ["Brightness", "Contrast", "Rotate", "Resize",
                "Flip Horizontal", "Flip Vertical", "Histogram"]),
    ("Drawing", ["Rectangle", "Circle", "Line", "Text", "Crop"]),
    ("Camera", ["Start Webcam", "Capture Frame", "Stop Webcam"]),
]


class VisionToolkitApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Vision Toolkit — Computer Vision Fellowship 2026")
        self.root.geometry("1300x760")
        self.root.configure(bg="#ECECEC")
        self.root.minsize(1100, 650)

        # ---- image state -------------------------------------------------
        self.original_image = None      # never modified after load
        self.display_image = None       # current working image (edits apply here)
        self.image_path = ""
        self._mapping = (0, 0, 1.0, 1, 1)  # offset_x, offset_y, scale, orig_w, orig_h

        # ---- webcam state --------------------------------------------------
        self.cap = None
        self.webcam_running = False
        self.webcam_after_id = None
        self._webcam_frame = None

        self.info_labels = {}

        self._build_layout()

        self.drawing = DrawingManager(
            canvas=self.canvas,
            get_mapping=lambda: self._mapping,
            get_image=lambda: self.display_image,
            set_image=self._commit_image,
            set_status=self.set_status,
        )

        self.set_status("Ready. Upload an image to begin.")

    # =====================================================================
    # LAYOUT
    # =====================================================================
    def _build_layout(self):
        # Left button panel (scrollable)
        self.left_outer = tk.Frame(self.root, bg="#1E1E2F", width=250)
        self.left_outer.pack(side="left", fill="y")
        self.left_outer.pack_propagate(False)

        self.left_canvas = tk.Canvas(self.left_outer, bg="#1E1E2F", highlightthickness=0)
        scrollbar = tk.Scrollbar(self.left_outer, orient="vertical", command=self.left_canvas.yview)
        self.left = tk.Frame(self.left_canvas, bg="#1E1E2F")

        self.left.bind("<Configure>", lambda e: self.left_canvas.configure(
            scrollregion=self.left_canvas.bbox("all")))
        left_window = self.left_canvas.create_window((0, 0), window=self.left, anchor="nw")
        self.left_canvas.configure(yscrollcommand=scrollbar.set)

        # Make the inner frame track the canvas width so buttons don't get clipped
        self.left_canvas.bind(
            "<Configure>",
            lambda e: self.left_canvas.itemconfig(left_window, width=e.width)
        )

        self.left_canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        self._create_left_panel()
        self._enable_mousewheel_scrolling()

        # Center: canvas + status bar
        center = tk.Frame(self.root, bg="#ECECEC")
        center.pack(side="left", fill="both", expand=True)

        self.canvas = tk.Canvas(center, width=CANVAS_W, height=CANVAS_H, bg="#333333",
                                 highlightthickness=0)
        self.canvas.pack(padx=10, pady=10)

        self.status = tk.Label(center, text="Status: Ready", anchor="w", bg="#1976D2",
                                fg="white", font=("Arial", 10, "bold"), padx=10, pady=6)
        self.status.pack(side="bottom", fill="x")

        # Right: information panel
        self.right = tk.Frame(self.root, bg="#F5F5F5", width=230)
        self.right.pack(side="right", fill="y")
        self.right.pack_propagate(False)

        self._create_information_panel()

    def _enable_mousewheel_scrolling(self):
        """
        Bind mouse-wheel scrolling to the left button panel. Windows/Mac send
        <MouseWheel> with a `delta`; Linux sends <Button-4>/<Button-5>
        instead. Bindings are only active while the pointer is over the left
        panel, so they don't interfere with anything else.
        """
        def _on_wheel(event):
            if getattr(event, "num", None) == 4:      # Linux scroll up
                self.left_canvas.yview_scroll(-1, "units")
            elif getattr(event, "num", None) == 5:     # Linux scroll down
                self.left_canvas.yview_scroll(1, "units")
            elif getattr(event, "delta", 0):           # Windows / macOS
                self.left_canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")

        def _bind(_event=None):
            self.left_canvas.bind_all("<MouseWheel>", _on_wheel)
            self.left_canvas.bind_all("<Button-4>", _on_wheel)
            self.left_canvas.bind_all("<Button-5>", _on_wheel)

        def _unbind(_event=None):
            self.left_canvas.unbind_all("<MouseWheel>")
            self.left_canvas.unbind_all("<Button-4>")
            self.left_canvas.unbind_all("<Button-5>")

        self.left_outer.bind("<Enter>", _bind)
        self.left_outer.bind("<Leave>", _unbind)

    def _create_left_panel(self):
        title = tk.Label(self.left, text="VISION TOOLKIT", bg="#1E1E2F", fg="white",
                          font=("Arial", 13, "bold"), pady=15)
        title.pack(fill="x")

        for section_name, items in BUTTON_SECTIONS:
            header = tk.Label(self.left, text=section_name.upper(), bg="#1E1E2F",
                               fg="#8E8EA8", font=("Arial", 9, "bold"), anchor="w")
            header.pack(fill="x", padx=14, pady=(14, 4))

            for item in items:
                btn = tk.Button(
                    self.left,
                    text=item,
                    width=24,
                    height=2,
                    bg="#1976D2",
                    fg="white",
                    activebackground="#1259A3",
                    activeforeground="white",
                    relief="flat",
                    font=("Arial", 10, "bold"),
                    command=lambda name=item: self.button_click(name)
                )
                btn.pack(padx=12, pady=3)

    def _create_information_panel(self):
        title = tk.Label(self.right, text="IMAGE INFORMATION", bg="#F5F5F5",
                          font=("Arial", 12, "bold"), pady=15)
        title.pack(fill="x")

        labels = ["Width", "Height", "Resolution", "Channels", "File Size", "Image Type"]

        for name in labels:
            row = tk.Frame(self.right, bg="#F5F5F5")
            row.pack(fill="x", padx=14, pady=6)

            tk.Label(row, text=name + ":", bg="#F5F5F5", font=("Arial", 10, "bold"),
                     anchor="w", width=10).pack(side="left")

            value = tk.Label(row, text="—", bg="#F5F5F5", font=("Arial", 10), anchor="w")
            value.pack(side="left", fill="x", expand=True)

            self.info_labels[name] = value

    # =====================================================================
    # DISPATCH
    # =====================================================================
    def button_click(self, name):
        handlers = {
            "Upload Image": self.upload_image,
            "Save Image": self.save_image,
            "Reset Image": self.reset_image,
            "Grayscale": self.apply_grayscale,
            "Gaussian Blur": self.apply_gaussian_blur,
            "Median Blur": self.apply_median_blur,
            "Binary Threshold": self.apply_binary_threshold,
            "Adaptive Threshold": self.apply_adaptive_threshold,
            "Canny Edge Detection": self.apply_canny,
            "Brightness": self.apply_brightness,
            "Contrast": self.apply_contrast,
            "Rotate": self.apply_rotate,
            "Resize": self.apply_resize,
            "Flip Horizontal": lambda: self._flip(1),
            "Flip Vertical": lambda: self._flip(0),
            "Histogram": self.show_histogram,
            "Rectangle": lambda: self.drawing.activate("rectangle"),
            "Circle": lambda: self.drawing.activate("circle"),
            "Line": lambda: self.drawing.activate("line"),
            "Text": lambda: self.drawing.activate("text"),
            "Crop": lambda: self.drawing.activate("crop"),
            "Start Webcam": self.start_webcam,
            "Capture Frame": self.capture_webcam_frame,
            "Stop Webcam": self.stop_webcam,
        }

        if not self._requires_image_ok(name):
            return

        handler = handlers.get(name)
        if handler:
            handler()
        else:
            self.set_status(name + " feature coming soon")

    def _requires_image_ok(self, name):
        """Block operations that need a loaded image when none exists."""
        exempt = ("Upload Image", "Start Webcam", "Stop Webcam", "Capture Frame")
        if name in exempt:
            return True
        if self.display_image is None:
            messagebox.showwarning("No Image", "Please upload an image first.")
            return False
        return True

    # =====================================================================
    # FILE OPERATIONS
    # =====================================================================
    def upload_image(self):
        path = fm.open_image_dialog()
        if not path:
            return

        image = cv2.imread(path)
        if image is None:
            messagebox.showerror("Error", "Could not read that image file.")
            return

        self.image_path = path
        self.original_image = image
        self.display_image = image.copy()

        self.show_image()
        self.update_information_panel()
        self.set_status("Image loaded successfully: " + os.path.basename(path))

    def save_image(self):
        if self.display_image is None:
            return
        initial_dir = os.path.dirname(self.image_path) if self.image_path else None
        path = fm.save_image_dialog(self.display_image, initial_dir=initial_dir)
        if path:
            self.set_status("Image saved to: " + path)

    def reset_image(self):
        if self.original_image is None:
            return
        self.display_image = self.original_image.copy()
        self.show_image()
        self.update_information_panel()
        self.set_status("Image reset to original")

    # =====================================================================
    # DISPLAY / INFO HELPERS
    # =====================================================================
    def show_image(self):
        self._render(self.display_image)

    def _render(self, img):
        if img is None:
            self.canvas.delete("all")
            return

        photo, disp_w, disp_h, off_x, off_y, scale = fit_image_to_canvas(img, CANVAS_W, CANVAS_H)
        self.canvas.delete("all")
        self.canvas.create_image(off_x + disp_w // 2, off_y + disp_h // 2, image=photo)
        self.canvas.image = photo  # keep a reference so it isn't garbage collected

        h, w = img.shape[:2]
        self._mapping = (off_x, off_y, scale, w, h)

    def _commit_image(self, new_img):
        """Used by the DrawingManager (and internally) to replace the
        working image after an edit, then refresh canvas + info panel."""
        self.display_image = new_img
        self.show_image()
        self.update_information_panel()

    def update_information_panel(self):
        if self.display_image is None:
            return

        shape = self.display_image.shape
        h, w = shape[0], shape[1]
        c = shape[2] if len(shape) == 3 else 1

        self.info_labels["Width"].config(text=str(w))
        self.info_labels["Height"].config(text=str(h))
        self.info_labels["Resolution"].config(text=f"{w} x {h}")
        self.info_labels["Channels"].config(text=str(c))

        if self.image_path and os.path.exists(self.image_path):
            size_bytes = os.path.getsize(self.image_path)
            self.info_labels["File Size"].config(text=format_file_size(size_bytes))
            ext = os.path.splitext(self.image_path)[1]
            self.info_labels["Image Type"].config(text=ext)

    def set_status(self, text):
        self.status.config(text="Status: " + text)

    # =====================================================================
    # FILTERS (no parameters)
    # =====================================================================
    def apply_grayscale(self):
        self._commit_image(ip.to_grayscale(self.display_image))
        self.set_status("Grayscale applied")

    def _flip(self, mode):
        self._commit_image(ip.flip_image(self.display_image, mode))
        self.set_status("Image flipped")

    # =====================================================================
    # FILTERS (parameterized) — use a shared live-preview dialog
    # =====================================================================
    def _open_param_dialog(self, title, sliders, compute_fn, base_img=None):
        """
        Generic modal dialog with one or more sliders that live-preview an
        effect on the canvas. `sliders` is a list of dicts:
            {"label": str, "from_": num, "to_": num, "default": num, "resolution": num}
        `compute_fn(base_img, *values)` must return the processed image.
        Nothing is committed to self.display_image until "Apply" is pressed.
        """
        if base_img is None:
            base_img = self.display_image.copy()

        dialog = tk.Toplevel(self.root)
        dialog.title(title)
        dialog.transient(self.root)
        dialog.grab_set()
        dialog.configure(bg="#F5F5F5")

        scales = []

        def do_preview(*_):
            values = [s.get() for s in scales]
            try:
                preview = compute_fn(base_img, *values)
                self._render(preview)
            except Exception as e:
                self.set_status(f"Preview error: {e}")

        for cfg in sliders:
            tk.Label(dialog, text=cfg["label"], bg="#F5F5F5", font=("Arial", 10, "bold")).pack(
                padx=16, pady=(14, 0), anchor="w")
            scale = tk.Scale(dialog, from_=cfg["from_"], to=cfg["to_"],
                              resolution=cfg.get("resolution", 1), orient="horizontal",
                              length=280, command=do_preview, bg="#F5F5F5")
            scale.set(cfg["default"])
            scale.pack(padx=16, pady=4)
            scales.append(scale)

        btn_row = tk.Frame(dialog, bg="#F5F5F5")
        btn_row.pack(pady=16)

        def on_apply():
            values = [s.get() for s in scales]
            result = compute_fn(base_img, *values)
            dialog.destroy()
            self._commit_image(result)
            self.set_status(f"{title} applied")

        def on_cancel():
            dialog.destroy()
            self.show_image()  # restore committed image (undo live preview)

        tk.Button(btn_row, text="Apply", width=12, bg="#2E7D32", fg="white",
                  command=on_apply).pack(side="left", padx=6)
        tk.Button(btn_row, text="Cancel", width=12, bg="#B71C1C", fg="white",
                  command=on_cancel).pack(side="left", padx=6)

        dialog.protocol("WM_DELETE_WINDOW", on_cancel)
        do_preview()

    def apply_gaussian_blur(self):
        self._open_param_dialog(
            "Gaussian Blur",
            [{"label": "Kernel Size (odd)", "from_": 1, "to_": 31, "default": 5, "resolution": 2}],
            lambda img, k: ip.gaussian_blur(img, int(k)),
        )

    def apply_median_blur(self):
        self._open_param_dialog(
            "Median Blur",
            [{"label": "Kernel Size (odd)", "from_": 1, "to_": 31, "default": 5, "resolution": 2}],
            lambda img, k: ip.median_blur(img, int(k)),
        )

    def apply_binary_threshold(self):
        self._open_param_dialog(
            "Binary Threshold",
            [{"label": "Threshold", "from_": 0, "to_": 255, "default": 127, "resolution": 1}],
            lambda img, t: ip.binary_threshold(img, int(t)),
        )

    def apply_adaptive_threshold(self):
        self._open_param_dialog(
            "Adaptive Threshold",
            [{"label": "Block Size (odd)", "from_": 3, "to_": 51, "default": 11, "resolution": 2},
             {"label": "C (subtracted constant)", "from_": -10, "to_": 10, "default": 2, "resolution": 1}],
            lambda img, block, c: ip.adaptive_threshold(img, int(block), int(c)),
        )

    def apply_canny(self):
        self._open_param_dialog(
            "Canny Edge Detection",
            [{"label": "Lower Threshold", "from_": 0, "to_": 500, "default": 100, "resolution": 5},
             {"label": "Upper Threshold", "from_": 0, "to_": 500, "default": 200, "resolution": 5}],
            lambda img, t1, t2: ip.canny_edges(img, int(t1), int(t2)),
        )

    def apply_brightness(self):
        self._open_param_dialog(
            "Brightness",
            [{"label": "Brightness (-100 to 100)", "from_": -100, "to_": 100, "default": 0, "resolution": 1}],
            lambda img, v: ip.adjust_brightness(img, int(v)),
        )

    def apply_contrast(self):
        self._open_param_dialog(
            "Contrast",
            [{"label": "Contrast (0.1 to 3.0)", "from_": 0.1, "to_": 3.0, "default": 1.0, "resolution": 0.1}],
            lambda img, v: ip.adjust_contrast(img, float(v)),
        )

    def apply_rotate(self):
        self._open_param_dialog(
            "Rotate",
            [{"label": "Angle (degrees)", "from_": -180, "to_": 180, "default": 0, "resolution": 1}],
            lambda img, a: ip.rotate_image(img, float(a)),
        )

    def apply_resize(self):
        if self.display_image is None:
            return
        h, w = self.display_image.shape[:2]

        dialog = tk.Toplevel(self.root)
        dialog.title("Resize")
        dialog.transient(self.root)
        dialog.grab_set()
        dialog.configure(bg="#F5F5F5")

        tk.Label(dialog, text="Width:", bg="#F5F5F5", font=("Arial", 10, "bold")).grid(
            row=0, column=0, padx=12, pady=12, sticky="e")
        width_var = tk.StringVar(value=str(w))
        tk.Entry(dialog, textvariable=width_var, width=10).grid(row=0, column=1, padx=12)

        tk.Label(dialog, text="Height:", bg="#F5F5F5", font=("Arial", 10, "bold")).grid(
            row=1, column=0, padx=12, pady=12, sticky="e")
        height_var = tk.StringVar(value=str(h))
        tk.Entry(dialog, textvariable=height_var, width=10).grid(row=1, column=1, padx=12)

        def on_apply():
            try:
                new_w = int(width_var.get())
                new_h = int(height_var.get())
                if new_w <= 0 or new_h <= 0:
                    raise ValueError
            except ValueError:
                messagebox.showerror("Invalid Input", "Width and height must be positive integers.")
                return
            result = ip.resize_image(self.display_image, new_w, new_h)
            dialog.destroy()
            self._commit_image(result)
            self.set_status(f"Resized to {new_w} x {new_h}")

        btn_row = tk.Frame(dialog, bg="#F5F5F5")
        btn_row.grid(row=2, column=0, columnspan=2, pady=14)
        tk.Button(btn_row, text="Apply", width=12, bg="#2E7D32", fg="white",
                  command=on_apply).pack(side="left", padx=6)
        tk.Button(btn_row, text="Cancel", width=12, bg="#B71C1C", fg="white",
                  command=dialog.destroy).pack(side="left", padx=6)

    # =====================================================================
    # HISTOGRAM
    # =====================================================================
    def show_histogram(self):
        if self.display_image is None:
            return

        hist_data = ip.compute_histogram(self.display_image)

        win = tk.Toplevel(self.root)
        win.title("Histogram")
        win.configure(bg="white")

        fig, ax = plt.subplots(figsize=(6, 4), dpi=100)
        colors = {"Blue": "b", "Green": "g", "Red": "r", "Gray": "black"}

        for channel_name, values in hist_data.items():
            ax.plot(values, color=colors.get(channel_name, "black"), label=channel_name)

        ax.set_title("Pixel Intensity Histogram")
        ax.set_xlabel("Pixel Value (0-255)")
        ax.set_ylabel("Frequency")
        ax.legend()
        fig.tight_layout()

        canvas = FigureCanvasTkAgg(fig, master=win)
        canvas.draw()
        canvas.get_tk_widget().pack(fill="both", expand=True)

        self.set_status("Histogram displayed")

    # =====================================================================
    # WEBCAM
    # =====================================================================
    def start_webcam(self):
        if self.webcam_running:
            return

        self.cap = cv2.VideoCapture(0)
        if not self.cap.isOpened():
            messagebox.showerror("Webcam Error", "Could not access the webcam.")
            self.cap = None
            return

        self.webcam_running = True
        self.set_status("Webcam started — click 'Capture Frame' to freeze an image")
        self._webcam_loop()

    def _webcam_loop(self):
        if not self.webcam_running or self.cap is None:
            return

        ret, frame = self.cap.read()
        if ret:
            self._webcam_frame = frame
            self._render(frame)

        self.webcam_after_id = self.root.after(30, self._webcam_loop)

    def capture_webcam_frame(self):
        if not self.webcam_running or self._webcam_frame is None:
            messagebox.showwarning("Webcam", "Start the webcam first.")
            return

        captured = self._webcam_frame.copy()
        self.stop_webcam()

        self.original_image = captured
        self.display_image = captured.copy()
        self.image_path = ""  # captured frame has no file on disk

        self.show_image()
        self._update_info_for_captured_frame()
        self.set_status("Webcam frame captured")

    def _update_info_for_captured_frame(self):
        h, w, c = self.display_image.shape
        self.info_labels["Width"].config(text=str(w))
        self.info_labels["Height"].config(text=str(h))
        self.info_labels["Resolution"].config(text=f"{w} x {h}")
        self.info_labels["Channels"].config(text=str(c))
        self.info_labels["File Size"].config(text="—")
        self.info_labels["Image Type"].config(text="webcam capture")

    def stop_webcam(self):
        self.webcam_running = False
        if self.webcam_after_id is not None:
            self.root.after_cancel(self.webcam_after_id)
            self.webcam_after_id = None
        if self.cap is not None:
            self.cap.release()
            self.cap = None
        if self.display_image is not None:
            self.show_image()
        self.set_status("Webcam stopped")

    # =====================================================================
    def on_close(self):
        self.stop_webcam()
        self.root.destroy()
