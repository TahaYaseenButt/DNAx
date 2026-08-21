import tkinter as tk


def _round_rect_coords(x1, y1, x2, y2, r):
    return (x1 + r, y1, x2 - r, y2, x1, y1 + r, x1, y2 - r, x2 - r, y1, x2, y2 - r)


class ModernButton(tk.Canvas):
    """Minimalist flat rounded button with subtle hover and click states.

    Use like: ModernButton(parent, text, command, width, height, bg, fg)
    """
    def __init__(self, parent, text="", command=None, width=120, height=36,
                 radius=8, bg="#1f2937", fg="white", font=("Segoe UI", 10, "bold"), **kwargs):
        super().__init__(parent, width=width, height=height, highlightthickness=0, bg=parent.cget("bg"), **kwargs)
        self._text = text
        self._cmd = command
        self._width = width
        self._height = height
        self._radius = radius
        self._bg = bg
        self._fg = fg
        self._font = font
        self._hover = False

        self._draw()
        self.bind("<Button-1>", lambda e: self._on_click())
        self.bind("<Enter>", lambda e: self._on_enter())
        self.bind("<Leave>", lambda e: self._on_leave())

    def _draw(self):
        self.delete("all")
        w = self._width
        h = self._height
        r = self._radius

        # subtle shadow (as a blurred dark rectangle approximation)
        self.create_rectangle(2, 2, w, h, outline="", fill="")

        fill = self._bg
        if self._hover:
            # slightly lighter on hover
            fill = self._adjust_color(self._bg, 1.06)

        # rounded background (approx using polygon points)
        pts = [r, 0, w - r, 0, w, r, w, h - r, w - r, h, r, h, 0, h - r, 0, r]
        self.create_polygon(pts, smooth=True, fill=fill, outline="")

        # centered text
        self.create_text(w // 2, h // 2, text=self._text, fill=self._fg, font=self._font)

    def _adjust_color(self, hexcolor, factor):
        hexcolor = hexcolor.lstrip('#')
        r = int(hexcolor[0:2], 16)
        g = int(hexcolor[2:4], 16)
        b = int(hexcolor[4:6], 16)
        r = max(0, min(255, int(r * factor)))
        g = max(0, min(255, int(g * factor)))
        b = max(0, min(255, int(b * factor)))
        return f"#{r:02x}{g:02x}{b:02x}"

    def _on_click(self):
        if callable(self._cmd):
            self._cmd()

    def _on_enter(self):
        self._hover = True
        self._draw()

    def _on_leave(self):
        self._hover = False
        self._draw()


class NavButton(tk.Frame):
    """Modern Vertical navigation button with active state pill, icon, and hover styling."""
    def __init__(self, parent, text, icon="", command=None, page_name="", active=False, width=220, height=42, bg="#0f172a", fg="#94a3b8"):
        super().__init__(parent, width=width, height=height, bg=bg)
        self.command = command
        self.page_name = page_name
        self._bg = bg
        self._fg = fg
        self._active = active
        self._hover = False
        self.pack_propagate(False)
        self.grid_propagate(False)

        # Left indicator bar (accent highlight when active)
        self.indicator = tk.Frame(self, bg="#6366f1" if active else bg, width=4)
        self.indicator.place(x=0, y=4, width=4, height=34)

        # Layout: Icon (left), Text (right)
        self.lbl_icon = tk.Label(self, text=icon, bg=self._bg, fg="#cbd5e1" if active else self._fg, font=("Segoe UI Symbol", 11), width=3)
        self.lbl_icon.place(x=6, y=0, height=42, width=40)

        self.lbl_text = tk.Label(self, text=text, bg=self._bg, fg="#ffffff" if active else self._fg,
                                 font=("Segoe UI", 9, "bold" if active else "normal"), anchor='w')
        self.lbl_text.place(x=46, y=0, height=42, width=165)

        # Bind events
        for w in (self, self.lbl_icon, self.lbl_text, self.indicator):
            w.bind('<Button-1>', lambda e: self._on_click())
            w.bind('<Enter>', lambda e: self._on_hover(True))
            w.bind('<Leave>', lambda e: self._on_hover(False))

    def set_active(self, active: bool):
        self._active = active
        bg_col = "#1e293b" if active else self._bg
        fg_col = "#ffffff" if active else self._fg
        self.config(bg=bg_col)
        self.lbl_icon.config(bg=bg_col, fg="#818cf8" if active else self._fg)
        self.lbl_text.config(bg=bg_col, fg=fg_col, font=("Segoe UI", 9, "bold" if active else "normal"))
        self.indicator.config(bg="#6366f1" if active else bg_col)

    def set_collapsed(self, collapsed: bool):
        if collapsed:
            self.lbl_text.place_forget()
            self.indicator.place_forget()
        else:
            self.lbl_text.place(x=46, y=0, height=42, width=165)
            self.indicator.place(x=0, y=4, width=4, height=34)

    def _on_click(self):
        if callable(self.command):
            self.command()

    def _on_hover(self, enter: bool):
        if self._active:
            return
        bg_col = "#1e293b" if enter else self._bg
        fg_col = "#f1f5f9" if enter else self._fg
        self.config(bg=bg_col)
        self.lbl_icon.config(bg=bg_col, fg="#818cf8" if enter else self._fg)
        self.lbl_text.config(bg=bg_col, fg=fg_col)
        self.indicator.config(bg="#475569" if enter else self._bg)


def bind_mousewheel(canvas, target_widget=None):
    """
    Universally binds mouse wheel to canvas so that scrolling works seamlessly
    over any nested widget (labels, frames, buttons, text) inside the scrollable region.
    """
    def _on_mousewheel(event):
        try:
            bbox = canvas.bbox("all")
            if bbox and bbox[3] > canvas.winfo_height():
                # On Windows event.delta is +/-120
                shift = int(-1 * (event.delta / 120))
                canvas.yview_scroll(shift, "units")
        except Exception:
            pass

    def _on_enter(event=None):
        canvas.bind_all("<MouseWheel>", _on_mousewheel)

    def _on_leave(event=None):
        canvas.unbind_all("<MouseWheel>")

    canvas.bind("<Enter>", _on_enter)
    canvas.bind("<Leave>", _on_leave)
    if target_widget:
        target_widget.bind("<Enter>", _on_enter)
        target_widget.bind("<Leave>", _on_leave)


class TopNavBar(tk.Frame):
    """
    Modern Minimalist React-Style Top Navigation Bar featuring:
    - Interactive History Navigation: ⬅ Back & Forward ➡ buttons with hover & state tracking
    - Direct Home Shortcut
    - Sleek Pipeline Stepper Tabs (1. Size -> 2. DNA Gen -> 3. BLAST -> 4. Primers -> 5. Probes -> 6. Review & Save)
    - Quick Database Library Status Pill
    """
    PIPELINE_STEPS = [
        ("size", "1. Size"),
        ("dna", "2. DNA Gen"),
        ("comparator", "3. BLAST"),
        ("primer", "4. Primers"),
        ("qpcr", "5. Probes"),
        ("export", "6. Review & Save")
    ]

    def __init__(self, parent, navigation_controller, *args, **kwargs):
        super().__init__(parent, bg="#ffffff", height=50, bd=0, *args, **kwargs)
        self.nav = navigation_controller
        self.pack_propagate(False)

        # Bottom hairline border
        self.border = tk.Frame(self, bg="#e2e8f0", height=1)
        self.border.pack(side="bottom", fill="x")

        # Inner container
        self.inner = tk.Frame(self, bg="#ffffff", padx=16)
        self.inner.pack(fill="both", expand=True)

        # 1. Back & Forward History Controls
        hist_box = tk.Frame(self.inner, bg="#ffffff")
        hist_box.pack(side="left", pady=8)

        self.btn_back = tk.Button(
            hist_box, text="← Back", command=self.nav.go_back,
            font=("Segoe UI", 9, "bold"), bg="#f8fafc", fg="#475569",
            activebackground="#f1f5f9", activeforeground="#0f172a",
            bd=1, relief="solid", padx=10, pady=3, cursor="hand2"
        )
        self.btn_back.pack(side="left", padx=(0, 4))

        self.btn_fwd = tk.Button(
            hist_box, text="Forward →", command=self.nav.go_forward,
            font=("Segoe UI", 9, "bold"), bg="#f8fafc", fg="#475569",
            activebackground="#f1f5f9", activeforeground="#0f172a",
            bd=1, relief="solid", padx=10, pady=3, cursor="hand2"
        )
        self.btn_fwd.pack(side="left", padx=(0, 8))

        # Home button
        self.btn_home = tk.Button(
            hist_box, text="🏠", command=lambda: self.nav.show("home"),
            font=("Segoe UI", 9), bg="#f8fafc", fg="#334155",
            bd=1, relief="solid", padx=8, pady=3, cursor="hand2"
        )
        self.btn_home.pack(side="left", padx=(0, 10))

        # Divider
        tk.Frame(self.inner, bg="#e2e8f0", width=1).pack(side="left", fill="y", pady=10, padx=(0, 10))

        # 2. Interactive Pipeline Stepper (React Webapp Style)
        self.step_frame = tk.Frame(self.inner, bg="#ffffff")
        self.step_frame.pack(side="left", pady=8)

        self.step_buttons = {}
        for idx, (page_key, step_title) in enumerate(self.PIPELINE_STEPS):
            btn = tk.Button(
                self.step_frame, text=step_title, command=lambda p=page_key: self.nav.show(p),
                font=("Segoe UI", 8, "bold"), bg="#f1f5f9", fg="#64748b",
                activebackground="#e2e8f0", bd=0, padx=10, pady=4, cursor="hand2", relief="flat"
            )
            btn.pack(side="left", padx=2)
            self.step_buttons[page_key] = btn

            if idx < len(self.PIPELINE_STEPS) - 1:
                tk.Label(self.step_frame, text="›", font=("Segoe UI", 10, "bold"), bg="#ffffff", fg="#cbd5e1").pack(side="left", padx=1)

        # 3. Right Status Badges
        right_box = tk.Frame(self.inner, bg="#ffffff")
        right_box.pack(side="right", pady=8)

        self.btn_db_chip = tk.Button(
            right_box, text="🗄 DNA Library", command=lambda: self.nav.show("matrix_db"),
            font=("Segoe UI", 8, "bold"), bg="#f5f3ff", fg="#7c3aed",
            activebackground="#ede9fe", bd=1, relief="solid", padx=10, pady=3, cursor="hand2"
        )
        self.btn_db_chip.pack(side="left", padx=(0, 8))

        tk.Label(right_box, text="v2.0 PRO", font=("Segoe UI", 8, "bold"), bg="#e0f2fe", fg="#0369a1", padx=6, pady=2).pack(side="left")

        # Register navigation listener to auto-update button states
        self.nav.register_listener(self._on_navigation_change)

    def _on_navigation_change(self, current_page, can_back, can_forward):
        # Update Back button
        if can_back:
            self.btn_back.config(state="normal", fg="#0f172a", bg="#f1f5f9", cursor="hand2")
        else:
            self.btn_back.config(state="disabled", fg="#cbd5e1", bg="#f8fafc", cursor="arrow")

        # Update Forward button
        if can_forward:
            self.btn_fwd.config(state="normal", fg="#0f172a", bg="#f1f5f9", cursor="hand2")
        else:
            self.btn_fwd.config(state="disabled", fg="#cbd5e1", bg="#f8fafc", cursor="arrow")

        # Update Stepper active highlight
        for page_key, btn in self.step_buttons.items():
            if page_key == current_page:
                btn.config(bg="#4f46e5", fg="#ffffff")
            else:
                btn.config(bg="#f1f5f9", fg="#64748b")

        # Update DB chip text with live count
        try:
            from utils.database import get_db
            db = get_db()
            count = db.count_sequences()
            self.btn_db_chip.config(text=f"🗄 DNA Library ({count})")
        except Exception:
            pass


class PlaceholderEntry(tk.Entry):
    """Entry with placeholder text (like HTML placeholder)."""
    def __init__(self, parent, placeholder="", color='grey', normal_fg='black', **kwargs):
        super().__init__(parent, **kwargs)
        self.placeholder = placeholder
        self.placeholder_color = color
        self.default_fg = normal_fg
        self.bind('<FocusIn>', self._clear_placeholder)
        self.bind('<FocusOut>', self._show_placeholder)
        self._show_placeholder()

    def _show_placeholder(self, event=None):
        if not self.get():
            self.insert(0, self.placeholder)
            self.config(fg=self.placeholder_color)

    def _clear_placeholder(self, event=None):
        if self.cget('fg') == self.placeholder_color:
            self.delete(0, 'end')
            self.config(fg=self.default_fg)


class CircularLoader(tk.Canvas):
    """Simple animated circular loader (arc) that can be started/stopped.

    Usage: create the widget and call `start()` to show and animate,
    call `stop()` to hide it.
    """
    def __init__(self, parent, size=20, line_width=3, fg="#1976d2", bg=None, speed=50, *args, **kwargs):
        bgcol = parent.cget('bg') if bg is None else bg
        super().__init__(parent, width=size, height=size, bg=bgcol, highlightthickness=0, *args, **kwargs)
        self.size = size
        self._line = line_width
        self._fg = fg
        self._speed = speed  # ms per frame
        self._angle = 0
        pad = 2
        self._arc_id = self.create_arc(pad, pad, size - pad, size - pad, start=self._angle, extent=260,
                                       style='arc', outline=self._fg, width=self._line)
        self._running = False

    def _animate(self):
        if not self._running:
            return
        self._angle = (self._angle + 15) % 360
        try:
            self.itemconfig(self._arc_id, start=self._angle)
        except Exception:
            pass
        self.after(self._speed, self._animate)

    def start(self):
        if self._running:
            return
        self._running = True
        self.pack_propagate(False)
        # Ensure visible
        try:
            self.pack(side='left', padx=(6,4))
        except Exception:
            pass
        self._animate()

    def stop(self):
        if not self._running:
            return
        self._running = False
        try:
            self.pack_forget()
        except Exception:
            pass

