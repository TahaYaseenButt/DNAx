import tkinter as tk
from tkinter import ttk, messagebox
import tools.simulation as sim

import math

class PlasmidMap(tk.Canvas):
    """Visualizes the circular DNA.
    Modes:
    1. Vector Map (Low Zoom): Thin backbone, feature arrows.
    2. Atomic Map (High Zoom): Actual ATGC bases, double helix ladder.
    """
    def __init__(self, parent, size=450, **kwargs):
        super().__init__(parent, width=size, height=size, bg="#ffffff", highlightthickness=0, **kwargs)
        self.base_size = size
        self.center = size / 2
        self.base_radius = (size / 2) - 100
        
        self.rotation = 0
        self.scale_factor = 1.0
        self.fragments = []
        self.total_len = 0
        
        # Panning state
        self.offset_x = 0
        self.offset_y = 0
        
        # Panning bindings
        self.bind("<ButtonPress-1>", self.on_drag_start)
        self.bind("<B1-Motion>", self.on_drag_motion)
        
        # Mouse Wheel bindings
        self.bind("<MouseWheel>", self.on_mouse_wheel)  # Windows
        self.bind("<Button-4>", self.on_mouse_wheel)    # Linux scroll up
        self.bind("<Button-5>", self.on_mouse_wheel)    # Linux scroll down
        
        self._drag_data = {"x": 0, "y": 0}

    def on_drag_start(self, event):
        self._drag_data["x"] = event.x
        self._drag_data["y"] = event.y

    def on_drag_motion(self, event):
        dx = event.x - self._drag_data["x"]
        dy = event.y - self._drag_data["y"]
        
        # Update internal offset state so redraws stick
        self.offset_x += dx
        self.offset_y += dy
        
        self.move("all", dx, dy)
        self._drag_data["x"] = event.x
        self._drag_data["y"] = event.y

    def on_mouse_wheel(self, event):
        # Determine direction
        delta = 0
        if event.num == 5 or event.delta < 0:
            delta = -0.1
        elif event.num == 4 or event.delta > 0:
            delta = 0.1
            
        new_scale = self.scale_factor + delta
        if new_scale < 0.5: new_scale = 0.5
        if new_scale > 20.0: new_scale = 20.0
        
        self.scale_factor = new_scale
        
        # Notify parent slider (if linked) - optional but nice
        # For now just redraw
        self.draw(self.fragments, self.total_len)

    def reset_view(self):
        self.scale_factor = 1.0
        self.offset_x = 0
        self.offset_y = 0
        self.rotation = 0
        self.draw(self.fragments, self.total_len)
        return 1.0, 0 # Return new values for sliders to update themselves if needed

    def set_view(self, rotation, scale):
        self.rotation = float(rotation)
        self.scale_factor = float(scale)
        self.draw(self.fragments, self.total_len)

    def draw(self, fragments, total_len):
        self.fragments = fragments
        self.total_len = total_len
        self.delete("all")
        if not fragments or total_len == 0:
            return
            
        # Reset position (centering) on redraw is tricky if we allow panning.
        # Ideally, we redraw relative to center, but if user panned away, they might lose it.
        # For simplicity in this demo, we recenter on every major update.
        # User pans to look around, but changing slider resets view.
        
        if self.scale_factor > 4.0:
            self.draw_atomic_mode()
        else:
            self.draw_vector_mode()

    def draw_vector_mode(self):
        radius = self.base_radius * self.scale_factor
        cx, cy = self.center + self.offset_x, self.center + self.offset_y
        
        # Backbone
        self.create_oval(cx - radius, cy - radius, cx + radius, cy + radius, outline="#cfd8dc", width=3)
        colors = ["#42a5f5", "#66bb6a", "#ffa726", "#ab47bc", "#ef5350", "#8d6e63"]
        
        base_angle = 90 - self.rotation
        current_angle = base_angle
        
        for i, frag in enumerate(self.fragments):
            frag_len = len(frag.get('start_site', '')) + len(frag.get('core', ''))
            extent = (frag_len / self.total_len) * 360
            color = colors[i % len(colors)]
            
            # Arrow
            w = 14 * self.scale_factor
            if w > 40: w = 40 # Cap thickness
            
            self.create_arc(cx - radius + w/2, cy - radius + w/2, cx + radius - w/2, cy + radius - w/2,
                            start=current_angle, extent=-extent, outline=color, width=w, style="arc")
            
            current_angle -= extent
            
        # Sites
        current_angle = base_angle
        for i, frag in enumerate(self.fragments):
            frag_len = len(frag.get('start_site', '')) + len(frag.get('core', ''))
            extent = (frag_len / self.total_len) * 360
            
            start_enz = frag.get('start_enzyme', '?')
            rad_angle = math.radians(current_angle)
            
            sx = cx + radius * math.cos(rad_angle)
            sy = cy - radius * math.sin(rad_angle)
            
            label_dist = radius + (40 * self.scale_factor)
            if self.scale_factor > 2: label_dist = radius + 60 # Don't scale label distance infinitely
            
            lx = cx + label_dist * math.cos(rad_angle)
            ly = cy - label_dist * math.sin(rad_angle)
            
            self.create_line(sx, sy, lx, ly, fill="#546e7a", width=1)
            
            anchor = "center"
            if lx > cx + 10: anchor = "w"
            elif lx < cx - 10: anchor = "e"
            elif ly < cy: anchor = "s"
            else: anchor = "n"
            
            fs = int(10 * self.scale_factor)
            if fs > 24: fs = 24
            if fs < 6: fs = 6
            self.create_text(lx, ly, text=start_enz, font=("Segoe UI", fs, "bold"), fill="#263238", anchor=anchor)
            
            current_angle -= extent
            
        self.create_text(cx, cy, text=f"{self.total_len} bp", font=("Segoe UI", int(14*self.scale_factor), "bold"), fill="#546e7a")

    def draw_atomic_mode(self):
        """Draws individual bases (A-T, G-C) in a ladder configuration."""
        radius = self.base_radius * self.scale_factor
        cx, cy = self.center + self.offset_x, self.center + self.offset_y
        
        # Construct full sequence
        # We need the actual chars to draw
        # fragments are dictionaries
        full_seq = ""
        frag_starts = [] # (index, name, color)
        colors = ["#42a5f5", "#66bb6a", "#ffa726", "#ab47bc", "#ef5350", "#8d6e63"]
        
        cursor = 0
        for i, frag in enumerate(self.fragments):
            seq = frag.get('start_site', '') + frag.get('core', '')
            frag_starts.append((cursor, frag.get('start_enzyme', ''), colors[i % len(colors)]))
            full_seq += seq
            cursor += len(seq)
            
        # Angle per base
        # 360 degrees / total bases
        angle_per_base = 360.0 / len(full_seq)
        
        base_angle = 90 - self.rotation
        
        comp_map = {'A':'T', 'T':'A', 'C':'G', 'G':'C', 'N':'N'}
        
        font_size = int(8 * (self.scale_factor / 5.0)) # linear scaling from zoom 5
        if font_size < 8: font_size = 8
        font = ("Consolas", font_size, "bold")
        
        # Backbone (Helix Rails)
        # Inner and Outer strands
        rail_dist = 12 * (self.scale_factor / 5.0)
        r_out = radius + rail_dist
        r_in = radius - rail_dist
        
        # If total bases large, don't draw rails as circles, they might be huge.
        # But create_oval handles it usually.
        self.create_oval(cx - r_out, cy - r_out, cx + r_out, cy + r_out, outline="#546e7a", width=2)
        self.create_oval(cx - r_in, cy - r_in, cx + r_in, cy + r_in, outline="#546e7a", width=2)

        for idx, char in enumerate(full_seq):
            theta_deg = base_angle - (idx * angle_per_base)
            theta_rad = math.radians(theta_deg)
            
            cos_t = math.cos(theta_rad)
            sin_t = math.sin(theta_rad) # y is inverted
            
            # Position for Outer Base (Top Strand)
            x_out = cx + r_out * cos_t
            y_out = cy - r_out * sin_t
            
            # Position for Inner Base (Bottom Strand)
            x_in = cx + r_in * cos_t
            y_in = cy - r_in * sin_t
            
            # Rung (Connection)
            self.create_line(x_in, y_in, x_out, y_out, fill="#cfd8dc", width=1)
            
            # Text Color based on base (Sanger colors)
            # A: Green, T: Red, G: Black/Yellow, C: Blue
            c_code = "#333"
            if char == 'A': c_code = "#2e7d32" # Green
            elif char == 'T': c_code = "#c62828" # Red
            elif char == 'G': c_code = "#f9a825" # Yellow-ish
            elif char == 'C': c_code = "#1565c0" # Blue
            
            # Draw Char
            # Rotate text to match angle? Tkinter Canvas text doesn't rotate easily.
            # We draw standard text. At high zoom it looks okay.
            self.create_text(x_out, y_out, text=char, fill=c_code, font=font)
            
            comp = comp_map.get(char, 'N')
            c_comp = "#333"
            if comp == 'A': c_comp = "#2e7d32"
            elif comp == 'T': c_comp = "#c62828"
            elif comp == 'G': c_comp = "#f9a825"
            elif comp == 'C': c_comp = "#1565c0"
            
            
            self.create_text(x_in, y_in, text=comp, fill=c_comp, font=font)

        # Draw Labels (Restriction Sites) for Atomic Mode
        # These need to be drawn ON TOP of the helix
        cursor = 0
        base_angle = 90 - self.rotation
        angle_per_base = 360.0 / len(full_seq)
        
        for i, frag in enumerate(self.fragments):
            start_enz = frag.get('start_enzyme', '?')
            frag_len = len(frag.get('start_site', '')) + len(frag.get('core', ''))
            
            # Label belongs at 'cursor' index
            theta_deg = base_angle - (cursor * angle_per_base)
            theta_rad = math.radians(theta_deg)
            
            # Position outside the outer rail
            label_dist = r_out + 40
            lx = cx + label_dist * math.cos(theta_rad)
            ly = cy - label_dist * math.sin(theta_rad)
            
            # Marker on the DNA
            sx = cx + r_out * math.cos(theta_rad)
            sy = cy - r_out * math.sin(theta_rad)
            
            self.create_line(sx, sy, lx, ly, fill="#546e7a", width=2)
            
            # Text
            anchor = "center"
            if lx > cx + 10: anchor = "w"
            elif lx < cx - 10: anchor = "e"
            elif ly < cy: anchor = "s"
            else: anchor = "n"
            
            self.create_text(lx, ly, text=start_enz, font=("Segoe UI", 12, "bold"), fill="#d32f2f", anchor=anchor)
            
            cursor += frag_len

