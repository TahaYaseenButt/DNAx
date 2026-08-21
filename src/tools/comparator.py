import threading
import time
import re
import requests
import tkinter as tk
from tkinter import ttk, messagebox
from ui_widgets import CircularLoader

# --- Backend Logic (Kept mostly the same) ---

def run_blast_search(sequence, on_success, on_fail):
    """Submit sequence to NCBI BLAST and return (natural_hits, synthetic_hits)."""
    try:
        if not sequence or len(sequence.strip()) == 0:
            on_fail("Empty sequence")
            return

        db_name = 'nt'
        url = "https://blast.ncbi.nlm.nih.gov/Blast.cgi"
        params = {
            'CMD': 'Put', 'PROGRAM': 'blastn', 'DATABASE': db_name,
            'QUERY': sequence, 'FORMAT_TYPE': 'JSON2_S'
        }

        # Optimization for short sequences
        if len(sequence) < 30:
            params.update({'TASK': 'blastn-short', 'EXPECT': 1000, 'WORD_SIZE': 7})

        resp = requests.post(url, data=params, timeout=10)
        match = re.search(r'RID\s*=\s*([\w\d]+)', resp.text)
        if not match:
            on_fail("NCBI Busy / No RID")
            return

        rid = match.group(1)
        start_time = time.time()
        
        while True:
            if time.time() - start_time > 90: 
                on_fail("Timeout waiting for NCBI")
                return
            
            try:
                check = requests.get(url, params={'CMD': 'Get', 'RID': rid, 'FORMAT_OBJECT': 'SearchInfo', 'FORMAT_TYPE': 'Text'}, timeout=5)
                text = check.text
                if 'Status=FAILED' in text:
                    on_fail('Search Failed')
                    return
                if 'Status=READY' in text:
                    if 'ThereAreHits=yes' in text:
                        break
                    else:
                        on_success([], [])
                        return
                time.sleep(2) 
            except Exception:
                time.sleep(2)

        # Retrieve results
        res = requests.get(url, params={'CMD': 'Get', 'RID': rid, 'FORMAT_TYPE': 'JSON2_S'}, timeout=10)
        data = res.json()
        search_result = data.get('BlastOutput2', [{}])[0].get('report', {}).get('results', {}).get('search', {})
        hits = search_result.get('hits', [])

        natural_hits = []
        synthetic_hits = []
        synthetic_keywords = ["vector", "plasmid", "synthetic", "construct", "clone", "cloning", "linker", "promoter", "expression", "gfp", "rfp", "hism"]

        for hit in hits:
            hsp = hit.get('hsps', [{}])[0]
            try:
                e_val = float(hsp.get('evalue', 1.0))
            except (ValueError, TypeError):
                e_val = 1.0
                
            # Filter out non-significant random alignments
            if e_val > 0.05:
                continue
                
            desc = hit.get('description', [{}])[0]
            title = desc.get('title', '').lower()
            if any(k in title for k in synthetic_keywords):
                synthetic_hits.append(hit)
            else:
                natural_hits.append(hit)
                
            if len(synthetic_hits) + len(natural_hits) >= 15:
                break

        on_success(natural_hits, synthetic_hits)

    except Exception as e:
        on_fail(str(e))


# --- Modern UI Components ---

