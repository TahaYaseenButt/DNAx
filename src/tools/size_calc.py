import math
import tkinter as tk
from tkinter import messagebox
from ui_widgets import bind_mousewheel, PlaceholderEntry

class SizeCalculatorPage(tk.Frame):
    """
    Modern Minimalist DNA Size & Molecular Weight Calculator.
    Calculates physical dimensions and molecular weights for linear & circular constructs.
    """
    BASE_RISE_NM = 0.34  # nm per base (approximate for B-form DNA)

    def __init__(self, parent):
        super().__init__(parent, bg="#f8fafb")
        self._build_ui()

    def _build_ui(self):
        canvas = tk.Canvas(self, bg="#f8fafb", highlightthickness=0)
        scrollbar = tk.Scrollbar(self, orient="vertical", command=canvas.yview)
        canvas.configure(yscrollcommand=scrollbar.set)

        scrollbar.pack(side="right", fill="y")
        canvas.pack(side="left", fill="both", expand=True)

        content = tk.Frame(canvas, bg="#f8fafb", padx=24, pady=20)
        canvas_window = canvas.create_window((0, 0), window=content, anchor="nw")

        content.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
        canvas.bind("<Configure>", lambda e: canvas.itemconfig(canvas_window, width=e.width))

        bind_mousewheel(canvas, content)

        # 1. Header
        header_frame = tk.Frame(content, bg="#f8fafb")
        header_frame.pack(fill="x", pady=(0, 16))

        tk.Label(header_frame, text="DNA Size & Mass Calculator", font=("Segoe UI", 16, "bold"), bg="#f8fafb", fg="#0f172a").pack(anchor="w")
        tk.Label(header_frame, text="Calculate physical dimensions, molecular weight, and spatial migration for target DNA constructs.",
                 font=("Segoe UI", 9), bg="#f8fafb", fg="#64748b").pack(anchor="w")

        # 2. Input Card (React-style Card)
        card = tk.Frame(content, bg="#ffffff", bd=1, relief="solid", padx=20, pady=16)
        card.pack(fill="x", pady=(0, 16))

        input_row = tk.Frame(card, bg="#ffffff")
        input_row.pack(fill="x", pady=(0, 10))

        tk.Label(input_row, text="Target Construct Length (bp):", font=("Segoe UI", 10, "bold"), bg="#ffffff", fg="#334155").pack(side="left", padx=(0, 10))

        self.entry_var = tk.StringVar(value="500")
        self.entry = PlaceholderEntry(input_row, placeholder="Enter bp length", textvariable=self.entry_var, font=("Segoe UI", 11), width=16, normal_fg="#0f172a")
        self.entry.pack(side="left", padx=(0, 10))
        self.entry.bind("<Return>", lambda e: self._calculate())

        calc_btn = tk.Button(input_row, text="⚡ Calculate Size", command=self._calculate,
                             bg="#4f46e5", fg="#ffffff", font=("Segoe UI", 9, "bold"), relief="flat", padx=14, pady=5, cursor="hand2")
        calc_btn.pack(side="left", padx=(0, 10))

        # Quick Presets
        presets_row = tk.Frame(card, bg="#ffffff")
        presets_row.pack(fill="x")

        tk.Label(presets_row, text="Quick Presets:", font=("Segoe UI", 8), bg="#ffffff", fg="#94a3b8").pack(side="left", padx=(0, 6))
        for p in (100, 250, 500, 1000, 2000, 5000):
            tk.Button(presets_row, text=f"{p} bp", command=lambda val=p: self._fill_example(val),
                      font=("Segoe UI", 8), bg="#f1f5f9", fg="#475569", relief="flat", padx=8, pady=2, cursor="hand2").pack(side="left", padx=2)

        self.status_label = tk.Label(card, text="", font=("Segoe UI", 9), fg="#dc2626", bg="#ffffff")
        self.status_label.pack(anchor="w", pady=(8, 0))

        # 3. KPI Metrics Grid (2x2)
        grid_frame = tk.Frame(content, bg="#f8fafb")
        grid_frame.pack(fill="x", pady=(0, 16))
        grid_frame.grid_columnconfigure((0, 1), weight=1)

        def make_kpi_card(row, col, title, initial_val, accent_color="#6366f1"):
            c = tk.Frame(grid_frame, bg="#ffffff", bd=1, relief="solid", padx=16, pady=14)
            c.grid(row=row, column=col, sticky="nsew", padx=6, pady=6)
            
            bar = tk.Frame(c, bg=accent_color, height=3)
            bar.pack(fill="x", pady=(0, 8))

            tk.Label(c, text=title, font=("Segoe UI", 8, "bold"), bg="#ffffff", fg="#64748b").pack(anchor="w")
            lbl_val = tk.Label(c, text=initial_val, font=("Segoe UI", 12, "bold"), bg="#ffffff", fg="#0f172a", justify="left")
            lbl_val.pack(anchor="w", pady=(4, 0))
            return lbl_val

        self.linear_val = make_kpi_card(0, 0, "PHYSICAL LINEAR LENGTH (B-FORM)", "—", "#0288d1")
        self.circular_val = make_kpi_card(0, 1, "CIRCULAR DIAMETER (RELAXED)", "—", "#10b981")
        self.mw_val = make_kpi_card(1, 0, "ESTIMATED MOLECULAR WEIGHT (dsDNA)", "—", "#8b5cf6")
        self.avg_val = make_kpi_card(1, 1, "AVERAGE MASS PER BASE PAIR", "660.00 Da (dsDNA standard)", "#f59e0b")

        # 4. Bottom Action Bar
        action_card = tk.Frame(content, bg="#ffffff", bd=1, relief="solid", padx=16, pady=12)
        action_card.pack(fill="x")

        tk.Button(action_card, text="📋 Copy Calculated Metrics", command=self._copy_results,
                  font=("Segoe UI", 9, "bold"), bg="#f1f5f9", fg="#334155", relief="flat", padx=12, pady=6, cursor="hand2").pack(side="left", padx=(0, 8))

        self.use_in_gen_btn = tk.Button(
            action_card, text="Use in DNA Generator ➡", command=self._go_to_generator, 
            font=("Segoe UI", 9, "bold"), bg="#10b981", fg="#ffffff", relief="flat", padx=16, pady=6, cursor="hand2"
        )
        self.use_in_gen_btn.pack(side="right")

        # Initial calculation
        self._calculate()

    def _fill_example(self, n):
        self.entry_var.set(str(n))
        self._calculate()

    def _format_units(self, nm_value: float) -> str:
        um = nm_value / 1000.0
        mm = nm_value / 1_000_000.0
        return f"{nm_value:,.2f} nm  ({um:.4f} µm)"

    def _calculate(self):
        txt = self.entry_var.get().strip()
        self.status_label.config(text="")
        try:
            n = int(float(txt))
            if n < 0:
                raise ValueError("negative")
        except Exception:
            self.status_label.config(text="Please enter a non-negative integer number of bases.")
            return

        rise = self.BASE_RISE_NM
        linear_nm = n * rise
        circular_diameter_nm = (n * rise) / math.pi if n > 0 else 0.0

        self.linear_val.config(text=self._format_units(linear_nm))
        self.circular_val.config(text=self._format_units(circular_diameter_nm))
        
        # Molecular weight estimation for dsDNA (~660 Da / bp)
        total_mw = n * 660.0 if n > 0 else 0.0
        kda = total_mw / 1000.0
        self.mw_val.config(text=f"{total_mw:,.1f} Da  ({kda:,.2f} kDa)")
        self.avg_val.config(text="660.00 Da/bp (dsDNA average)")

    def _copy_results(self):
        linear = self.linear_val.cget("text")
        circular = self.circular_val.cget("text")
        mw = self.mw_val.cget("text")
        avg = self.avg_val.cget("text")
        if linear == "—" and circular == "—":
            messagebox.showinfo("Copy Results", "No results to copy. Run a calculation first.")
            return

        text = (
            f"Linear length:\n{linear}\n\n"
            f"Circular diameter:\n{circular}\n\n"
            f"Estimated molecular weight:\n{mw}\n"
            f"Avg mass per base:\n{avg}\n\n"
            f"(Assumed rise/base = {self.BASE_RISE_NM} nm)"
        )
        try:
            self.clipboard_clear()
            self.clipboard_append(text)
            messagebox.showinfo("Copy Results", "Results copied to clipboard.")
        except Exception:
            messagebox.showerror("Copy Failed", "Unable to copy to clipboard on this platform.")

    def _go_to_generator(self):
        """Navigate to DNA Generator page with current bp value pre-filled."""
        txt = self.entry_var.get().strip()
        try:
            n = int(float(txt))
            if n <= 0:
                messagebox.showwarning("Invalid Value", "Please enter a valid positive number of bases first.")
                return
        except Exception:
            messagebox.showwarning("Invalid Value", "Please enter a valid number of bases first.")
            return
        
        try:
            # Access the DNA Generator page and set the bp value
            dna_page = self.master.pages.get('dna')
            if dna_page:
                dna_page.set_bp_from_size_calc(n)
                self.master.show('dna')
            else:
                messagebox.showerror("Error", "DNA Generator page not found.")
        except Exception as e:
            messagebox.showerror("Error", f"Could not navigate: {e}")