class ValidationPage(tk.Frame):
    """
    Industrial In Silico Validation Page (QC Report).
    Displays detailed analysis of PCR, Digestion, and Ligation phases.
    """
    def __init__(self, parent):
        super().__init__(parent, bg="#f0f2f5")
        self.parent = parent
        self.report_data = None
        
        # Header
        header = tk.Frame(self, bg="#ffffff", height=60)
        header.pack(fill="x", side="top")
        tk.Label(header, text="QC / In Silico Validation", font=("Segoe UI", 18, "bold"), bg="#ffffff", fg="#1a237e").pack(side="left", padx=20, pady=10)
        
        # Toolbar
        toolbar = tk.Frame(self, bg="#e0e0e0", height=40)
        toolbar.pack(fill="x", side="top")
        
        self.btn_refresh = tk.Button(toolbar, text="Fetch Latest Design", command=self.load_latest_design, bg="#1976d2", fg="white", font=("Segoe UI", 9, "bold"), relief="flat", padx=10)
        self.btn_refresh.pack(side="left", padx=10, pady=5)
        
        tk.Label(toolbar, text="source: DNA Generator", bg="#e0e0e0", fg="#555").pack(side="left")
        
        # Main Content Area
        self.content_frame = tk.Frame(self, bg="#f0f2f5")
        self.content_frame.pack(fill="both", expand=True, padx=20, pady=20)
        
        # Placeholder / Empty State
        self.empty_lbl = tk.Label(self.content_frame, text="No Validation Data Loaded.\nGo to 'DNA Generate' or click Fetch.", font=("Segoe UI", 14), fg="#757575", bg="#f0f2f5")
        self.empty_lbl.pack(expand=True)
        
        # Report Container (Hidden initially)
        self.report_canvas = tk.Canvas(self.content_frame, bg="#ffffff", highlightthickness=0)
        self.scrollbar = tk.Scrollbar(self.content_frame, orient="vertical", command=self.report_canvas.yview)
        self.report_inner = tk.Frame(self.report_canvas, bg="#ffffff")
        
        self.report_inner.bind("<Configure>", lambda e: self.report_canvas.configure(scrollregion=self.report_canvas.bbox("all")))
        self.window_id = self.report_canvas.create_window((0,0), window=self.report_inner, anchor="nw")
        self.report_canvas.configure(yscrollcommand=self.scrollbar.set)
        
        # Bind resize to update canvas window width
        self.report_canvas.bind("<Configure>", self._on_canvas_configure)

    def _on_canvas_configure(self, event):
        self.report_canvas.itemconfig(self.window_id, width=event.width)

    def load_latest_design(self):
        """Attempts to fetch fragments from the DNA Generate page logic."""
        # We need to access the sibling page 'DNAGeneratePage'
        # The parent is NavigationFrame, which has .pages dict
        try:
            nav = self.parent
            # Main.py registers it as "dna"
            gen_page = nav.pages.get('dna')
            if not gen_page:
                messagebox.showerror("Error", "DNA Generator module not found.")
                return
            
            # Access the private attribute for fragments
            frags = getattr(gen_page, '_last_fragments', None)
            
            if not frags:
                messagebox.showinfo("Validation", "No active design found in DNA Generator.\nPlease generate a sequence first.")
                return
            
            # Run simulation
            report = sim.run_simulation(frags)
            self._render_report(report, frags)
            
        except Exception as e:
            messagebox.showerror("System Error", f"Could not link to Generator: {e}")

    def _render_report(self, report, fragments=None):
        self.empty_lbl.pack_forget()
        
        # Clear previous
        for widget in self.report_inner.winfo_children():
            widget.destroy()
            
        # Show canvas
        self.report_canvas.pack(side="left", fill="both", expand=True)
        self.scrollbar.pack(side="right", fill="y")
        
        # 1. Executive Summary Card
        summary_frame = tk.Frame(self.report_inner, bg="#f5f7fa", bd=1, relief="solid")
        summary_frame.pack(fill="x", padx=10, pady=10)
        
        s_color = "#2e7d32" if report["success"] else "#c62828"
        s_text = "PASS" if report["success"] else "FAIL"
        
        tk.Label(summary_frame, text="VALIDATION STATUS", font=("Segoe UI", 10, "bold"), fg="#555", bg="#f5f7fa").pack(anchor="w", padx=10, pady=(10,2))
        tk.Label(summary_frame, text=s_text, font=("Segoe UI", 24, "bold"), fg=s_color, bg="#f5f7fa").pack(anchor="w", padx=10, pady=(0,10))
        
        if "final_seq" in report and report["final_seq"]:
             seq_len = len(report['final_seq'])
             tk.Label(summary_frame, text=f"Final Construct Length: {seq_len} bp", font=("Segoe UI", 11), bg="#f5f7fa").pack(anchor="w", padx=10, pady=(0,10))

             # --- PLASMID VISUALIZATION ---
             viz_frame = tk.Frame(self.report_inner, bg="#ffffff")
             viz_frame.pack(fill="x", padx=10, pady=10)
             
             tk.Label(viz_frame, text="Plasmid Map", font=("Segoe UI", 12, "bold"), bg="#ffffff").pack(anchor="center")
             
             # Controls
             ctrl_frame = tk.Frame(viz_frame, bg="#ffffff")
             ctrl_frame.pack(fill="x", pady=5)
             
             # Zoom
             tk.Label(ctrl_frame, text="Zoom:", bg="#ffffff").pack(side="left", padx=5)
             s_zoom = tk.Scale(ctrl_frame, from_=0.5, to=20.0, resolution=0.1, orient="horizontal", showvalue=0, length=200, bg="#ffffff")
             s_zoom.set(1.0)
             s_zoom.pack(side="left", padx=5)
             tk.Label(ctrl_frame, text="(Drag map to pan)", font=("Segoe UI", 8), bg="#ffffff", fg="#777").pack(side="left")
             
             # Rotation
             tk.Label(ctrl_frame, text="Rotate:", bg="#ffffff").pack(side="left", padx=5)
             s_rot = tk.Scale(ctrl_frame, from_=0, to=360, orient="horizontal", showvalue=0, length=100, bg="#ffffff")
             s_rot.set(0)
             s_rot.pack(side="left", padx=5)
             
             # Reset Button
             def _do_reset():
                 val_s, val_r = pmap.reset_view()
                 s_zoom.set(val_s)
                 s_rot.set(val_r)
                 
             tk.Button(ctrl_frame, text="⟲ Reset View", command=_do_reset, bg="#eceff1").pack(side="left", padx=15)

             pmap = PlasmidMap(viz_frame, size=450)
             pmap.pack(pady=10)
             pmap.draw(fragments, seq_len)
             
             # Bind Sliders
             def _update_view(e):
                 pmap.set_view(s_rot.get(), s_zoom.get())
             
             s_zoom.bind("<Motion>", _update_view)
             s_zoom.bind("<ButtonRelease-1>", _update_view)
             s_rot.bind("<Motion>", _update_view)
             s_rot.bind("<ButtonRelease-1>", _update_view)
             
             # --- SEQUENCE VIEWER ---
             tk.Label(viz_frame, text="Circular Sequence (5'->3')", font=("Segoe UI", 11, "bold"), bg="#ffffff").pack(anchor="w")
             
             seq_txt = tk.Text(viz_frame, height=6, font=("Consolas", 10), wrap="char", bg="#f9f9f9", bd=1, relief="solid")
             seq_txt.pack(fill="x", pady=(5,5))
             seq_txt.insert("1.0", report["final_seq"])
             seq_txt.config(state="disabled")
             
             def _copy_seq():
                 self.clipboard_clear()
                 self.clipboard_append(report["final_seq"])
                 messagebox.showinfo("Copied", "Sequence copied to clipboard.")
                 
             tk.Button(viz_frame, text="Copy Sequence", command=_copy_seq).pack(anchor="e")

        # 2. Detailed Steps
        tk.Label(self.report_inner, text="Detailed Traceability", font=("Segoe UI", 14, "bold"), bg="#ffffff", fg="#333").pack(anchor="w", padx=10, pady=(10,5))
        
        for step in report["steps"]:
            self._create_step_card(step)

    def _create_step_card(self, step):
        card = tk.Frame(self.report_inner, bg="#ffffff", bd=1, relief="solid")
        card.pack(fill="x", padx=10, pady=5)
        
        # Header
        h_bg = "#e8f5e9" if step["status"] else "#ffebee"
        h_fg = "#2e7d32" if step["status"] else "#c62828"
        icon = "✔" if step["status"] else "✖"
        
        header = tk.Frame(card, bg=h_bg, height=30)
        header.pack(fill="x")
        tk.Label(header, text=f"{icon} {step['name']}", font=("Segoe UI", 11, "bold"), fg=h_fg, bg=h_bg).pack(side="left", padx=10, pady=5)
        
        # Logs
        log_frame = tk.Frame(card, bg="#ffffff")
        log_frame.pack(fill="x", padx=10, pady=5)
        
        for log in step["logs"]:
            fg = "#424242"
            if "FAIL" in log: fg = "#d32f2f"
            elif "PASS" in log: fg = "#388e3c"
            elif "WARN" in log: fg = "#f57c00"
            
            tk.Label(log_frame, text=f"• {log}", font=("Consolas", 9), bg="#ffffff", fg=fg, justify="left", wraplength=700).pack(anchor="w", pady=1)