class ResultCard(tk.Frame):
    """A clean card to display a single BLAST hit."""
    def __init__(self, parent, idx, hit, color):
        super().__init__(parent, bg="white", bd=1, relief="solid")
        self.pack(fill="x", pady=4, padx=2)
        
        desc = hit.get('description', [{}])[0]
        title = desc.get('title', 'Unknown Sequence')
        hsp = hit.get('hsps', [{}])[0]
        
        align_len = hsp.get('align_len', 1)
        identity = hsp.get('identity', 0)
        match_pct = (identity / max(1, align_len)) * 100
        e_val = hsp.get('evalue')

        is_exact = match_pct >= 100.0
        is_predicted = "PREDICTED" in title

        # Card Border Color: Red for Exact (Warning), Green/Orange for specific types, Gray for Partial
        border_color = "#d32f2f" if is_exact else "#e0e0e0"
        if not is_exact:
            self.configure(bd=1, relief="solid", highlightbackground=border_color, highlightthickness=0)
        else:
            self.configure(bd=2, relief="solid", highlightbackground=border_color, highlightthickness=1)

        header = tk.Frame(self, bg="white")
        header.pack(fill="x", padx=5, pady=5)
        
        # Badge
        if is_exact:
            tk.Label(header, text=" EXACT MATCH ", bg="#d32f2f", fg="white", font=("Segoe UI", 8, "bold")).pack(side="right", padx=5)
        elif is_predicted:
             tk.Label(header, text=" PREDICTED ", bg="#78909c", fg="white", font=("Segoe UI", 7)).pack(side="right", padx=5)
        else:
            tk.Label(header, text=" PARTIAL ", bg="#eeeeee", fg="#666", font=("Segoe UI", 7)).pack(side="right", padx=5)
        
        tk.Label(header, text=f"{idx}. {title}", font=("Segoe UI", 9, "bold"), 
                 bg="white", anchor="w", justify="left", wraplength=300).pack(fill="x")
        
        details = tk.Frame(self, bg="white")
        details.pack(fill="x", padx=5, pady=(0, 5))
        
        # Match %
        m_color = "#d32f2f" if is_exact else color
        tk.Label(details, text=f"Match: {match_pct:.1f}%", fg=m_color, bg="white", font=("Segoe UI", 8, "bold")).pack(side="left")
        tk.Label(details, text=f" | E-Value: {e_val}", fg="#666", bg="white", font=("Segoe UI", 8)).pack(side="left")


class ResultPanel(tk.Frame):
    """Reusable panel with two columns (Natural vs Synthetic)."""
    def __init__(self, parent):
        super().__init__(parent, bg="#f0f2f5")
        
        # Uniqueness Summary Banner
        self.summary_frame = tk.Frame(self, bg="#fff", pady=8, padx=10, bd=1, relief="solid")
        self.summary_frame.pack(fill="x", padx=5, pady=(5,0))
        self.lbl_summary_icon = tk.Label(self.summary_frame, text="", font=("Segoe UI", 16), bg="#fff")
        self.lbl_summary_icon.pack(side="left", padx=(0,10))
        self.lbl_summary_title = tk.Label(self.summary_frame, text="", font=("Segoe UI", 11, "bold"), bg="#fff")
        self.lbl_summary_title.pack(anchor="w")
        self.lbl_summary_desc = tk.Label(self.summary_frame, text="", font=("Segoe UI", 9), bg="#fff", fg="#555")
        self.lbl_summary_desc.pack(anchor="w")
        
        self.panes = ttk.PanedWindow(self, orient="horizontal")
        self.panes.pack(fill="both", expand=True, padx=5, pady=5)

        self.left_frame = self._create_scrolling_col("Genomic / Natural Matches", "#2e7d32") 
        self.panes.add(self.left_frame, weight=1)

        self.right_frame = self._create_scrolling_col("Synthetic / Vector Matches", "#ef6c00") 
        self.panes.add(self.right_frame, weight=1)
        
        # Hide summary initially
        self.summary_frame.pack_forget()

    def _create_scrolling_col(self, title, color):
        container = ttk.Frame(self.panes)
        
        lbl = tk.Label(container, text=title, bg=color, fg="white", font=("Segoe UI", 10, "bold"), pady=5)
        lbl.pack(fill="x")

        canvas = tk.Canvas(container, bg="white", highlightthickness=0)
        scrollbar = ttk.Scrollbar(container, orient="vertical", command=canvas.yview)
        scrollable_frame = tk.Frame(canvas, bg="white")

        scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )

        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw", width=380)
        canvas.bind('<Configure>', lambda e: canvas.itemconfig(canvas.find_all()[0], width=e.width))

        canvas.configure(yscrollcommand=scrollbar.set)

        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        from ui_widgets import bind_mousewheel
        bind_mousewheel(canvas, scrollable_frame)

        container.inner = scrollable_frame
        return container

    def clear(self):
        for widget in self.left_frame.inner.winfo_children(): widget.destroy()
        for widget in self.right_frame.inner.winfo_children(): widget.destroy()
        self.summary_frame.pack_forget()

    def display_results(self, natural, synthetic):
        self.clear()
        
        # ANALYZE UNIQUENESS
        # We consider a match "Exact" if identity is 100%.
        all_hits = natural + synthetic
        exact_matches = []
        for hit in all_hits:
            hsp = hit.get('hsps', [{}])[0]
            align_len = hsp.get('align_len', 1)
            identity = hsp.get('identity', 0)
            if align_len > 0 and (identity / align_len) >= 1.0:
                 exact_matches.append(hit)
        
        self.summary_frame.pack(fill="x", padx=5, pady=(5,0))
        
        if not exact_matches:
            # UNIQUE
            self.summary_frame.config(bg="#e8f5e9") # Green bg
            for w in self.summary_frame.winfo_children(): w.config(bg="#e8f5e9")
            
            self.lbl_summary_icon.config(text="✅", fg="#2e7d32")
            self.lbl_summary_title.config(text="Sequence Appears Unique", fg="#2e7d32")
            self.lbl_summary_desc.config(text="No 100% exact matches found in the database. (Partial matches may exist)")
        else:
            # FOUND MATCHES
            self.summary_frame.config(bg="#ffebee") # Red bg
            for w in self.summary_frame.winfo_children(): w.config(bg="#ffebee")
            
            count = len(exact_matches)
            self.lbl_summary_icon.config(text="⚠️", fg="#c62828")
            self.lbl_summary_title.config(text=f"Exact Matches Found ({count})", fg="#c62828")
            self.lbl_summary_desc.config(text="This sequence matches existing records exactly.")
        
        if not natural:
            tk.Label(self.left_frame.inner, text="No matches found.", bg="white", fg="#999").pack(pady=10)
        for i, hit in enumerate(natural, 1):
            ResultCard(self.left_frame.inner, i, hit, "#2e7d32")

        if not synthetic:
            tk.Label(self.right_frame.inner, text="No matches found.", bg="white", fg="#999").pack(pady=10)
        for i, hit in enumerate(synthetic, 1):
            ResultCard(self.right_frame.inner, i, hit, "#ef6c00")


