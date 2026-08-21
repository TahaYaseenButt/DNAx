import tkinter as tk
from tkinter import ttk
import os
from utils.database import get_db

class HomePage(tk.Frame):
    def __init__(self, parent):
        super().__init__(parent, bg="#f8fafb")
        self.db = get_db()
        self._build_ui()

    def _build_ui(self):
        # Main scrollable canvas container
        canvas = tk.Canvas(self, bg="#f8fafb", highlightthickness=0)
        scrollbar = tk.Scrollbar(self, orient="vertical", command=canvas.yview)
        canvas.configure(yscrollcommand=scrollbar.set)

        scrollbar.pack(side="right", fill="y")
        canvas.pack(side="left", fill="both", expand=True)

        content = tk.Frame(canvas, bg="#f8fafb", padx=28, pady=20)
        canvas_window = canvas.create_window((0, 0), window=content, anchor="nw")

        content.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
        canvas.bind("<Configure>", lambda e: canvas.itemconfig(canvas_window, width=e.width))

        from ui_widgets import bind_mousewheel
        bind_mousewheel(canvas, content)

        # --- 1. HERO BANNER ---
        hero = tk.Frame(content, bg="#0f172a", padx=24, pady=20, bd=0)
        hero.pack(fill="x", pady=(0, 20))

        hero_left = tk.Frame(hero, bg="#0f172a")
        hero_left.pack(side="left", fill="both", expand=True)

        tk.Label(hero_left, text="DNAₓ Laboratory Suite", font=("Segoe UI", 18, "bold"), bg="#0f172a", fg="#f8fafc").pack(anchor="w")
        tk.Label(
            hero_left,
            text="Production-grade Track & Trace DNA Assay Designer, In Silico Verification & Similarity Matrix Database",
            font=("Segoe UI", 10), bg="#0f172a", fg="#94a3b8"
        ).pack(anchor="w", pady=(4, 12))

        # Quick action buttons inside hero
        hero_btn_box = tk.Frame(hero_left, bg="#0f172a")
        hero_btn_box.pack(anchor="w")

        tk.Button(
            hero_btn_box, text="🚀 Start New Assay Workflow ➡", command=lambda: self.master.show("size"),
            font=("Segoe UI", 10, "bold"), bg="#6366f1", fg="#ffffff", activebackground="#4f46e5",
            activeforeground="#ffffff", relief="flat", padx=16, pady=8, cursor="hand2"
        ).pack(side="left", padx=(0, 10))

        tk.Button(
            hero_btn_box, text="🗄 Open DNA Matrix & DB", command=lambda: self.master.show("matrix_db"),
            font=("Segoe UI", 10, "bold"), bg="#1e293b", fg="#e2e8f0", activebackground="#334155",
            activeforeground="#ffffff", relief="flat", padx=14, pady=8, cursor="hand2"
        ).pack(side="left")

        # --- 2. PIPELINE OVERVIEW SECTION ---
        tk.Label(content, text="End-to-End Assay Design Pipeline", font=("Segoe UI", 13, "bold"), bg="#f8fafb", fg="#0f172a").pack(anchor="w", pady=(0, 10))

        # 2x3 Grid of Interactive Cards
        grid_frame = tk.Frame(content, bg="#f8fafb")
        grid_frame.pack(fill="x", pady=(0, 20))
        grid_frame.grid_columnconfigure((0, 1, 2), weight=1)

        pipeline_cards = [
            ("📏 Step 1: Size Calculator", "Calculate target construct length, molecular weight & migration distance.", "size", "#0288d1"),
            ("🧬 Step 2: DNA Generator", "Synthesize orthogonal DNA payloads with Golden Gate or Linear ends.", "dna", "#6366f1"),
            ("⚖ Step 3: BLAST Comparator", "Cross-check against NCBI BLAST to confirm zero natural homology.", "comparator", "#ea580c"),
            ("🧪 Step 4: Primer Designer", "Design optimal PCR forward & reverse primers with 3' stability.", "primer", "#059669"),
            ("📊 Step 5: qPCR Analysis", "Design 4-channel TaqMan probes (FAM, HEX, ROX, Cy5) with GC clamp.", "qpcr", "#7c3aed"),
            ("💾 Step 6: Review & Save", "Final confirmation, save verified construct to SQLite DB & export.", "export", "#10b981"),
        ]

        for i, (title, desc, page_name, accent) in enumerate(pipeline_cards):
            row = i // 3
            col = i % 3

            card = tk.Frame(grid_frame, bg="#ffffff", bd=1, relief="solid", padx=14, pady=12)
            card.grid(row=row, column=col, sticky="nsew", padx=6, pady=6)

            # Top indicator bar
            bar = tk.Frame(card, bg=accent, height=3)
            bar.pack(fill="x", pady=(0, 8))

            tk.Label(card, text=title, font=("Segoe UI", 10, "bold"), bg="#ffffff", fg="#0f172a").pack(anchor="w")
            tk.Label(card, text=desc, font=("Segoe UI", 8), bg="#ffffff", fg="#64748b", wraplength=220, justify="left").pack(anchor="w", pady=(4, 10))

            tk.Button(
                card, text="Open Tool ➡", command=lambda p=page_name: self.master.show(p),
                font=("Segoe UI", 8, "bold"), bg="#f1f5f9", fg="#334155", activebackground="#e2e8f0",
                relief="flat", padx=8, pady=3, cursor="hand2"
            ).pack(anchor="e")

        # --- 3. DATABASE & ASSAY STATS SECTION ---
        bottom_frame = tk.Frame(content, bg="#ffffff", bd=1, relief="solid", padx=16, pady=14)
        bottom_frame.pack(fill="x")

        tk.Label(bottom_frame, text="Local Database & Matrix Status", font=("Segoe UI", 11, "bold"), bg="#ffffff", fg="#0f172a").pack(anchor="w")

        try:
            count = self.db.count_sequences()
            status_desc = f"Currently managing {count} verified DNA construct(s) in local SQLite repository with instant pairwise similarity alignment."
        except Exception:
            status_desc = "Local SQLite repository active."

        tk.Label(bottom_frame, text=status_desc, font=("Segoe UI", 9), bg="#ffffff", fg="#64748b").pack(anchor="w", pady=(2, 8))

        btn_row = tk.Frame(bottom_frame, bg="#ffffff")
        btn_row.pack(anchor="w")

        tk.Button(
            btn_row, text="📊 View Pairwise Similarity Matrix", command=lambda: self.master.show("matrix_db"),
            font=("Segoe UI", 9, "bold"), bg="#f3e8ff", fg="#6b21a8", relief="flat", padx=12, pady=5, cursor="hand2"
        ).pack(side="left", padx=(0, 8))

        tk.Button(
            btn_row, text="📄 View Laboratory Protocols", command=lambda: self.master.show("protocol"),
            font=("Segoe UI", 9, "bold"), bg="#f1f5f9", fg="#475569", relief="flat", padx=12, pady=5, cursor="hand2"
        ).pack(side="left")
