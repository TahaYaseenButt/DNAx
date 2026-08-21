import math
import tkinter as tk
from tkinter import messagebox


class SizeCalculatorPage(tk.Frame):
    """Improved UI for the Size Calculator.

    Uses same assumptions as before (0.34 nm per base) but presents
    results in a clean, card-like layout with copy-to-clipboard.
    """

    BASE_RISE_NM = 0.34  # nm per base (approximate for B-form DNA)

    def __init__(self, parent):
        super().__init__(parent, bg="#f8fafb")

        header = tk.Label(self, text="Size Calculator", font=("Segoe UI", 18, "bold"), bg="#f8fafb")
        header.pack(pady=(12, 6))

        # Input card
        card = tk.Frame(self, bg="#ffffff", bd=1, relief="solid")
        card.pack(padx=16, pady=8, fill="x")
        card.grid_columnconfigure(1, weight=1)

        lbl = tk.Label(card, text="Number of bases", font=("Segoe UI", 11), bg="#ffffff")
        lbl.grid(row=0, column=0, sticky="w", padx=12, pady=(12, 6))

        self.entry_var = tk.StringVar()
        from ui_widgets import PlaceholderEntry
        entry = PlaceholderEntry(card, placeholder="Enter number of bases", textvariable=self.entry_var, font=("Segoe UI", 12), width=18, normal_fg="#000000")
        entry.grid(row=0, column=1, sticky="w", padx=(0,12), pady=(12, 6))

        hint = tk.Label(card, text="Integer (e.g. 1000)", font=("Segoe UI", 9), fg="#666666", bg="#ffffff")
        hint.grid(row=1, column=0, columnspan=2, sticky="w", padx=12, pady=(0,12))

        btn_frame = tk.Frame(card, bg="#ffffff")
        btn_frame.grid(row=2, column=0, columnspan=2, sticky="w", padx=12, pady=(0,12))

        calc_btn = tk.Button(btn_frame, text="Calculate", command=self._calculate, bg="#2e7d32", fg="white", padx=12, pady=6)
        calc_btn.pack(side="left")

        # Results card
        res_card = tk.Frame(self, bg="#ffffff", bd=1, relief="solid")
        res_card.pack(padx=16, pady=8, fill="both", expand=True)
        res_card.grid_columnconfigure(1, weight=1)

        self.status_label = tk.Label(res_card, text="", font=("Segoe UI", 10), fg="#d32f2f", bg="#ffffff")
        self.status_label.grid(row=0, column=0, columnspan=2, sticky="w", padx=12, pady=(12,0))

        tk.Label(res_card, text="Linear length:", font=("Segoe UI", 11, "bold"), bg="#ffffff").grid(row=1, column=0, sticky="w", padx=12, pady=(8,4))
        self.linear_val = tk.Label(res_card, text="—", font=("Courier New", 11), bg="#ffffff")
        self.linear_val.grid(row=1, column=1, sticky="w", padx=12, pady=(8,4))

        tk.Label(res_card, text="Approx. circular diameter:", font=("Segoe UI", 11, "bold"), bg="#ffffff").grid(row=2, column=0, sticky="w", padx=12, pady=(4,8))
        self.circular_val = tk.Label(res_card, text="—", font=("Courier New", 11), bg="#ffffff")
        self.circular_val.grid(row=2, column=1, sticky="w", padx=12, pady=(4,8))

        # Copy/export area
        copy_frame = tk.Frame(res_card, bg="#ffffff")
        copy_frame.grid(row=3, column=0, columnspan=2, sticky="e", padx=12, pady=(0,12))
        copy_btn = tk.Button(copy_frame, text="Copy Results", command=self._copy_results, padx=10, pady=6)
        copy_btn.pack(side="left")
        
        # New Link to DNA Generator
        link_btn = tk.Button(copy_frame, text="Use in DNA Generator", command=self._go_to_generator, 
                             bg="#e3f2fd", fg="#1565c0", padx=10, pady=6)
        link_btn.pack(side="left", padx=10)

        # footer note
        note = tk.Label(self, text="Assumption: rise per base = 0.34 nm (typical B-form DNA). Results shown in nm, µm and mm.", font=("Segoe UI", 9), fg="#555555", bg="#f8fafb")
        note.pack(padx=16, pady=(6,12), anchor="w")

    def _fill_example(self, n):
        self.entry_var.set(str(n))
        self._calculate()

    def _format_units(self, nm_value: float) -> str:
        um = nm_value / 1000.0
        mm = nm_value / 1_000_000.0
        return f"{nm_value:,.2f} nm  |  {um:.4f} µm  |  {mm:.6f} mm"

    def _calculate(self):
        txt = self.entry_var.get().strip()
        self.status_label.config(text="")
        try:
            n = int(float(txt))
            if n < 0:
                raise ValueError("negative")
        except Exception:
            self.status_label.config(text="Please enter a non-negative integer number of bases.")
            self.linear_val.config(text="—")
            self.circular_val.config(text="—")
            return

        rise = self.BASE_RISE_NM
        linear_nm = n * rise
        circular_diameter_nm = (n * rise) / math.pi if n > 0 else 0.0

        self.linear_val.config(text=self._format_units(linear_nm))
        self.circular_val.config(text=self._format_units(circular_diameter_nm))

    def _copy_results(self):
        linear = self.linear_val.cget("text")
        circular = self.circular_val.cget("text")
        if linear == "—" and circular == "—":
            messagebox.showinfo("Copy Results", "No results to copy. Run a calculation first.")
            return

        text = f"Linear length:\n{linear}\n\nCircular diameter:\n{circular}\n\n(Assumed rise/base = {self.BASE_RISE_NM} nm)"
        try:
            self.clipboard_clear()
            self.clipboard_append(text)
            messagebox.showinfo("Copy Results", "Results copied to clipboard.")
        except Exception:
            messagebox.showerror("Copy Failed", "Unable to copy to clipboard on this platform.")

    def _go_to_generator(self):
        txt = self.entry_var.get().strip()
        if not txt:
             messagebox.showinfo("Wait", "Calculate a size first.")
             return
        
        try:
            # Assuming parent is NavigationFrame container's page wrapper
            # self.master.master should be NavigationFrame? 
            # In main.py: self.navigate.add_page("size", SizeCalculatorPage)
            # SizeCalculatorPage init(parent) -> super(parent)
            # So self.master IS the NavigationFrame
            dna_page = self.master.pages.get('dna')
            if dna_page:
                try:
                    bp = int(float(txt))
                    dna_page.set_bp_from_size_calc(bp)
                    self.master.show('dna')
                except:
                    pass
        except:
            pass