class ComparatorPage(tk.Frame):
    """Main UI Page."""
    def __init__(self, parent):
        super().__init__(parent, bg="#f0f2f5")
        self.pack(fill="both", expand=True)

        # -- Header --
        header = tk.Frame(self, bg="white", height=50)
        header.pack(fill="x", side="top")
        tk.Label(header, text="BLAST Comparator", font=("Segoe UI", 16, "bold"), bg="white", fg="#333").pack(side="left", padx=20, pady=10)

        nav_box = tk.Frame(header, bg="white")
        nav_box.pack(side="right", padx=15, pady=8)

        tk.Button(nav_box, text="Next: Review Primers ➡", command=lambda: self.master.show('primer'),
                  bg="#e3f2fd", fg="#0d47a1", font=("Segoe UI", 9, "bold"), padx=10, pady=4, relief="flat", cursor="hand2").pack(side="left", padx=4)

        tk.Button(nav_box, text="Proceed to Final Review & Save ➡", command=lambda: self.master.show('export'),
                  bg="#10b981", fg="white", font=("Segoe UI", 9, "bold"), padx=10, pady=4, relief="flat", cursor="hand2").pack(side="left", padx=4)

        # -- Tabs --
        self.notebook = ttk.Notebook(self)
        self.notebook.pack(fill="both", expand=True, padx=10, pady=10)

        # Tab 1: Single Sequence
        self.tab_single = tk.Frame(self.notebook, bg="#f0f2f5")
        self.notebook.add(self.tab_single, text="  Quick Scan  ")
        self._init_single_scan_ui()

    # --------------------------------------------------------------------------
    # TAB 1: Single Scan Logic
    # --------------------------------------------------------------------------
    def _init_single_scan_ui(self):
        input_frame = tk.Frame(self.tab_single, bg="white", padx=10, pady=10)
        input_frame.pack(fill="x", padx=5, pady=5)
        
        tk.Label(input_frame, text="Paste DNA Sequence:", bg="white", font=("Segoe UI", 10)).pack(anchor="w")
        self.txt_single = tk.Text(input_frame, height=5, font=("Consolas", 10), bd=1, relief="solid")
        self.txt_single.pack(fill="x", pady=5)

        btn_frame = tk.Frame(input_frame, bg="white")
        btn_frame.pack(fill="x")
        
        self.btn_single_scan = ttk.Button(btn_frame, text="Run BLAST Scan", command=self._run_single_scan)
        self.btn_single_scan.pack(side="right")

        self.single_loader = CircularLoader(btn_frame, size=18)
        self.lbl_single_status = tk.Label(btn_frame, text="Ready", bg="white", fg="gray")
        self.lbl_single_status.pack(side="left")
        
        # Design Primers Button (New)
        ttk.Button(btn_frame, text="Design Primers", command=self._send_single_to_primer_designer).pack(side="right", padx=10)

        self.results_single = ResultPanel(self.tab_single)
        self.results_single.pack(fill="both", expand=True, padx=5, pady=(0,5))
        
    def _send_single_to_primer_designer(self):
        seq = self.txt_single.get("1.0", "end").strip()
        if not seq:
            messagebox.showwarning("Empty", "Please enter a sequence first.")
            return
            
        try:
            # Navigate to Primer Designer
            primer_page = self.master.pages.get('primer')
            if primer_page:
                primer_page.set_single_sequence(seq)
                self.master.show('primer')
            else:
                messagebox.showerror("Error", "Primer page not found.")
        except Exception as e:
             messagebox.showerror("Error", f"Navigation failed: {e}")

    def _run_single_scan(self):
        seq = self.txt_single.get("1.0", "end").strip()
        if not seq:
            messagebox.showwarning("Warning", "Please enter a sequence.")
            return

        self.btn_single_scan.config(state="disabled")
        self.lbl_single_status.config(text="Searching NCBI Database... (This may take a minute)", fg="#ef6c00")
        self.results_single.clear()

        def success(nat, syn):
            self.after(0, lambda: self.results_single.display_results(nat, syn))
            self.after(0, lambda: self.lbl_single_status.config(text="Scan Complete", fg="green"))
            self.after(0, lambda: self.btn_single_scan.config(state="normal"))
            self.after(0, lambda: self.single_loader.stop())

        def fail(msg):
            self.after(0, lambda: messagebox.showerror("Error", msg))
            self.after(0, lambda: self.lbl_single_status.config(text="Error", fg="red"))
            self.after(0, lambda: self.btn_single_scan.config(state="normal"))
            self.after(0, lambda: self.single_loader.stop())

        self.single_loader.start()
        threading.Thread(target=run_blast_search, args=(seq, success, fail), daemon=True).start()

    # --------------------------------------------------------------------------
    # TAB 2: Fragments Logic (Master-Detail View)
    # --------------------------------------------------------------------------
    def _init_fragments_ui(self):
        # Top Control Bar
        ctrl_bar = tk.Frame(self.tab_fragments, bg="#e1e4e8", padx=10, pady=5)
        ctrl_bar.pack(fill="x")
        
        # Action Buttons
        self.scan_all_btn = ttk.Button(ctrl_bar, text="Scan All Fragments", command=self._scan_all_fragments)
        self.scan_all_btn.pack(side="right", padx=(5,0))
        
        # New Button: Send to Primer Designer
        self.primer_btn = ttk.Button(ctrl_bar, text="Design Primers", command=self._send_to_primer_designer)
        self.primer_btn.pack(side="right", padx=(5,5))

        # Status and Loader
        self.frag_loader = CircularLoader(ctrl_bar, size=18)
        self.lbl_frag_status = tk.Label(ctrl_bar, text="Load fragments from Generator first.", bg="#e1e4e8")
        self.lbl_frag_status.pack(side="left")

        # Split View (List | Results)
        paned = ttk.PanedWindow(self.tab_fragments, orient="horizontal")
        paned.pack(fill="both", expand=True, padx=5, pady=5)

        # -- Left: Treeview List --
        list_frame = tk.Frame(paned, bg="white", width=300)
        paned.add(list_frame, weight=1)
        
        columns = ("name", "enzymes", "status")
        self.tree = ttk.Treeview(list_frame, columns=columns, show="headings", selectmode="browse")
        self.tree.heading("name", text="Fragment Name")
        self.tree.heading("enzymes", text="Ends")
        self.tree.heading("status", text="Status")
        self.tree.column("name", width=120)
        self.tree.column("enzymes", width=100)
        self.tree.column("status", width=80)
        
        ysb = ttk.Scrollbar(list_frame, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=ysb.set)
        
        self.tree.pack(side="left", fill="both", expand=True)
        ysb.pack(side="right", fill="y")
        
        self.tree.bind("<<TreeviewSelect>>", self._on_fragment_select)

        # -- Right: Result Panel --
        detail_frame = tk.Frame(paned, bg="#f0f2f5")
        paned.add(detail_frame, weight=3)
        
        self.lbl_current_frag = tk.Label(detail_frame, text="Select a fragment to view results", 
                                         font=("Segoe UI", 12, "bold"), bg="#f0f2f5", pady=5)
        self.lbl_current_frag.pack(fill="x")
        
        self.results_frag = ResultPanel(detail_frame)
        self.results_frag.pack(fill="both", expand=True)

    def load_fragments(self, full_seq, fragments):
        """Called by external pages to populate data."""
        self.fragment_data = []
        self.fragment_results = {}
        
        # Add Full Sequence
        self.fragment_data.append({
            'id': 'full',
            'name': 'Full Construct',
            'seq': full_seq,
            'enzymes': 'N/A',
            # Store raw None for logic purposes
            'start_enzyme': None,
            'end_enzyme': None
        })

        # Add parts
        for i, frag in enumerate(fragments):
            name = f"Fragment {i+1}"
            enz = f"{frag.get('start_enzyme','')} -> {frag.get('end_enzyme','')}"
            self.fragment_data.append({
                'id': f'frag_{i}',
                'name': name,
                'seq': frag.get('seq', ''),
                'enzymes': enz,
                # Persist these so we can pass them to Primer Designer later
                'start_enzyme': frag.get('start_enzyme'),
                'end_enzyme': frag.get('end_enzyme')
            })

        self._refresh_tree()
        self.notebook.select(self.tab_fragments)
        self.lbl_frag_status.config(text=f"Loaded {len(self.fragment_data)} sequences. Ready to scan.")

    def _refresh_tree(self):
        for item in self.tree.get_children():
            self.tree.delete(item)
            
        for item in self.fragment_data:
            status = "Waiting"
            if item['id'] in self.fragment_results:
                status = "Done"
            
            self.tree.insert("", "end", iid=item['id'], values=(item['name'], item['enzymes'], status))

    def _on_fragment_select(self, event):
        selected = self.tree.selection()
        if not selected:
            return
        
        frag_id = selected[0]
        frag = next((f for f in self.fragment_data if f['id'] == frag_id), None)
        if not frag: 
            return

        self.lbl_current_frag.config(text=f"Results: {frag['name']}")
        
        if frag_id in self.fragment_results:
            nat, syn = self.fragment_results[frag_id]
            self.results_frag.display_results(nat, syn)
        else:
            self.results_frag.clear()
            btn = ttk.Button(self.results_frag.left_frame.inner, text="Scan This Fragment", 
                             command=lambda: self._scan_single_fragment_thread(frag_id))
            btn.pack(pady=20, padx=20)

    def _scan_single_fragment_thread(self, frag_id):
        self.tree.set(frag_id, "status", "Scanning...")
        frag = next((f for f in self.fragment_data if f['id'] == frag_id), None)
        try:
            self.frag_loader.start()
        except Exception:
            pass
        
        def success(nat, syn):
            self.fragment_results[frag_id] = (nat, syn)
            self.after(0, lambda: self.tree.set(frag_id, "status", "Done"))
            if self.tree.selection() and self.tree.selection()[0] == frag_id:
                self.after(0, lambda: self.results_frag.display_results(nat, syn))
            self.after(0, lambda: self.frag_loader.stop())

        def fail(msg):
            self.after(0, lambda: self.tree.set(frag_id, "status", "Error"))
            messagebox.showerror("Error", msg)
            self.after(0, lambda: self.frag_loader.stop())

        threading.Thread(target=run_blast_search, args=(frag['seq'], success, fail), daemon=True).start()

    def _scan_all_fragments(self):
        """Scans everything in the list sequentially."""
        threading.Thread(target=self._scan_all_thread, daemon=True).start()

    def _scan_all_thread(self):
        self.after(0, lambda: self.scan_all_btn.config(state='disabled'))
        try:
            self.after(0, lambda: self.frag_loader.start())
        except Exception:
            pass

        total = len(self.fragment_data)
        for i, frag in enumerate(self.fragment_data):
            fid = frag['id']
            if fid in self.fragment_results:
                continue

            self.after(0, lambda f=fid: self.tree.set(f, "status", "Scanning..."))
            self.after(0, lambda x=i: self.lbl_frag_status.config(text=f"Scanning {x+1}/{total}..."))
            
            done_event = threading.Event()
            
            def s(nat, syn):
                self.fragment_results[fid] = (nat, syn)
                self.after(0, lambda: self.tree.set(fid, "status", "Done"))
                done_event.set()
            
            def f(msg):
                self.after(0, lambda: self.tree.set(fid, "status", "Failed"))
                done_event.set()

            try:
                run_blast_search(frag['seq'], s, f)
                done_event.wait()
            except Exception:
                pass
            
            self.after(0, lambda: self._refresh_view_if_selected(fid))

        self.after(0, lambda: self.lbl_frag_status.config(text="Batch Scan Complete."))
        self.after(0, lambda: self.scan_all_btn.config(state='normal'))
        try:
            self.after(0, lambda: self.frag_loader.stop())
        except Exception:
            pass

    def _refresh_view_if_selected(self, fid):
        sel = self.tree.selection()
        if sel and sel[0] == fid:
            nat, syn = self.fragment_results.get(fid, ([], []))
            self.results_frag.display_results(nat, syn)

    # --- Communication Logic ---
    def _send_to_primer_designer(self):
        """Bundles current data and sends it to Primer Designer page."""
        if not self.fragment_data:
            messagebox.showwarning("No Data", "Please load fragments first.")
            return

        # 1. Extract Full Sequence (Item 0)
        full_seq = ""
        full_item = next((f for f in self.fragment_data if f['id'] == 'full'), None)
        if full_item:
            full_seq = full_item['seq']
        
        # 2. Extract Fragments (Items starting with 'frag_')
        fragments = []
        for item in self.fragment_data:
            if item['id'].startswith('frag_'):
                fragments.append({
                    'seq': item['seq'],
                    'start_enzyme': item.get('start_enzyme'),
                    'end_enzyme': item.get('end_enzyme')
                })

        try:
            # Assuming self.master is the NavigationFrame which holds .pages dict
            primer_page = self.master.pages.get('primer')
            if primer_page:
                primer_page.load_sequences(full_seq, fragments)
                self.master.show('primer')
            else:
                messagebox.showerror("Error", "Primer Designer page not found.")
        except Exception as e:
            messagebox.showerror("Error", f"Could not send data: {e}")

    # --- External API Hook ---
    def start_scan_with_sequences(self, full_seq: str, fragments: list):
        """Entry point for other pages."""
        try:
            self.master.show('comparator') 
        except:
            pass
        self.load_fragments(full_seq, fragments)
    
    def set_sequence(self, seq: str):
        """Set sequence for Single Scan tab."""
        self.notebook.select(self.tab_single)
        self.txt_single.delete("1.0", "end")
        self.txt_single.insert("1.0", seq)
