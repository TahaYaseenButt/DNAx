import os
import sys
import tkinter as tk
from tkinter import messagebox
from utils import resource_path

try:
    import fitz  # PyMuPDF
except Exception:
    fitz = None
try:
    from PIL import Image, ImageTk
except Exception:
    Image = None
    ImageTk = None


class ProtocolPage(tk.Frame):
    def __init__(self, parent):
        super().__init__(parent, bg="#f8fafb")
        self.pack(fill="both", expand=True)

        header = tk.Frame(self, bg="white")
        header.pack(fill="x")
        tk.Label(header, text="Protocols", font=("Segoe UI", 16, "bold"), bg="white").pack(side="left", padx=20, pady=10)

        # Internal navbar (top) with four protocol buttons
        nav = tk.Frame(self, bg="#f0f2f5")
        nav.pack(fill="x", padx=10, pady=(10, 0))

        btn_gel = tk.Button(nav, text="Gel Electrophoresis Protocol", command=lambda: self.show_protocol('gel'))
        btn_tae = tk.Button(nav, text="TAE Buffer", command=lambda: self.show_protocol('tae'))
        btn_pcr = tk.Button(nav, text="PCR PROTOCOL", command=lambda: self.show_protocol('pcr'))
        btn_ctab = tk.Button(nav, text="CTAB Buffer Protocol", command=lambda: self.show_protocol('ctab'))

        for b in (btn_gel, btn_tae, btn_pcr, btn_ctab):
            b.pack(side="left", padx=6, pady=6)

        # Content area
        self.content = tk.Frame(self, bg="#ffffff", bd=1, relief="solid")
        self.content.pack(fill="both", expand=True, padx=10, pady=10)

        # Top info and controls bar
        top_bar = tk.Frame(self.content, bg="#ffffff")
        top_bar.pack(fill="x", pady=(8, 0))

        self.lbl_info = tk.Label(top_bar, text="Select a protocol to view", bg="#ffffff", font=("Segoe UI", 12))
        self.lbl_info.pack(side="left", padx=8, pady=6)

        # External-open button (only shown when embedded viewer not available)
        self.btn_open = tk.Button(top_bar, text="Open PDF", command=self._open_current_pdf, state="disabled")
        if not (fitz and Image and ImageTk):
            self.btn_open.pack(side="right", padx=8)

        self.current_pdf = None

        # default protocol mapping
        self.protocol_files = {
            'gel': 'Gel Electrophoresis Protocol.pdf',
            'tae': 'TAE Buffer.pdf',
            'pcr': 'PCR PROTOCOL.pdf',
            'ctab': 'CTAB Buffer Protocol.pdf'
        }

        # expected folder for PDFs (project assets/protocols at repo root)
        self.protocols_dir = resource_path(os.path.join('assets', 'protocols'))
        try:
            os.makedirs(self.protocols_dir, exist_ok=True)
        except Exception:
            pass

        # PDF viewer state
        self.doc = None
        self.page_count = 0
        self.current_page = 0
        self.zoom = 1.0

        # Viewer widgets: controls (top-right) and scrollable canvas
        ctrl_frame = tk.Frame(top_bar, bg="#ffffff")
        ctrl_frame.pack(side="right")

        # Only show page label and zoom controls (no prev/next)
        self.lbl_page = tk.Label(ctrl_frame, text="Page: 0/0", bg="#ffffff")
        self.btn_zoom_out = tk.Button(ctrl_frame, text="Zoom -", command=lambda: self._change_zoom(1/1.2), state="disabled")
        self.btn_zoom_in = tk.Button(ctrl_frame, text="Zoom +", command=lambda: self._change_zoom(1.2), state="disabled")

        for w in (self.lbl_page, self.btn_zoom_out, self.btn_zoom_in):
            w.pack(side="left", padx=4)

        # Canvas for scrollable PDF image
        canvas_frame = tk.Frame(self.content, bg="#ffffff")
        canvas_frame.pack(fill="both", expand=True, pady=6)

        self.canvas = tk.Canvas(canvas_frame, bg="#ffffff", highlightthickness=0)
        self.vbar = tk.Scrollbar(canvas_frame, orient="vertical", command=self.canvas.yview)
        self.hbar = tk.Scrollbar(canvas_frame, orient="horizontal", command=self.canvas.xview)
        self.canvas.configure(yscrollcommand=self.vbar.set, xscrollcommand=self.hbar.set)

        self.vbar.pack(side="right", fill="y")
        self.hbar.pack(side="bottom", fill="x")
        self.canvas.pack(side="left", fill="both", expand=True)

        self._image_id = None

    def show_protocol(self, key):
        fname = self.protocol_files.get(key)
        if not fname:
            return
        path = os.path.join(self.protocols_dir, fname)
        self.current_pdf = path

        if os.path.exists(path):
            # show only filename, not full path
            self.lbl_info.config(text=f"Selected: {fname}")
            self.btn_open.config(state="normal")
        else:
            self.lbl_info.config(text=f"File not found: {fname}\nPlease save the PDF in the 'assets/protocols' folder.")
            self.btn_open.config(state="disabled")

        # attempt to load into embedded viewer
        if os.path.exists(path):
            self._load_document(path)

    def _open_current_pdf(self):
        if not self.current_pdf:
            return
        if not os.path.exists(self.current_pdf):
            messagebox.showerror("Not found", f"PDF not found:\n{self.current_pdf}")
            return
        try:
            # Windows
            if fitz and Image and ImageTk:
                # already loaded into embedded viewer (or will be)
                self._load_document(self.current_pdf)
            else:
                if os.name == 'nt':
                    os.startfile(self.current_pdf)
                else:
                    import subprocess
                    opener = 'open' if sys.platform == 'darwin' else 'xdg-open'
                    subprocess.Popen([opener, self.current_pdf])
        except Exception as e:
            messagebox.showerror("Open Failed", f"Could not open PDF: {e}")

    # --- Embedded viewer methods ---
    def _load_document(self, path):
        if not fitz or not Image or not ImageTk:
            msg = "Embedded PDF viewer requires the 'PyMuPDF' and 'Pillow' packages.\n"
            msg += "Install with: pip install PyMuPDF Pillow"
            self.lbl_info.config(text=msg)
            return

        try:
            self.doc = fitz.open(path)
            self.page_count = self.doc.page_count
            self.current_page = 0
            self.zoom = 1.0
            # hide external-open button (we use embedded viewer)
            try:
                self.btn_open.pack_forget()
            except Exception:
                pass
            self._update_controls()
            self._render_page()
            # enable mouse/touchpad handlers for scrolling and zoom
            self._enable_input_bindings()
        except Exception as e:
            self.lbl_info.config(text=f"Failed to load PDF: {e}")

    def _render_page(self):
        if not self.doc:
            return
        try:
            page = self.doc.load_page(self.current_page)
            mat = fitz.Matrix(self.zoom, self.zoom)
            pix = page.get_pixmap(matrix=mat)
            mode = "RGBA" if pix.alpha else "RGB"
            img = Image.frombytes(mode, [pix.width, pix.height], pix.samples)
            # convert to PhotoImage and keep reference
            self._photo = ImageTk.PhotoImage(img)
            # draw on canvas and set scrollregion
            self.canvas.delete("all")
            self._image_id = self.canvas.create_image(0, 0, image=self._photo, anchor='nw')
            self.canvas.config(scrollregion=(0, 0, pix.width, pix.height))
            self.canvas.xview_moveto(0)
            self.canvas.yview_moveto(0)
            self.lbl_page.config(text=f"Page: {self.current_page+1}/{self.page_count}")
        except Exception as e:
            self.lbl_info.config(text=f"Render failed: {e}")

    def _enable_input_bindings(self):
        # Bind mouse wheel for vertical scroll
        try:
            self.canvas.bind_all('<MouseWheel>', self._on_mouse_wheel)
            # Shift + wheel for horizontal scroll
            self.canvas.bind_all('<Shift-MouseWheel>', self._on_shift_mouse_wheel)
            # Ctrl + wheel for zoom (common touchpads map pinch to ctrl+wheel)
            self.canvas.bind_all('<Control-MouseWheel>', self._on_ctrl_mouse_wheel)
        except Exception:
            pass
        # X11 scroll events
        try:
            self.canvas.bind_all('<Button-4>', lambda e: self.canvas.yview_scroll(-1, 'units'))
            self.canvas.bind_all('<Button-5>', lambda e: self.canvas.yview_scroll(1, 'units'))
        except Exception:
            pass

    def _on_mouse_wheel(self, event):
        # Vertical scroll
        try:
            if sys.platform == 'darwin':
                delta = int(event.delta)
            else:
                delta = int(event.delta / 120)
        except Exception:
            delta = 0
        if delta:
            self.canvas.yview_scroll(-delta, 'units')

    def _on_shift_mouse_wheel(self, event):
        # Horizontal scroll when holding Shift
        try:
            delta = int(event.delta / 120)
        except Exception:
            delta = 0
        if delta:
            self.canvas.xview_scroll(-delta, 'units')

    def _on_ctrl_mouse_wheel(self, event):
        # Zoom in/out with Ctrl + wheel
        try:
            delta = int(event.delta / 120)
        except Exception:
            delta = 0
        if delta > 0:
            self._change_zoom(1.1)
        elif delta < 0:
            self._change_zoom(1/1.1)

    def _prev_page(self):
        if not self.doc or self.current_page <= 0:
            return
        self.current_page -= 1
        self._render_page()

    def _next_page(self):
        if not self.doc or self.current_page >= self.page_count - 1:
            return
        self.current_page += 1
        self._render_page()

    def _change_zoom(self, factor):
        if not self.doc:
            return
        self.zoom *= factor
        # clamp zoom
        if self.zoom < 0.2: self.zoom = 0.2
        if self.zoom > 4.0: self.zoom = 4.0
        self._render_page()

    def _update_controls(self):
        enabled = bool(self.doc and self.page_count > 0)
        state = "normal" if enabled else "disabled"
        for btn in (self.btn_zoom_in, self.btn_zoom_out):
            btn.config(state=state)
        # always update page label
        if enabled:
            self.lbl_page.config(text=f"Page: {self.current_page+1}/{self.page_count}")
        else:
            self.lbl_page.config(text="Page: 0/0")
