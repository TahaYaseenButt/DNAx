import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import os
import datetime
from utils.database import get_db
from utils.bio_alignment import (
    needleman_wunsch, compute_similarity_matrix,
    compare_query_to_database, get_similarity_status
)
from utils.bio_math import calculate_gc, calculate_tm

class MatrixDBPage(tk.Frame):
    """
    DNA Library & Similarity Matrix Page.
    Provides local SQLite database management, pairwise similarity matrix heatmaps,
    and detailed Needleman-Wunsch sequence alignment inspections.
    """

    def __init__(self, parent):
        super().__init__(parent, bg="#f8fafb")
        self.db = get_db()
        self._current_records = []
        self._matrix_data = None
        self._selected_seq_id = None

        self._build_ui()
        self.refresh_data()

    def _build_ui(self):
        # 1. Top Header Bar
        header = tk.Frame(self, bg="#ffffff", height=64, bd=0)
        header.pack(fill="x", side="top")
        
        title_box = tk.Frame(header, bg="#ffffff")
        title_box.pack(side="left", padx=20, pady=12)

        tk.Label(title_box, text="DNA Library & Similarity Matrix", font=("Segoe UI", 16, "bold"),
                 bg="#ffffff", fg="#1e293b").pack(anchor="w")
        tk.Label(title_box, text="Local SQLite repository, bioinformatics pairwise alignment & cross-homology heatmap",
                 font=("Segoe UI", 9), bg="#ffffff", fg="#64748b").pack(anchor="w")

        # Top Action Buttons
        btn_box = tk.Frame(header, bg="#ffffff")
        btn_box.pack(side="right", padx=20, pady=14)

        tk.Button(btn_box, text="🔄 Refresh", command=self.refresh_data,
                  bg="#f1f5f9", fg="#334155", font=("Segoe UI", 9, "bold"),
                  relief="flat", padx=12, pady=5, cursor="hand2").pack(side="left", padx=4)

        tk.Button(btn_box, text="📤 Export Matrix", command=self._export_matrix,
                  bg="#0284c7", fg="#ffffff", font=("Segoe UI", 9, "bold"),
                  relief="flat", padx=12, pady=5, cursor="hand2").pack(side="left", padx=4)

        tk.Button(btn_box, text="➕ New DNA", command=self._go_to_dna_generate,
                  bg="#10b981", fg="#ffffff", font=("Segoe UI", 9, "bold"),
                  relief="flat", padx=12, pady=5, cursor="hand2").pack(side="left", padx=4)

        # 2. Stats Strip
        self.stats_strip = tk.Frame(self, bg="#ffffff", bd=1, relief="solid")
        self.stats_strip.pack(fill="x", padx=16, pady=(12, 6))
        self._build_stats_strip()

        # 3. Main Notebook (Tabs)
        self.notebook = ttk.Notebook(self)
        self.notebook.pack(fill="both", expand=True, padx=16, pady=(6, 16))

        # Style notebook
        style = ttk.Style()
        style.theme_use("clam")
        style.configure("TNotebook", background="#f8fafb", borderwidth=0)
        style.configure("TNotebook.Tab", font=("Segoe UI", 10, "bold"), padding=[16, 8], background="#e2e8f0")
        style.map("TNotebook.Tab", background=[("selected", "#ffffff")], foreground=[("selected", "#0f172a")])

        # Tabs
        self.tab_matrix = tk.Frame(self.notebook, bg="#f8fafb")
        self.tab_library = tk.Frame(self.notebook, bg="#f8fafb")
        self.tab_align = tk.Frame(self.notebook, bg="#f8fafb")

        self.notebook.add(self.tab_matrix, text="📊 Similarity Heatmap Matrix")
        self.notebook.add(self.tab_library, text="🗄 Sequence Library")
        self.notebook.add(self.tab_align, text="🔬 Pairwise Alignment Inspector")

        self._build_matrix_tab()
        self._build_library_tab()
        self._build_align_tab()

    # --- Stats Strip ---
    def _build_stats_strip(self):
        for w in self.stats_strip.winfo_children():
            w.destroy()

        self.lbl_count = tk.Label(self.stats_strip, text="Stored Constructs: 0", font=("Segoe UI", 9, "bold"), bg="#ffffff", fg="#334155")
        self.lbl_count.pack(side="left", padx=16, pady=8)

        self.lbl_avg_len = tk.Label(self.stats_strip, text="Avg Length: --", font=("Segoe UI", 9), bg="#ffffff", fg="#64748b")
        self.lbl_avg_len.pack(side="left", padx=16, pady=8)

        self.lbl_avg_gc = tk.Label(self.stats_strip, text="Avg GC: --", font=("Segoe UI", 9), bg="#ffffff", fg="#64748b")
        self.lbl_avg_gc.pack(side="left", padx=16, pady=8)

        self.lbl_sim_summary = tk.Label(self.stats_strip, text="Max Pairwise Similarity: --", font=("Segoe UI", 9), bg="#ffffff", fg="#64748b")
        self.lbl_sim_summary.pack(side="left", padx=16, pady=8)

        self.lbl_status_badge = tk.Label(self.stats_strip, text="No sequences in library", font=("Segoe UI", 9, "bold"), bg="#f1f5f9", fg="#64748b", padx=8, pady=2)
        self.lbl_status_badge.pack(side="right", padx=16, pady=6)

    # --- TAB 1: Similarity Heatmap Matrix ---
    def _build_matrix_tab(self):
        # Toolbar inside matrix tab
        m_top = tk.Frame(self.tab_matrix, bg="#f8fafb")
        m_top.pack(fill="x", padx=10, pady=8)

        tk.Label(m_top, text="Pairwise Sequence Identity (%):", font=("Segoe UI", 11, "bold"), bg="#f8fafb", fg="#1e293b").pack(side="left")
        
        # Algorithm Selector
        tk.Label(m_top, text="Method:", font=("Segoe UI", 9, "bold"), bg="#f8fafb", fg="#475569").pack(side="left", padx=(16, 4))
        self.algo_var = tk.StringVar(value="Auto (Optimal)")
        self.algo_combo = ttk.Combobox(m_top, textvariable=self.algo_var,
                                       values=["Auto (Optimal)", "Needleman-Wunsch (Exact)", "Vectorized 4-mer (Fast / 100s of DNAs)"],
                                       state="readonly", width=28)
        self.algo_combo.pack(side="left")
        self.algo_combo.bind("<<ComboboxSelected>>", lambda e: self.refresh_data())

        # Legend
        legend_frame = tk.Frame(m_top, bg="#f8fafb")
        legend_frame.pack(side="right")

        legends = [
            ("< 30% (Orthogonal)", "#dcfce7", "#15803d"),
            ("30-50% (Low)", "#e0f2fe", "#0369a1"),
            ("50-70% (Moderate)", "#fef9c3", "#a16207"),
            ("> 70% (High Clash)", "#fee2e2", "#b91c1c")
        ]
        for text, bg_c, fg_c in legends:
            box = tk.Label(legend_frame, text=text, bg=bg_c, fg=fg_c, font=("Segoe UI", 8, "bold"), padx=6, pady=2, bd=1, relief="solid")
            box.pack(side="left", padx=3)

        # Scrollable Canvas container for Matrix Grid
        matrix_container = tk.Frame(self.tab_matrix, bg="#ffffff", bd=1, relief="solid")
        matrix_container.pack(fill="both", expand=True, padx=10, pady=(0, 10))

        self.matrix_canvas = tk.Canvas(matrix_container, bg="#ffffff", highlightthickness=0)
        self.matrix_scroll_y = tk.Scrollbar(matrix_container, orient="vertical", command=self.matrix_canvas.yview)
        self.matrix_scroll_x = tk.Scrollbar(matrix_container, orient="horizontal", command=self.matrix_canvas.xview)
        
        self.matrix_canvas.configure(xscrollcommand=self.matrix_scroll_x.set, yscrollcommand=self.matrix_scroll_y.set)
        
        self.matrix_scroll_y.pack(side="right", fill="y")
        self.matrix_scroll_x.pack(side="bottom", fill="x")
        self.matrix_canvas.pack(side="left", fill="both", expand=True)

        self.matrix_inner = tk.Frame(self.matrix_canvas, bg="#ffffff")
        self.matrix_inner.bind("<Configure>", lambda e: self.matrix_canvas.configure(scrollregion=self.matrix_canvas.bbox("all")))

        from ui_widgets import bind_mousewheel
        bind_mousewheel(self.matrix_canvas, self.matrix_inner)

    def _render_matrix_grid(self):
        for w in self.matrix_inner.winfo_children():
            w.destroy()

        if not self._matrix_data or len(self._matrix_data.get('names', [])) == 0:
            tk.Label(self.matrix_inner, text="No sequences stored in the database yet.\nGenerate and save DNA sequences to view the similarity matrix.",
                     font=("Segoe UI", 11), bg="#ffffff", fg="#64748b", pady=60).pack(fill="both", expand=True)
            return

        names = self._matrix_data['names']
        matrix = self._matrix_data['matrix']
        records = self._matrix_data['records']
        n = len(names)

        # Header corner
        tk.Label(self.matrix_inner, text="Sequence", font=("Segoe UI", 9, "bold"),
                 bg="#0f172a", fg="#ffffff", padx=10, pady=8, bd=1, relief="solid", width=14).grid(row=0, column=0, sticky="nsew")

        # Column headers
        for j in range(n):
            short_name = names[j] if len(names[j]) <= 14 else names[j][:12] + '..'
            lbl = tk.Label(self.matrix_inner, text=short_name, font=("Segoe UI", 9, "bold"),
                           bg="#1e293b", fg="#f8fafc", padx=8, pady=8, bd=1, relief="solid", width=12)
            lbl.grid(row=0, column=j + 1, sticky="nsew")

        # Matrix rows
        for i in range(n):
            # Row header
            short_name = names[i] if len(names[i]) <= 14 else names[i][:12] + '..'
            r_lbl = tk.Label(self.matrix_inner, text=short_name, font=("Segoe UI", 9, "bold"),
                             bg="#334155", fg="#ffffff", padx=8, pady=6, bd=1, relief="solid", anchor="w")
            r_lbl.grid(row=i + 1, column=0, sticky="nsew")

            for j in range(n):
                val = matrix[i][j]
                
                # Determine cell colors
                if i == j:
                    bg_col = "#f1f5f9"
                    fg_col = "#64748b"
                    font_w = ("Segoe UI", 9)
                elif val < 30.0:
                    bg_col = "#dcfce7"
                    fg_col = "#166534"
                    font_w = ("Segoe UI", 9, "bold")
                elif val < 50.0:
                    bg_col = "#e0f2fe"
                    fg_col = "#075985"
                    font_w = ("Segoe UI", 9, "bold")
                elif val < 70.0:
                    bg_col = "#fef9c3"
                    fg_col = "#854d0e"
                    font_w = ("Segoe UI", 9, "bold")
                else:
                    bg_col = "#fee2e2"
                    fg_col = "#991b1b"
                    font_w = ("Segoe UI", 9, "bold")

                cell_txt = f"{val:.1f}%" if i != j else "100%"
                cell = tk.Label(self.matrix_inner, text=cell_txt, font=font_w,
                                bg=bg_col, fg=fg_col, padx=8, pady=6, bd=1, relief="solid", cursor="hand2")
                cell.grid(row=i + 1, column=j + 1, sticky="nsew")

                # Bind click to open Pairwise Alignment Inspector
                if i != j:
                    cell.bind("<Button-1>", lambda e, recA=records[i], recB=records[j]: self._inspect_alignment(recA, recB))

    # --- TAB 2: Sequence Library ---
    def _build_library_tab(self):
        # Search & Filter Bar
        bar = tk.Frame(self.tab_library, bg="#f8fafb")
        bar.pack(fill="x", padx=10, pady=8)

        tk.Label(bar, text="🔍 Search:", font=("Segoe UI", 9, "bold"), bg="#f8fafb", fg="#334155").pack(side="left")
        self.search_var = tk.StringVar()
        self.search_var.trace_add("write", lambda *args: self._on_search())
        self.search_entry = tk.Entry(bar, textvariable=self.search_var, font=("Segoe UI", 9), width=28, bd=1, relief="solid")
        self.search_entry.pack(side="left", padx=8)

        tk.Label(bar, text="Sort by:", font=("Segoe UI", 9), bg="#f8fafb", fg="#64748b").pack(side="left", padx=(16, 4))
        self.sort_var = tk.StringVar(value="Newest")
        sort_combo = ttk.Combobox(bar, textvariable=self.sort_var, values=["Newest", "Oldest", "Name (A-Z)", "Length (High-Low)", "GC% (High-Low)"], state="readonly", width=18)
        sort_combo.pack(side="left")
        sort_combo.bind("<<ComboboxSelected>>", lambda e: self._on_sort_changed())

        # Split pane: Treeview (top) and Details Drawer (bottom)
        paned = tk.PanedWindow(self.tab_library, orient="vertical", bg="#cbd5e1", sashwidth=4)
        paned.pack(fill="both", expand=True, padx=10, pady=(0, 10))

        # Top: Table of Sequences
        table_frame = tk.Frame(paned, bg="#ffffff", bd=1, relief="solid")
        paned.add(table_frame, height=220)

        columns = ("id", "name", "mode", "length", "gc_pct", "primers", "probes", "created_at")
        self.tree = ttk.Treeview(table_frame, columns=columns, show="headings", selectmode="browse")
        
        self.tree.heading("id", text="ID")
        self.tree.heading("name", text="Name")
        self.tree.heading("mode", text="Type")
        self.tree.heading("length", text="Payload Length")
        self.tree.heading("gc_pct", text="GC Content")
        self.tree.heading("primers", text="Primers")
        self.tree.heading("probes", text="TaqMan Probes")
        self.tree.heading("created_at", text="Saved On")

        self.tree.column("id", width=45, anchor="center")
        self.tree.column("name", width=160, anchor="w")
        self.tree.column("mode", width=80, anchor="center")
        self.tree.column("length", width=95, anchor="center")
        self.tree.column("gc_pct", width=85, anchor="center")
        self.tree.column("primers", width=110, anchor="center")
        self.tree.column("probes", width=110, anchor="center")
        self.tree.column("created_at", width=140, anchor="center")

        tree_scroll_y = tk.Scrollbar(table_frame, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=tree_scroll_y.set)
        tree_scroll_y.pack(side="right", fill="y")
        self.tree.pack(side="left", fill="both", expand=True)

        self.tree.bind("<<TreeviewSelect>>", self._on_tree_select)

        # Bottom: Sequence Details Drawer
        self.drawer = tk.Frame(paned, bg="#ffffff", bd=1, relief="solid", padx=16, pady=12)
        paned.add(self.drawer, height=240)
        self._build_drawer_content()

    def _build_drawer_content(self):
        for w in self.drawer.winfo_children():
            w.destroy()

        self.drawer_title = tk.Label(self.drawer, text="Select a sequence above to view parameters",
                                     font=("Segoe UI", 11, "bold"), bg="#ffffff", fg="#1e293b")
        self.drawer_title.pack(anchor="w")

        self.drawer_body = tk.Frame(self.drawer, bg="#ffffff")
        self.drawer_body.pack(fill="both", expand=True, pady=8)

        # Action Buttons in Drawer
        self.drawer_actions = tk.Frame(self.drawer, bg="#ffffff")
        self.drawer_actions.pack(fill="x", side="bottom")

    def _on_tree_select(self, event):
        selected_items = self.tree.selection()
        if not selected_items:
            return
        item = selected_items[0]
        seq_id = self.tree.item(item, "values")[0]
        rec = self.db.get_sequence_by_id(seq_id)
        if rec:
            self._render_drawer_record(rec)

    def _render_drawer_record(self, rec):
        for w in self.drawer.winfo_children():
            w.destroy()

        # Top line with title and actions
        top_line = tk.Frame(self.drawer, bg="#ffffff")
        top_line.pack(fill="x")

        tk.Label(top_line, text=f"📌 {rec['name']}", font=("Segoe UI", 12, "bold"), bg="#ffffff", fg="#0f172a").pack(side="left")
        tk.Label(top_line, text=f"({rec['mode'].capitalize()} • {rec['length']} bp • {rec['gc_pct']}% GC)",
                 font=("Segoe UI", 10), bg="#ffffff", fg="#64748b").pack(side="left", padx=8)

        btn_box = tk.Frame(top_line, bg="#ffffff")
        btn_box.pack(side="right")

        tk.Button(btn_box, text="📋 Copy Payload", command=lambda: self._copy_text(rec['payload'], "Payload copied!"),
                  bg="#f1f5f9", fg="#334155", font=("Segoe UI", 8, "bold"), padx=8, pady=3, relief="flat", cursor="hand2").pack(side="left", padx=2)

        tk.Button(btn_box, text="🔬 Compare in Inspector", command=lambda: self._send_to_align_tab(rec),
                  bg="#0284c7", fg="#ffffff", font=("Segoe UI", 8, "bold"), padx=8, pady=3, relief="flat", cursor="hand2").pack(side="left", padx=2)

        tk.Button(btn_box, text="🗑 Delete", command=lambda: self._delete_record(rec['id'], rec['name']),
                  bg="#fee2e2", fg="#b91c1c", font=("Segoe UI", 8, "bold"), padx=8, pady=3, relief="flat", cursor="hand2").pack(side="left", padx=2)

        # Content grid
        content = tk.Frame(self.drawer, bg="#ffffff")
        content.pack(fill="both", expand=True, pady=8)

        # Left Column: Sequence Text
        left_col = tk.Frame(content, bg="#ffffff")
        left_col.pack(side="left", fill="both", expand=True, padx=(0, 10))

        tk.Label(left_col, text="Payload Sequence (5' → 3'):", font=("Segoe UI", 9, "bold"), bg="#ffffff", fg="#475569").pack(anchor="w")
        txt_seq = tk.Text(left_col, height=4, font=("Consolas", 9), bg="#f8fafc", bd=1, relief="solid", wrap="char")
        txt_seq.insert("1.0", rec['payload'])
        txt_seq.config(state="disabled")
        txt_seq.pack(fill="both", expand=True, pady=4)

        if rec.get('notes'):
            tk.Label(left_col, text=f"Notes: {rec['notes']}", font=("Segoe UI", 8, "italic"), bg="#ffffff", fg="#64748b").pack(anchor="w")

        # Right Column: Primers & Probes Summary
        right_col = tk.Frame(content, bg="#ffffff", width=280)
        right_col.pack(side="right", fill="y")

        tk.Label(right_col, text="Assay Details:", font=("Segoe UI", 9, "bold"), bg="#ffffff", fg="#475569").pack(anchor="w")
        
        assay_card = tk.Frame(right_col, bg="#f8fafc", bd=1, relief="solid", padx=10, pady=8)
        assay_card.pack(fill="both", expand=True, pady=4)

        primers = rec.get('primers')
        if primers and "fwd" in primers and "rev" in primers:
            fwd = primers['fwd']
            rev = primers['rev']
            tk.Label(assay_card, text=f"Fwd Primer: {fwd.get('seq','')} (Tm: {fwd.get('tm', 0):.1f}°C)", font=("Consolas", 8), bg="#f8fafc", fg="#1e293b").pack(anchor="w")
            tk.Label(assay_card, text=f"Rev Primer: {rev.get('seq','')} (Tm: {rev.get('tm', 0):.1f}°C)", font=("Consolas", 8), bg="#f8fafc", fg="#1e293b").pack(anchor="w")
        else:
            tk.Label(assay_card, text="Primers: Not configured", font=("Segoe UI", 8), bg="#f8fafc", fg="#94a3b8").pack(anchor="w")

        probes = rec.get('probes')
        if probes and isinstance(probes, list):
            tk.Label(assay_card, text=f"TaqMan Probes: {len(probes)} designed", font=("Segoe UI", 8, "bold"), bg="#f8fafc", fg="#15803d").pack(anchor="w", pady=(4, 0))
            for idx, p in enumerate(probes[:3]):
                p_seq = p.get('seq', '')
                tk.Label(assay_card, text=f" P{idx+1}: {p_seq} (Tm: {p.get('tm',0):.1f}°C)", font=("Consolas", 8), bg="#f8fafc", fg="#334155").pack(anchor="w")
        else:
            tk.Label(assay_card, text="Probes: None stored", font=("Segoe UI", 8), bg="#f8fafc", fg="#94a3b8").pack(anchor="w")

    # --- TAB 3: Pairwise Alignment Inspector ---
    def _build_align_tab(self):
        # Controls Frame
        ctrl = tk.Frame(self.tab_align, bg="#ffffff", bd=1, relief="solid", padx=16, pady=12)
        ctrl.pack(fill="x", padx=10, pady=8)

        tk.Label(ctrl, text="Sequence A (Query):", font=("Segoe UI", 9, "bold"), bg="#ffffff", fg="#334155").grid(row=0, column=0, sticky="w", padx=4)
        self.align_combo_a = ttk.Combobox(ctrl, state="readonly", width=25)
        self.align_combo_a.grid(row=0, column=1, padx=8, pady=4)

        tk.Label(ctrl, text="Sequence B (Subject):", font=("Segoe UI", 9, "bold"), bg="#ffffff", fg="#334155").grid(row=0, column=2, sticky="w", padx=4)
        self.align_combo_b = ttk.Combobox(ctrl, state="readonly", width=25)
        self.align_combo_b.grid(row=0, column=3, padx=8, pady=4)

        tk.Button(ctrl, text="⚡ Run Global Alignment", command=self._run_manual_alignment,
                  bg="#0f172a", fg="#ffffff", font=("Segoe UI", 9, "bold"), padx=14, pady=5, relief="flat", cursor="hand2").grid(row=0, column=4, padx=16)

        # Alignment Metrics Card
        self.align_metrics_frame = tk.Frame(self.tab_align, bg="#ffffff", bd=1, relief="solid", padx=16, pady=10)
        self.align_metrics_frame.pack(fill="x", padx=10, pady=(0, 8))
        self.align_metrics_lbl = tk.Label(self.align_metrics_frame, text="Select two sequences above and click 'Run Global Alignment'.",
                                          font=("Segoe UI", 9), bg="#ffffff", fg="#64748b")
        self.align_metrics_lbl.pack(anchor="w")

        # Alignment Visual Text Box
        align_box = tk.Frame(self.tab_align, bg="#ffffff", bd=1, relief="solid")
        align_box.pack(fill="both", expand=True, padx=10, pady=(0, 10))

        tk.Label(align_box, text="Needleman-Wunsch Alignment Matrix Representation:", font=("Segoe UI", 9, "bold"),
                 bg="#ffffff", fg="#1e293b").pack(anchor="w", padx=12, pady=(8, 4))

        self.txt_align = tk.Text(align_box, font=("Consolas", 10), bg="#0f172a", fg="#38bdf8", bd=0, padx=12, pady=12, wrap="none")
        align_scroll_y = tk.Scrollbar(align_box, orient="vertical", command=self.txt_align.yview)
        align_scroll_x = tk.Scrollbar(align_box, orient="horizontal", command=self.txt_align.xview)
        self.txt_align.configure(yscrollcommand=align_scroll_y.set, xscrollcommand=align_scroll_x.set)

        align_scroll_y.pack(side="right", fill="y")
        align_scroll_x.pack(side="bottom", fill="x")
        self.txt_align.pack(side="left", fill="both", expand=True)

        # Tags for colored alignment
        self.txt_align.tag_configure("match", foreground="#4ade80")
        self.txt_align.tag_configure("mismatch", foreground="#f87171")
        self.txt_align.tag_configure("gap", foreground="#fbbf24")
        self.txt_align.tag_configure("header", foreground="#94a3b8", font=("Consolas", 9, "bold"))

    def _inspect_alignment(self, recA, recB):
        """Loads two specific records into the inspector tab and computes alignment."""
        self.notebook.select(self.tab_align)
        
        # Populate combos
        opt_a = f"{recA['id']}: {recA['name']}"
        opt_b = f"{recB['id']}: {recB['name']}"

        self.align_combo_a.set(opt_a)
        self.align_combo_b.set(opt_b)

        self._execute_alignment_display(recA, recB)

    def _send_to_align_tab(self, recA):
        self.notebook.select(self.tab_align)
        self.align_combo_a.set(f"{recA['id']}: {recA['name']}")

    def _run_manual_alignment(self):
        val_a = self.align_combo_a.get()
        val_b = self.align_combo_b.get()

        if not val_a or not val_b:
            messagebox.showwarning("Select Sequences", "Please select both Sequence A and Sequence B.")
            return

        try:
            id_a = int(val_a.split(":")[0])
            id_b = int(val_b.split(":")[0])
        except Exception:
            messagebox.showerror("Error", "Invalid sequence selection.")
            return

        recA = self.db.get_sequence_by_id(id_a)
        recB = self.db.get_sequence_by_id(id_b)

        if not recA or not recB:
            messagebox.showerror("Error", "Could not load sequence records.")
            return

        self._execute_alignment_display(recA, recB)

    def _execute_alignment_display(self, recA, recB):
        seqA = recA.get('payload') or recA.get('linear_seq', '')
        seqB = recB.get('payload') or recB.get('linear_seq', '')

        # Run Needleman-Wunsch Alignment
        res = needleman_wunsch(seqA, seqB)

        # Update metrics label
        ident = res['identity_pct']
        sim = res['similarity_pct']
        score = res['score']
        matches = res['matches']
        mismatches = res['mismatches']
        gaps = res['gaps']
        gc_delta = res['gc_delta']
        tm_delta = res['tm_delta']

        status_text, status_color, _ = get_similarity_status(ident)

        for w in self.align_metrics_frame.winfo_children():
            w.destroy()

        top_m = tk.Frame(self.align_metrics_frame, bg="#ffffff")
        top_m.pack(fill="x")

        tk.Label(top_m, text=f"Alignment: {recA['name']} vs {recB['name']}", font=("Segoe UI", 11, "bold"), bg="#ffffff", fg="#0f172a").pack(side="left")
        tk.Label(top_m, text=f"• {status_text}", font=("Segoe UI", 10, "bold"), bg="#ffffff", fg=status_color).pack(side="left", padx=10)

        stats_row = tk.Frame(self.align_metrics_frame, bg="#ffffff")
        stats_row.pack(fill="x", pady=(4, 0))

        tk.Label(stats_row, text=f"Global Identity: {ident}%", font=("Segoe UI", 9, "bold"), bg="#ffffff", fg="#0284c7").pack(side="left", padx=(0, 16))
        tk.Label(stats_row, text=f"Score: {score}", font=("Segoe UI", 9), bg="#ffffff", fg="#334155").pack(side="left", padx=8)
        tk.Label(stats_row, text=f"Matches: {matches}", font=("Segoe UI", 9), bg="#ffffff", fg="#16a34a").pack(side="left", padx=8)
        tk.Label(stats_row, text=f"Mismatches: {mismatches}", font=("Segoe UI", 9), bg="#ffffff", fg="#dc2626").pack(side="left", padx=8)
        tk.Label(stats_row, text=f"Gaps: {gaps}", font=("Segoe UI", 9), bg="#ffffff", fg="#d97706").pack(side="left", padx=8)
        tk.Label(stats_row, text=f"Δ GC: {gc_delta}%", font=("Segoe UI", 9), bg="#ffffff", fg="#64748b").pack(side="left", padx=8)
        tk.Label(stats_row, text=f"Δ Tm: {tm_delta}°C", font=("Segoe UI", 9), bg="#ffffff", fg="#64748b").pack(side="left", padx=8)

        # Render formatted multi-line alignment block (60 bases per block)
        self.txt_align.config(state="normal")
        self.txt_align.delete("1.0", "end")

        a_s1 = res['aligned_seq1']
        a_s2 = res['aligned_seq2']
        m_str = res['match_line']
        block_size = 60
        tot_len = len(a_s1)

        pos1 = 1
        pos2 = 1

        for start in range(0, tot_len, block_size):
            end = min(start + block_size, tot_len)
            sub1 = a_s1[start:end]
            sub2 = a_s2[start:end]
            sub_m = m_str[start:end]

            # Count non-gap bases in this block
            count1 = len(sub1.replace('-', ''))
            count2 = len(sub2.replace('-', ''))

            end_pos1 = pos1 + count1 - 1 if count1 > 0 else pos1
            end_pos2 = pos2 + count2 - 1 if count2 > 0 else pos2

            header_txt = f"\nRange {start+1} - {end} bp\n"
            self.txt_align.insert("end", header_txt, "header")

            # Seq A line
            self.txt_align.insert("end", f"{recA['name'][:12]:<12} {pos1:>5}  {sub1}  {end_pos1:<5}\n")
            # Match line
            self.txt_align.insert("end", f"{' ':12} {' ':>5}  {sub_m}\n", "match")
            # Seq B line
            self.txt_align.insert("end", f"{recB['name'][:12]:<12} {pos2:>5}  {sub2}  {end_pos2:<5}\n")

            pos1 += count1
            pos2 += count2

        self.txt_align.config(state="disabled")

    # --- Actions & Helpers ---
    def refresh_data(self):
        """Reloads all sequence records from the SQLite database and refreshes matrix & table."""
        records = self.db.get_all_sequences()
        self._current_records = records

        algo_choice = getattr(self, 'algo_var', None)
        algo_str = algo_choice.get() if algo_choice else "Auto (Optimal)"
        if "Needleman" in algo_str:
            method = 'exact'
        elif "Vectorized" in algo_str or "k-mer" in algo_str:
            method = 'kmer'
        else:
            method = 'auto'

        self._matrix_data = compute_similarity_matrix(records, method=method)

        # 1. Update stats strip
        count = len(records)
        self.lbl_count.config(text=f"Stored Constructs: {count}")
        if count > 0:
            avg_l = sum(r['length'] for r in records) / count
            avg_g = sum(r['gc_pct'] for r in records) / count
            self.lbl_avg_len.config(text=f"Avg Length: {avg_l:.1f} bp")
            self.lbl_avg_gc.config(text=f"Avg GC: {avg_g:.1f}%")

            max_sim = self._matrix_data.get('max_sim', 0.0)
            self.lbl_sim_summary.config(text=f"Max Pairwise Similarity: {max_sim:.1f}%")

            status_text, status_col, _ = get_similarity_status(max_sim if count > 1 else 0.0)
            method_badge = self._matrix_data.get('method_used', '')
            self.lbl_status_badge.config(text=f"{status_text} • [{method_badge}]", fg=status_col, bg="#ffffff")
        else:
            self.lbl_avg_len.config(text="Avg Length: --")
            self.lbl_avg_gc.config(text="Avg GC: --")
            self.lbl_sim_summary.config(text="Max Pairwise Similarity: --")
            self.lbl_status_badge.config(text="Library Empty", fg="#94a3b8", bg="#ffffff")

        # 2. Update matrix grid
        self._render_matrix_grid()

        # 3. Update table
        self._populate_tree(records)

        # 4. Update alignment dropdowns
        combo_values = [f"{r['id']}: {r['name']}" for r in records]
        self.align_combo_a['values'] = combo_values
        self.align_combo_b['values'] = combo_values
        if len(combo_values) >= 2:
            if not self.align_combo_a.get(): self.align_combo_a.set(combo_values[0])
            if not self.align_combo_b.get(): self.align_combo_b.set(combo_values[1])

    def _populate_tree(self, records):
        for item in self.tree.get_children():
            self.tree.delete(item)

        for r in records:
            p_status = "✅ Configured" if r.get('primers') else "—"
            pr_status = f"✅ {len(r['probes'])} probes" if r.get('probes') else "—"
            created = str(r.get('created_at', ''))[:16]
            self.tree.insert("", "end", values=(
                r['id'],
                r['name'],
                r['mode'].capitalize(),
                f"{r['length']} bp",
                f"{r['gc_pct']:.1f}%",
                p_status,
                pr_status,
                created
            ))

        if records:
            # Auto select first
            first = self.tree.get_children()[0]
            self.tree.selection_set(first)
            self._render_drawer_record(records[0])

    def _on_search(self):
        query = self.search_var.get().strip()
        if not query:
            self._populate_tree(self._current_records)
            return
        results = self.db.search_sequences(query)
        self._populate_tree(results)

    def _on_sort_changed(self):
        val = self.sort_var.get()
        order_map = {
            "Newest": "created_at DESC",
            "Oldest": "created_at ASC",
            "Name (A-Z)": "name ASC",
            "Length (High-Low)": "length DESC",
            "GC% (High-Low)": "gc_pct DESC"
        }
        order_by = order_map.get(val, "created_at DESC")
        records = self.db.get_all_sequences(order_by=order_by)
        self._populate_tree(records)

    def _delete_record(self, seq_id, name):
        if messagebox.askyesno("Confirm Delete", f"Are you sure you want to delete sequence '{name}' (ID: {seq_id})?\nThis action cannot be undone."):
            self.db.delete_sequence(seq_id)
            messagebox.showinfo("Deleted", f"Sequence '{name}' removed from database.")
            self.refresh_data()

    def _copy_text(self, text, msg):
        self.clipboard_clear()
        self.clipboard_append(text)
        messagebox.showinfo("Copied", msg)

    def _export_matrix(self):
        if not self._matrix_data or len(self._matrix_data.get('names', [])) == 0:
            messagebox.showwarning("No Data", "No sequence matrix data available to export.")
            return

        file_path = filedialog.asksaveasfilename(
            defaultextension=".csv",
            filetypes=[("CSV Spreadsheet", "*.csv"), ("All Files", "*.*")],
            title="Export Similarity Matrix"
        )
        if not file_path:
            return

        try:
            names = self._matrix_data['names']
            matrix = self._matrix_data['matrix']
            with open(file_path, 'w', encoding='utf-8') as f:
                # Header row
                f.write("," + ",".join(f'"{n}"' for n in names) + "\n")
                for i, row in enumerate(matrix):
                    f.write(f'"{names[i]}",' + ",".join(f"{val:.2f}" for val in row) + "\n")

            messagebox.showinfo("Export Successful", f"Similarity matrix exported to:\n{file_path}")
        except Exception as e:
            messagebox.showerror("Export Failed", f"Could not export matrix: {e}")

    def _go_to_dna_generate(self):
        try:
            self.master.show("dna")
        except Exception:
            pass
