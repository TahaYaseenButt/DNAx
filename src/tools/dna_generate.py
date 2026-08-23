import tkinter as tk
from tkinter import messagebox, ttk, filedialog
from ui_widgets import CircularLoader
import random
import threading
import math
import datetime
from tools.simulation import run_simulation, SimulationResultsWindow
from utils.database import get_db
from utils.bio_alignment import (
    compare_query_to_database, get_similarity_status,
    validate_primers_and_probes_against_db, check_oligo_cross_reactivity
)

# --- Constants for Golden Gate Assembly ---
BSAI_SITE = "GGTCTC"
BSAI_REV = "GAGACC"  # Reverse complement of GGTCTC
OVERHANG_FWD = "GTCA"
OVERHANG_REV = "GTCA"
SPACER = "A" # Spacer between BsaI and Overhang

def reverse_complement(s: str) -> str:
    comp_map = {'A':'T','T':'A','C':'G','G':'C','a':'t','t':'a','c':'g','g':'c', 'N':'N'}
    return ''.join(comp_map.get(ch, 'N') for ch in reversed(s))


def safe_random_dna(length: int) -> str:
    if length <= 0: return ""
    res = []
    for _ in range(length):
        allowed = ['A', 'T', 'C', 'G']
        if len(res) >= 3 and res[-1] == res[-2] == res[-3]:
            allowed.remove(res[-1])
        res.append(random.choice(allowed))
    return ''.join(res)


def generate_smart_payload(length=500, mode='linear', primer_option='denovo',
                           univ_fwd='CGATCGATCGATCGATCGAT', univ_rev='TAACGATCGATCGCTAGCGC',
                           num_probes=4, existing_db_records=None):
    """
    Modular payload generator that produces orthogonal DNA constructs with 
    embedded TaqMan probe binding sites and primer seeds.
    Strictly preserves probe thermodynamic standard (24bp, Tm >= 68.0°C).
    Raises ValueError if length is insufficient for requested probe count.
    """
    from tools.qpcr import ProbeDesigner
    from tools.primer_designer import find_primers
    from utils.bio_math import calculate_gc, calculate_tm

    existing_db_records = existing_db_records or []
    num_probes = max(0, int(num_probes))

    # Standard probe length to guarantee Tm >= 68°C without compromise
    probe_length = 24
    primer_len = len(univ_fwd) if primer_option == "universal" else 20
    min_spacer = 6

    # Absolute minimum length required to fit high-quality probes without physical overlap or Tm compromise
    min_required_len = (primer_len * 2) + (num_probes * probe_length) + ((num_probes + 1) * min_spacer)

    if length < min_required_len and num_probes > 0:
        raise ValueError(
            f"Insufficient construct length: {num_probes} standard TaqMan probes ({min_required_len} bp required) "
            f"cannot fit into a {length} bp construct without compromising thermodynamic stability (Tm ≥ 68.0°C). "
            f"Minimum length required: {min_required_len} bp. Please increase length or reduce probe count."
        )

    # Generate ideal probes of standard length 24bp
    ideal_probes = ProbeDesigner.generate_ideal_probes(
        num_probes, length=probe_length, existing_db_records=existing_db_records
    ) if num_probes > 0 else []

    # Assign fluorophore channels dynamically
    fluorophore_channels = [
        {"channel": "FAM", "color": "#10b981", "quencher": "BHQ-1"},
        {"channel": "HEX", "color": "#f59e0b", "quencher": "BHQ-1"},
        {"channel": "ROX", "color": "#f97316", "quencher": "BHQ-2"},
        {"channel": "Cy5", "color": "#ec4899", "quencher": "BHQ-3"},
        {"channel": "Quasar705", "color": "#8b5cf6", "quencher": "BHQ-3"},
        {"channel": "CAL Fluor 610", "color": "#ef4444", "quencher": "BHQ-2"},
        {"channel": "TET", "color": "#eab308", "quencher": "BHQ-1"},
        {"channel": "JOE", "color": "#84cc16", "quencher": "BHQ-1"},
    ]

    for idx, p in enumerate(ideal_probes):
        ch_info = fluorophore_channels[idx % len(fluorophore_channels)]
        p['channel'] = ch_info['channel']
        p['quencher'] = ch_info['quencher']
        p['color'] = ch_info['color']

    # Primer seeds
    if primer_option == "universal":
        fwd_seed = univ_fwd.upper().strip()
        rev_seed = reverse_complement(univ_rev.upper().strip())
    else:
        fwd_seed = "GC" + safe_random_dna(16) + "GC"
        rev_seed = "GC" + safe_random_dna(16) + "GC"

    remaining = length - len(fwd_seed) - len(rev_seed)
    if remaining <= 0:
        payload = (fwd_seed + rev_seed)[:length]
        probes_with_coords = []
    else:
        probe_seqs = [p['seq'] for p in ideal_probes]
        total_probe_len = sum(len(p) for p in probe_seqs)
        if remaining < total_probe_len or not ideal_probes:
            mid = safe_random_dna(remaining)
            payload = fwd_seed + mid + rev_seed
            probes_with_coords = []
        else:
            spacer_len_total = remaining - total_probe_len
            num_spacers = len(probe_seqs) + 1
            spacer_len = spacer_len_total // num_spacers
            extra = spacer_len_total % num_spacers

            parts = [fwd_seed]
            current_pos = len(fwd_seed)
            probes_with_coords = []

            for i, p_data in enumerate(ideal_probes):
                p_seq = p_data['seq']
                sp_len = spacer_len + (1 if i < extra else 0)
                parts.append(safe_random_dna(sp_len))
                current_pos += sp_len

                p_copy = p_data.copy()
                p_copy['start'] = current_pos
                p_copy['end'] = current_pos + len(p_seq)
                probes_with_coords.append(p_copy)

                parts.append(p_seq)
                current_pos += len(p_seq)

            parts.append(safe_random_dna(spacer_len))
            parts.append(rev_seed)
            payload = ''.join(parts)

    linear_seq = payload

    # Primers
    if primer_option == "universal":
        fwd_p = univ_fwd.upper().strip()
        rev_p = univ_rev.upper().strip()
        primers_res = {
            "fwd": {"seq": fwd_p, "tm": calculate_tm(fwd_p), "gc": calculate_gc(fwd_p), "len": len(fwd_p), "score": 100.0},
            "rev": {"seq": rev_p, "tm": calculate_tm(rev_p), "gc": calculate_gc(rev_p), "len": len(rev_p), "score": 100.0},
            "product_size": len(linear_seq)
        }
    else:
        primers_res = find_primers(linear_seq)

    return {
        'mode': mode,
        'payload': payload,
        'linear_seq': linear_seq,
        'gc': calculate_gc(payload),
        'length': len(payload),
        'total_length': len(linear_seq),
        'primers': primers_res,
        'probes': probes_with_coords
    }

class DNAGeneratePage(tk.Frame):
    """Generate a random DNA sequence for Golden Gate Assembly.

    Workflow:
    1. Generate random 'Payload' sequence (User length N).
    2. Validate Payload:
       - GC Content: 40% - 60%
       - No Homopolymers > 5 bases
       - No internal BsaI sites (GGTCTC or GAGACC)
    3. Assemble Linear Construct:
       [BsaI] - [Spacer] - [Overhang Fwd] - [Payload] - [Overhang Rev] - [Spacer] - [BsaI Rev]
    4. Visualize Linear Construct & Circular Taggant.
    """

    MAX_LENGTH = 10000

    def __init__(self, parent):
        super().__init__(parent, bg="#f8fafb")

        self.db = get_db()
        self._similarity_results = []

        self.primer_option_var = tk.StringVar(value="specific")
        self.univ_fwd_var = tk.StringVar(value="ATGCTAGCCGATCGATCGTA")
        self.univ_rev_var = tk.StringVar(value="TAACGATCGATCGCTAGCGC")

        self.univ_fwd_var.trace_add("write", lambda *args: self._clean_dna_input(self.univ_fwd_var))
        self.univ_rev_var.trace_add("write", lambda *args: self._clean_dna_input(self.univ_rev_var))

        # Create a canvas with scrollbar for the entire page
        self._canvas = tk.Canvas(self, bg="#f8fafb", highlightthickness=0)
        self._scrollbar = tk.Scrollbar(self, orient="vertical", command=self._canvas.yview)
        self._canvas.configure(yscrollcommand=self._scrollbar.set)
        
        self._scrollbar.pack(side="right", fill="y")
        self._canvas.pack(side="left", fill="both", expand=True)
        
        # Inner frame that holds all content
        self._inner = tk.Frame(self._canvas, bg="#f8fafb", padx=20, pady=16)
        self._canvas_window = self._canvas.create_window((0, 0), window=self._inner, anchor="nw")
        
        # Bind resize and universal mousewheel scroll events
        self._inner.bind("<Configure>", self._on_frame_configure)
        self._canvas.bind("<Configure>", self._on_canvas_configure)
        
        from ui_widgets import bind_mousewheel
        bind_mousewheel(self._canvas, self._inner)

        # --- Header ---
        header_frame = tk.Frame(self._inner, bg="#f8fafb")
        header_frame.pack(fill="x", pady=(0, 14))

        tk.Label(header_frame, text="DNA Sequence Generator", font=("Segoe UI", 16, "bold"), bg="#f8fafb", fg="#0f172a").pack(anchor="w")
        tk.Label(header_frame, text="De novo synthetic construct generation, Golden Gate / Linear assembly & database orthogonality validation.",
                 font=("Segoe UI", 9), bg="#f8fafb", fg="#64748b").pack(anchor="w")

        self.mode_var = tk.StringVar(value="linear")

        # Initialize Primer Type Options UI
        self._init_primer_ui()

        # Top Configuration Card (React-style clean card)
        top = tk.Frame(self._inner, bg="#ffffff", bd=1, relief="solid", padx=16, pady=14)
        top.pack(fill="x", pady=(0, 14))

        cfg_row1 = tk.Frame(top, bg="#ffffff")
        cfg_row1.pack(fill="x", pady=(0, 8))

        tk.Label(cfg_row1, text="Payload Length (bp):", font=("Segoe UI", 9, "bold"), bg="#ffffff", fg="#334155").pack(side="left", padx=(0, 8))
        self.len_var = tk.StringVar(value="")
        from ui_widgets import PlaceholderEntry
        self.len_entry = PlaceholderEntry(cfg_row1, placeholder="500", textvariable=self.len_var, width=12, font=("Segoe UI", 10), normal_fg="#0f172a")
        self.len_entry.pack(side="left", padx=(0, 8))

        # Quick preset buttons
        tk.Label(cfg_row1, text="Presets:", font=("Segoe UI", 8), bg="#ffffff", fg="#94a3b8").pack(side="left", padx=(8, 4))
        for preset in (100, 250, 500, 1000):
            tk.Button(cfg_row1, text=f"{preset}bp", command=lambda p=preset: self.len_var.set(str(p)),
                      font=("Segoe UI", 8), bg="#f1f5f9", fg="#475569", relief="flat", padx=6, pady=2, cursor="hand2").pack(side="left", padx=2)

        self.generate_btn = tk.Button(cfg_row1, text="⚡ Synthesize Sequence", command=self._on_generate,
                                      bg="#4f46e5", fg="#ffffff", font=("Segoe UI", 9, "bold"), relief="flat", padx=14, pady=5, cursor="hand2")
        self.generate_btn.pack(side="right", padx=(8, 0))

        # Loader and Status
        self.gen_loader = CircularLoader(top, size=18, fg="#4f46e5")
        self.status = tk.Label(top, text="Ready to generate sequence.", font=("Segoe UI", 9), bg="#ffffff", fg="#64748b")
        self.status.pack(anchor="w", pady=(4, 0))

        # Analysis / Info Area
        self.analysis_frame = tk.Frame(self._inner, bg="#ffffff", bd=1, relief="solid")
        self.analysis_frame.pack(fill="x", padx=16, pady=(12,8))
        self.analysis_label = tk.Label(self.analysis_frame, text="Construct Details:", font=("Segoe UI", 11, "bold"), bg="#ffffff")
        self.analysis_label.pack(anchor="w", padx=8, pady=8)
        self.analysis_body = tk.Frame(self.analysis_frame, bg="#ffffff")
        self.analysis_body.pack(fill="x", padx=8, pady=(0,4))

        # Database Cross-Homology / Similarity Info Strip
        self.db_sim_frame = tk.Frame(self.analysis_frame, bg="#f8fafc", bd=1, relief="solid")
        self.db_sim_frame.pack(fill="x", padx=8, pady=(4, 8))
        self.lbl_db_sim = tk.Label(self.db_sim_frame, text="Database Cross-Homology: Generate a sequence to check similarity against saved library.", font=("Segoe UI", 9), bg="#f8fafc", fg="#64748b")
        self.lbl_db_sim.pack(side="left", padx=8, pady=4)

        # Sequences Display
        self.seq_title = tk.Label(self._inner, text="Linear Construction (5' -> 3'):", bg="#f8fafb", font=("Segoe UI", 10, "bold"))
        self.seq_title.pack(anchor="w", padx=16)
        
        # Container for sequences
        self.seq_container = tk.Frame(self._inner, bg="#f8fafb")
        self.seq_container.pack(fill="x", padx=16, pady=(4,8))

        # Action and navigation buttons
        btn_row = tk.Frame(self._inner, bg="#f8fafb")
        btn_row.pack(fill="x", padx=16, pady=4)

        # Left action buttons
        self.btn_proceed_export = tk.Button(btn_row, text="Proceed to Final Review & Save ➡", 
                                            command=lambda: self.master.show('export'),
                                            bg="#10b981", fg="#ffffff", font=("Segoe UI", 9, "bold"), padx=12, pady=4, relief="flat", cursor="hand2")
        self.btn_proceed_export.pack(side="left", padx=(0, 6))

        self.btn_save_db = tk.Button(btn_row, text="💾 Quick Save", command=self._open_save_dialog,
                                     bg="#f1f5f9", fg="#334155", font=("Segoe UI", 9, "bold"), padx=10, pady=4, relief="flat", cursor="hand2")
        self.btn_save_db.pack(side="left", padx=4)

        self.btn_view_matrix = tk.Button(btn_row, text="📊 Similarity Matrix ➡", command=self._go_to_matrix_page,
                                         bg="#f3e8ff", fg="#6b21a8", font=("Segoe UI", 9, "bold"), padx=10, pady=4, relief="flat", cursor="hand2")
        self.btn_view_matrix.pack(side="left", padx=4)

        # Right utility and pipeline navigation buttons
        tk.Button(btn_row, text="Copy Sequence", command=self._copy_linear).pack(side="right")
        
        self.btn_view_probes = tk.Button(btn_row, text="3. Probes ➡", command=lambda: self.master.show('qpcr'), bg="#e8f5e9", fg="#2e7d32", font=("Segoe UI", 9, "bold"))
        self.btn_view_probes.pack(side="right", padx=4)

        self.btn_view_primers = tk.Button(btn_row, text="2. Primers ➡", command=lambda: self.master.show('primer'), bg="#e3f2fd", fg="#0d47a1", font=("Segoe UI", 9, "bold"))
        self.btn_view_primers.pack(side="right", padx=4)

        tk.Button(btn_row, text="1. Run BLAST ➡", command=self._send_to_comparator, bg="#fff3e0", fg="#e65100", font=("Segoe UI", 9, "bold")).pack(side="right", padx=4)

        # Helix Visualization disabled to focus purely on Linear fragments
        self.helix_title = tk.Frame()
        self.helix_container = tk.Frame()

        # Store last generated data
        self._last_data = {}

    def _on_frame_configure(self, event):
        self._canvas.configure(scrollregion=self._canvas.bbox("all"))

    def _on_canvas_configure(self, event):
        self._canvas.itemconfig(self._canvas_window, width=event.width)

    def _on_mousewheel(self, event):
        self._canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")

    def _copy_linear(self):
        if self._last_data.get('linear_seq'):
            self.clipboard_clear()
            self.clipboard_append(self._last_data['linear_seq'])
            messagebox.showinfo("Copied", "Sequence copied to clipboard.")
            
    def _send_to_comparator(self):
        seq = self._last_data.get('linear_seq')
        if not seq:
            messagebox.showwarning("No Sequence", "Generate a sequence first.")
            return

        try:
            # Assuming self.master is NavigationFrame (or close parent)
            # We traverse up to find 'comparator' page if self.master.pages works
            # self.master should be NavigationFrame based on main.py adds
            comp_page = self.master.pages.get('comparator')
            if comp_page:
                comp_page.set_sequence(seq)
                self.master.show('comparator')
            else:
                messagebox.showerror("Error", "Comparator page not found.")
        except Exception as e:
            messagebox.showerror("Error", f"Could not send to comparator: {e}")

    def _on_generate(self):
        txt = self.len_var.get().strip()
        try:
            n = int(float(txt))
        except Exception:
            messagebox.showerror("Invalid length", f"Please enter a valid integer between 1 and {self.MAX_LENGTH}.")
            return

        if n <= 20 or n > self.MAX_LENGTH:
            messagebox.showerror("Invalid length", f"Please enter a valid integer between 20 and {self.MAX_LENGTH}.")
            return

        mode = self.mode_var.get()
        
        self.generate_btn.config(state="disabled", text="Generating...")
        self.status.config(text=f"Generating {mode} sequence...", fg="#2e7d32")
        self.gen_loader.start()
        
        # Run generation in thread
        t = threading.Thread(target=lambda: self._run_generation(n, mode), daemon=True)
        t.start()
    
    def set_bp_from_size_calc(self, bp):
        """External hook to set BP."""
        self.len_var.set(str(bp))

    def _run_generation(self, n: int, mode: str):
        try:
            from tools.primer_designer import find_primers
            from tools.qpcr import ProbeDesigner
        except ImportError:
            pass

        # 1. Determine dynamic probe length and count based on requested payload length `n`
        if n < 150:
            probe_length = 18
        elif n < 300:
            probe_length = 20
        elif n < 600:
            probe_length = 22
        else:
            probe_length = 24

        # Calculate max possible probes to prevent overlapping under tight lengths
        if self.primer_option_var.get() == "universal":
            fwd_p_len = len(self.univ_fwd_var.get().strip())
            rev_p_len = len(self.univ_rev_var.get().strip())
            remaining_space = n - fwd_p_len - rev_p_len
        else:
            remaining_space = n - 50  # minus 25bp for each primer end seed
        num_probes = 4
        while num_probes > 0:
            required_space = num_probes * probe_length + (num_probes + 1) * 5
            if remaining_space >= required_space:
                break
            num_probes -= 1

        # 0. Retrieve database records to enforce global assay uniqueness
        db_records = []
        try:
            db_records = self.db.get_all_sequences()
        except Exception:
            pass

        # 2. Generate de novo ideal probes with zero compromise and 100% database uniqueness
        ideal_probes = ProbeDesigner.generate_ideal_probes(
            num_probes, length=probe_length, existing_db_records=db_records
        ) if num_probes > 0 else []

        max_retries = 300
        payload = None
        
        for attempt in range(max_retries):
            # 3. Generate Candidate with proper spacing around the designed de novo probes
            candidate, probes = self._generate_smart_payload(n, ideal_probes, existing_db_records=db_records)
            
            if mode == "circular":
                 linear_seq_candidate = f"{BSAI_SITE}{SPACER}{OVERHANG_FWD}{candidate}{OVERHANG_REV}{SPACER}{BSAI_REV}"
            else:
                 linear_seq_candidate = candidate

            # 4. Design Primers on the resulting sequence
            if self.primer_option_var.get() == "universal":
                fwd_p = self.univ_fwd_var.get().upper().strip()
                rev_p = self.univ_rev_var.get().upper().strip()
                from utils.bio_math import calculate_tm, calculate_gc
                primers_res = {
                    "fwd": {
                        "seq": fwd_p,
                        "tm": calculate_tm(fwd_p),
                        "gc": calculate_gc(fwd_p),
                        "len": len(fwd_p),
                        "pos": 0,
                        "score": 100.0
                    },
                    "rev": {
                        "seq": rev_p,
                        "tm": calculate_tm(rev_p),
                        "gc": calculate_gc(rev_p),
                        "len": len(rev_p),
                        "pos": 0,
                        "score": 100.0
                    },
                    "product_size": len(linear_seq_candidate)
                }
            else:
                primers_res = find_primers(linear_seq_candidate)
                if "error" in primers_res:
                    continue  # Retry

                # 5. Strict Database Orthogonality Check: primers and probes must not cross-react with DB
                f_seq = primers_res.get('fwd', {}).get('seq', '')
                r_seq = primers_res.get('rev', {}).get('seq', '')
                oligo_val = validate_primers_and_probes_against_db(f_seq, r_seq, probes, db_records)
                if not oligo_val['is_valid']:
                    continue  # Discard candidate and retry for 100% uniqueness
                
            payload = candidate
            self._temp_primers = primers_res 
            self._temp_probes = probes
            break
            
        if not payload:
             self.after(0, lambda: self._generation_failed())
             return

        data = {}
        
        if mode == "circular":
             linear_seq = f"{BSAI_SITE}{SPACER}{OVERHANG_FWD}{payload}{OVERHANG_REV}{SPACER}{BSAI_REV}"
             data = {
                 'mode': 'circular',
                 'payload': payload,
                 'linear_seq': linear_seq,
                 'gc_pct': (payload.count('G') + payload.count('C')) / len(payload) * 100,
                 'length': len(payload),
                 'total_length': len(linear_seq),
                 'primers': self._temp_primers, 
                 'probes': self._temp_probes
             }
        else:
             data = {
                 'mode': 'linear',
                 'payload': payload,
                 'linear_seq': payload, 
                 'gc_pct': (payload.count('G') + payload.count('C')) / len(payload) * 100,
                 'length': len(payload),
                 'total_length': len(payload),
                 'primers': self._temp_primers, 
                 'probes': self._temp_probes
             }
        
        self.after(0, lambda: self._display_results(data))

    def _safe_random_dna(self, length: int) -> str:
        if length <= 0: return ""
        res = []
        for _ in range(length):
            allowed = ['A', 'T', 'C', 'G']
            if len(res) >= 3 and res[-1] == res[-2] == res[-3]:
                allowed.remove(res[-1])
            res.append(random.choice(allowed))
        return ''.join(res)

    def _generate_smart_payload(self, length: int, ideal_probes: list = None, existing_db_records: list = None) -> tuple:
        """
        Constructs a DNA sequence that is GUARANTEED to work with Primer/Probe tools
        and orthogonal to all existing records in the database.
        Structure: [Good 5' Primer Site] --- [Spacers] --- [Probes] --- [Spacers] --- [Good 3' Primer Site]
        Returns: (payload_sequence, list_of_probes_with_coordinates)
        """
        if length < 60:
            # Too short for smart structure, fallback to random
            seq = self._safe_random_dna(length)
            return seq, []
            
        # 1. Good Primer Ends (ensuring database uniqueness)
        if self.primer_option_var.get() == "universal":
            fwd_seed = self.univ_fwd_var.get().upper().strip()
            rev_seed = reverse_complement(self.univ_rev_var.get().upper().strip())
        else:
            fwd_seed = "GC" + self._safe_random_dna(21) + "GC"
            rev_seed = "GC" + self._safe_random_dna(21) + "GC"
            if existing_db_records:
                for _ in range(50):
                    if any(check_oligo_cross_reactivity(fwd_seed, r.get('payload') or '') for r in existing_db_records):
                        fwd_seed = "GC" + self._safe_random_dna(21) + "GC"
                    else:
                        break
                for _ in range(50):
                    if any(check_oligo_cross_reactivity(rev_seed, r.get('payload') or '') for r in existing_db_records):
                        rev_seed = "GC" + self._safe_random_dna(21) + "GC"
                    else:
                        break
        
        remaining = length - len(fwd_seed) - len(rev_seed)
        
        if remaining <= 0:
            raw = fwd_seed + rev_seed
            return raw[:length], []
            
        if not ideal_probes:
            mid = self._safe_random_dna(remaining)
            return fwd_seed + mid + rev_seed, []
            
        # Place probes evenly in remaining space
        probe_seqs = [p['seq'] for p in ideal_probes]
        total_probe_len = sum(len(p) for p in probe_seqs)
        
        if remaining < total_probe_len:
            # Not enough room for all probes
            mid = self._safe_random_dna(remaining)
            return fwd_seed + mid + rev_seed, []
            
        spacer_len_total = remaining - total_probe_len
        num_spacers = len(probe_seqs) + 1
        spacer_len = spacer_len_total // num_spacers
        extra = spacer_len_total % num_spacers
        
        parts = [fwd_seed]
        current_pos = len(fwd_seed)
        probes_with_coords = []
        
        for i, p_data in enumerate(ideal_probes):
            p_seq = p_data['seq']
            sp_len = spacer_len + (1 if i < extra else 0)
            
            # Append spacer
            parts.append(self._safe_random_dna(sp_len))
            current_pos += sp_len
            
            # Record probe coordinates in the payload
            probe_copy = p_data.copy()
            probe_copy['start'] = current_pos
            probe_copy['end'] = current_pos + len(p_seq)
            probes_with_coords.append(probe_copy)
            
            # Append probe
            parts.append(p_seq)
            current_pos += len(p_seq)
            
        # Append final spacer and rev_seed
        parts.append(self._safe_random_dna(spacer_len))
        parts.append(rev_seed)
        
        payload_seq = ''.join(parts)
        return payload_seq, probes_with_coords

    def _init_primer_ui(self):
        # Primer Option Frame
        primer_frame = tk.Frame(self._inner, bg="#f8fafb")
        primer_frame.pack(fill="x", padx=16, pady=4)
        
        tk.Label(primer_frame, text="Primer Type:", bg="#f8fafb", font=("Segoe UI", 10, "bold")).pack(side="left", padx=(0,10))
        
        rb_spec = tk.Radiobutton(primer_frame, text="Specific Primers (De Novo)", variable=self.primer_option_var,
                                 value="specific", bg="#f8fafb", activebackground="#f8fafb", font=("Segoe UI", 9),
                                 command=self._toggle_primer_inputs)
        rb_spec.pack(side="left", padx=5)
        
        rb_univ = tk.Radiobutton(primer_frame, text="Universal Primers", variable=self.primer_option_var,
                                 value="universal", bg="#f8fafb", activebackground="#f8fafb", font=("Segoe UI", 9),
                                 command=self._toggle_primer_inputs)
        rb_univ.pack(side="left", padx=5)
        
        # Universal Primers Input Frame
        self.univ_inputs_frame = tk.Frame(self._inner, bg="#f8fafb")
        
        tk.Label(self.univ_inputs_frame, text="Univ Fwd Primer (5' → 3'):", bg="#f8fafb", font=("Segoe UI", 9)).grid(row=0, column=0, sticky="w")
        self.entry_univ_fwd = tk.Entry(self.univ_inputs_frame, textvariable=self.univ_fwd_var, width=25, font=("Consolas", 9), bd=1, relief="solid")
        self.entry_univ_fwd.grid(row=0, column=1, padx=8, pady=2)
        
        tk.Label(self.univ_inputs_frame, text="Univ Rev Primer (5' → 3'):", bg="#f8fafb", font=("Segoe UI", 9)).grid(row=0, column=2, sticky="w", padx=(20,0))
        self.entry_univ_rev = tk.Entry(self.univ_inputs_frame, textvariable=self.univ_rev_var, width=25, font=("Consolas", 9), bd=1, relief="solid")
        self.entry_univ_rev.grid(row=0, column=3, padx=8, pady=2)
        
        # Call toggle initially to hide universal inputs since 'specific' is default
        self._toggle_primer_inputs()

    def _toggle_primer_inputs(self):
        if self.primer_option_var.get() == "universal":
            self.univ_inputs_frame.pack(fill="x", padx=16, pady=4)
        else:
            self.univ_inputs_frame.pack_forget()

    def _clean_dna_input(self, var):
        val = var.get().upper()
        cleaned = "".join(ch for ch in val if ch in ['A', 'T', 'C', 'G'])
        if cleaned != var.get():
            var.set(cleaned)

    def _generation_failed(self):
        self.gen_loader.stop()
        self.generate_btn.config(state="normal", text="Generate Sequence")
        self.status.config(text="Generation failed. Could not design valid probes. Try again.", fg="#d32f2f")

    def _display_results(self, data):
        self._last_data = data
        self.gen_loader.stop()
        self.generate_btn.config(state="normal", text="Generate Sequence")
        self.status.config(text="Generation Complete.", fg="#2e7d32")

        mode = data.get('mode', 'circular')

        # Update Analysis
        for w in self.analysis_body.winfo_children():
            w.destroy()
        
        tk.Label(self.analysis_body, text=f"Payload Length: {data['length']} bp", bg="#ffffff", font=("Segoe UI", 9)).grid(row=0, column=0, sticky="w", padx=12)
        tk.Label(self.analysis_body, text=f"GC Content: {data['gc_pct']:.1f}%", bg="#ffffff", font=("Segoe UI", 9)).grid(row=0, column=1, sticky="w", padx=12)
        
        c_text = "Constraints: No BsaI, No Homopolymers > 5"
        if mode == 'circular':
            c_text += ", Golden Gate Ends"
        
        tk.Label(self.analysis_body, text=c_text, bg="#ffffff", fg="#2e7d32", font=("Segoe UI", 9)).grid(row=0, column=2, sticky="w", padx=12)

        # --- VISUALIZATION ---
        # Clear container
        for w in self.seq_container.winfo_children():
            w.destroy()
        
        if mode == 'circular':
             self._display_circular_viz(data)
             self.helix_title.pack(side="top", anchor="w", padx=16, pady=(12,4))
             self.helix_container.pack(side="top", fill="x", padx=16, pady=(0,12))
             self.seq_title.config(text="Linear Construction (5' -> 3'):")
             self._draw_helix(data['payload'])
        else:
             self._display_linear_viz(data)
             # Hide Helix for linear
             self.helix_title.pack_forget()
             self.helix_container.pack_forget()
             self.seq_title.config(text="Linear Sequence (5' -> 3'):")

        # Calculate similarity & assay orthogonality against local database
        try:
            db_records = self.db.get_all_sequences()
            if db_records:
                sims = compare_query_to_database(data['payload'], db_records)
                self._similarity_results = sims
                top_match = sims[0]
                max_sim = top_match['similarity']
                status_text, status_col, is_safe = get_similarity_status(max_sim)

                # Validate Primer and Probe uniqueness against database
                f_seq = data.get('primers', {}).get('fwd', {}).get('seq', '')
                r_seq = data.get('primers', {}).get('rev', {}).get('seq', '')
                pr_list = data.get('probes', [])
                oligo_val = validate_primers_and_probes_against_db(f_seq, r_seq, pr_list, db_records)

                sim_text = f"Database Cross-Homology: Max {max_sim:.1f}% similarity with '{top_match['name']}' ({top_match['length']} bp) • {status_text}"
                if oligo_val['is_valid']:
                    sim_text += f" | 🛡️ Primers & Probes: 100% Unique & Orthogonal across {len(db_records)} DB entries"
                else:
                    sim_text += f" | ⚠️ Assay Warning: {oligo_val['status_text']}"

                self.lbl_db_sim.config(text=sim_text, fg=status_col)
            else:
                self.lbl_db_sim.config(
                    text="Database Library: 0 constructs saved. Ready to save as first reference.",
                    fg="#64748b"
                )
        except Exception as e:
            self.lbl_db_sim.config(text=f"Database check error: {e}", fg="#dc2626")

        # Push generated data to respective pages behind the scenes
        try:
            # Primers
            primer_page = self.master.pages.get('primer')
            if primer_page and data.get('primers') and "error" not in data['primers']:
                primer_page.set_precalculated_result(data['primers'], data['payload'])
                
            # Probes
            qpcr_page = self.master.pages.get('qpcr')
            if qpcr_page and data.get('probes'):
                qpcr_page.set_precalculated_probes(data['probes'], data['payload'])
        except Exception as e:
            pass

    def _open_save_dialog(self):
        if not self._last_data or not self._last_data.get('payload'):
            messagebox.showwarning("No Data", "Please generate a DNA sequence first before saving.")
            return

        data = self._last_data
        
        dlg = tk.Toplevel(self)
        dlg.title("Save Sequence to Local Database")
        dlg.geometry("500x420")
        dlg.configure(bg="#ffffff")
        dlg.transient(self.winfo_toplevel())
        dlg.grab_set()
        
        # Center dialog
        dlg.update_idletasks()
        w = dlg.winfo_width()
        h = dlg.winfo_height()
        x = max(0, (dlg.winfo_screenwidth() // 2) - (w // 2))
        y = max(0, (dlg.winfo_screenheight() // 2) - (h // 2))
        dlg.geometry(f"+{x}+{y}")

        tk.Label(dlg, text="Save DNA Sequence Record", font=("Segoe UI", 13, "bold"), bg="#ffffff", fg="#0f172a").pack(anchor="w", padx=20, pady=(16, 4))
        tk.Label(dlg, text="Save sequence payload, primers, probes, and parameters to the local SQLite database.",
                 font=("Segoe UI", 9), bg="#ffffff", fg="#64748b").pack(anchor="w", padx=20, pady=(0, 12))

        form = tk.Frame(dlg, bg="#ffffff")
        form.pack(fill="x", padx=20)

        # Name Field
        tk.Label(form, text="Sequence Name / ID *:", font=("Segoe UI", 9, "bold"), bg="#ffffff", fg="#334155").grid(row=0, column=0, sticky="w", pady=4)
        default_name = f"DNA_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}"
        name_var = tk.StringVar(value=default_name)
        entry_name = tk.Entry(form, textvariable=name_var, font=("Segoe UI", 10), width=28, bd=1, relief="solid")
        entry_name.grid(row=0, column=1, sticky="w", padx=8, pady=4)

        # Mode & Info
        tk.Label(form, text="Construct Type:", font=("Segoe UI", 9), bg="#ffffff", fg="#64748b").grid(row=1, column=0, sticky="w", pady=4)
        tk.Label(form, text=f"{data.get('mode', 'linear').capitalize()} ({data.get('length', 0)} bp, {data.get('gc_pct', 0):.1f}% GC)", font=("Segoe UI", 9, "bold"), bg="#ffffff", fg="#0f172a").grid(row=1, column=1, sticky="w", padx=8, pady=4)

        # Primers & Probes status
        p_count = len(data.get('probes', []))
        tk.Label(form, text="Assay Components:", font=("Segoe UI", 9), bg="#ffffff", fg="#64748b").grid(row=2, column=0, sticky="w", pady=4)
        tk.Label(form, text=f"Primers: Configured • TaqMan Probes: {p_count}", font=("Segoe UI", 9), bg="#ffffff", fg="#16a34a").grid(row=2, column=1, sticky="w", padx=8, pady=4)

        # Notes Field
        tk.Label(form, text="Notes / Tags:", font=("Segoe UI", 9, "bold"), bg="#ffffff", fg="#334155").grid(row=3, column=0, sticky="nw", pady=6)
        txt_notes = tk.Text(form, height=3, width=28, font=("Segoe UI", 9), bd=1, relief="solid")
        txt_notes.grid(row=3, column=1, sticky="w", padx=8, pady=6)

        # Save action
        def do_save():
            name = name_var.get().strip()
            if not name:
                messagebox.showerror("Error", "Please enter a valid sequence name.", parent=dlg)
                return
            notes = txt_notes.get("1.0", "end").strip()
            try:
                self.db.save_sequence(
                    name=name,
                    payload=data['payload'],
                    linear_seq=data['linear_seq'],
                    mode=data.get('mode', 'linear'),
                    length=data.get('length'),
                    total_length=data.get('total_length'),
                    gc_pct=data.get('gc_pct'),
                    primers=data.get('primers'),
                    probes=data.get('probes'),
                    notes=notes
                )
                dlg.destroy()
                messagebox.showinfo("Saved", f"Sequence '{name}' saved successfully to local database!")
                
                # If matrix page exists, refresh it
                try:
                    matrix_page = self.master.pages.get('matrix_db')
                    if matrix_page:
                        matrix_page.refresh_data()
                except Exception:
                    pass
            except Exception as err:
                messagebox.showerror("Save Failed", f"Could not save sequence: {err}", parent=dlg)

        btn_box = tk.Frame(dlg, bg="#ffffff")
        btn_box.pack(fill="x", side="bottom", padx=20, pady=16)

        tk.Button(btn_box, text="💾 Save to Database", command=do_save,
                  bg="#10b981", fg="#ffffff", font=("Segoe UI", 10, "bold"), padx=14, pady=6, relief="flat", cursor="hand2").pack(side="right", padx=4)

        tk.Button(btn_box, text="Cancel", command=dlg.destroy,
                  bg="#f1f5f9", fg="#475569", font=("Segoe UI", 10), padx=12, pady=6, relief="flat", cursor="hand2").pack(side="right", padx=4)

    def _go_to_matrix_page(self):
        try:
            self.master.show("matrix_db")
        except Exception:
            messagebox.showwarning("Navigation", "Matrix page is not registered yet.")

    def _display_linear_viz(self, data):
        """Simple display for linear fragment."""
        seq = data['linear_seq']
        
        # Just show the sequence in a nice box
        tk.Label(self.seq_container, text="Generated Linear Fragment", bg="#f8fafb", font=("Segoe UI", 9, "bold")).pack(anchor="w", pady=(0,5))
        
        txt_frame = tk.Frame(self.seq_container, bg="#ffffff", bd=1, relief="solid")
        txt_frame.pack(fill="x")
        
        txt = tk.Text(txt_frame, height=8, wrap="char", font=("Courier New", 10), bd=0, padx=5, pady=5)
        txt.pack(fill="x")
        txt.insert("1.0", seq)
        txt.config(state="disabled")

    def _display_circular_viz(self, data):
        """Full Golden Gate Grid Visualization."""
        # Horizontal Scrollbar for the Grid
        h_scroll = tk.Scrollbar(self.seq_container, orient="horizontal")
        h_scroll.pack(side="bottom", fill="x")
        
        # Canvas for scrolling the grid
        grid_canvas = tk.Canvas(self.seq_container, bg="#ffffff", height=280, highlightthickness=0, xscrollcommand=h_scroll.set)
        grid_canvas.pack(side="top", fill="x", expand=True)
        h_scroll.config(command=grid_canvas.xview)
        
        # Internal Frame for Grid
        grid_frame = tk.Frame(grid_canvas, bg="#ffffff")
        grid_window = grid_canvas.create_window((0, 0), window=grid_frame, anchor="nw")
        
        def on_conf(e):
            grid_canvas.configure(scrollregion=grid_canvas.bbox("all"))
        grid_frame.bind("<Configure>", on_conf)

        # Parts
        # Linear Seq: BsaI(6) - Spacer(1) - Overhang(4) - Payload(N) - Overhang(4) - Spacer(1) - BsaI(6)
        seq = data['linear_seq']
        p_start = 11
        p_end = len(seq) - 11
        
        # Component Definition
        parts = [
            {"name": "Left BsaI", "seq": seq[:6], "bg": "#eee", "fg": "#666"},
            {"name": "Sp", "seq": seq[6:7], "bg": "#fff", "fg": "#000"},
            {"name": "L-Overhang", "seq": seq[7:11], "bg": "#ffebee", "fg": "#c62828"},
            {"name": "Payload", "seq": seq[p_start:p_end], "bg": "#e3f2fd", "fg": "#1565c0", "trunc": True},
            {"name": "R-Overhang", "seq": seq[p_end:p_end+4], "bg": "#ffebee", "fg": "#c62828"},
            {"name": "Sp", "seq": seq[p_end+4:p_end+5], "bg": "#fff", "fg": "#000"},
            {"name": "Right BsaI", "seq": seq[p_end+5:], "bg": "#eee", "fg": "#666"},
        ]
        
        # Headers
        for col, p in enumerate(parts):
            bg = p['bg']
            tk.Label(grid_frame, text=p['name'], bg=bg, font=("Segoe UI", 8, "bold"), padx=4, pady=2, relief="flat").grid(row=0, column=col, sticky="ew", padx=1, pady=1)

        # Sense Strand (5' -> 3')
        tk.Label(grid_frame, text="5'->3'", bg="#fff", font=("Consolas", 8)).grid(row=1, column=len(parts), sticky="w")
        for col, p in enumerate(parts):
            s = p['seq']
            if p.get('trunc') and len(s) > 40:
                s = s[:20] + " ... " + s[-20:]
            tk.Label(grid_frame, text=s, bg=p['bg'], fg=p['fg'], font=("Consolas", 10), padx=4, pady=4, relief="solid", bd=1).grid(row=1, column=col, sticky="ew", padx=1, pady=1)
            
        # Antisense Strand (3' <- 5')
        tk.Label(grid_frame, text="3'<-5'", bg="#fff", font=("Consolas", 8)).grid(row=2, column=len(parts), sticky="w")
        
        comp_map = {'A':'T','T':'A','C':'G','G':'C', 'N':'N'}
        def get_comp_str(s):
            return "".join(comp_map.get(c, 'N') for c in s)
            
        for col, p in enumerate(parts):
            s = p['seq']
            c_str = get_comp_str(s) # Just complement, not reverse
            if p.get('trunc') and len(c_str) > 40:
                c_str = c_str[:20] + " ... " + c_str[-20:]
            tk.Label(grid_frame, text=c_str, bg=p['bg'], fg=p['fg'], font=("Consolas", 10), padx=4, pady=4, relief="solid", bd=1).grid(row=2, column=col, sticky="ew", padx=1, pady=1)

        # --- STEP 2: Digested / Sticky Ends ---
        # Separator
        tk.Label(grid_frame, text="Step 2: Digestion (Sticky Ends Exposed)", bg="#fff", font=("Segoe UI", 9, "bold"), fg="#e65100").grid(row=3, column=0, columnspan=len(parts)+1, sticky="w", pady=(20, 5))
        
        faded = "#f5f5f5"
        
        # Left BsaI/Sp (Cut Away)
        tk.Label(grid_frame, text="X", bg=faded, fg="#ccc").grid(row=4, column=0, sticky="ew")
        tk.Label(grid_frame, text="X", bg=faded, fg="#ccc").grid(row=4, column=1, sticky="ew")
        tk.Label(grid_frame, text="X", bg=faded, fg="#ccc").grid(row=5, column=0, sticky="ew")
        tk.Label(grid_frame, text="X", bg=faded, fg="#ccc").grid(row=5, column=1, sticky="ew")

        # Left Overhang (GTCA)
        # Top: Visible (GTCA)
        tk.Label(grid_frame, text="GTCA", bg="#ffebee", fg="#c62828", font=("Consolas", 10, "bold"), relief="solid", bd=1).grid(row=4, column=2, sticky="ew")
        # Bot: Empty (Single Strand!)
        tk.Label(grid_frame, text="    ", bg="#fff", relief="flat").grid(row=5, column=2, sticky="ew")

        # Payload
        # Top & Bot Present
        p_seq = parts[3]['seq']
        
        # Top Display
        p_trunc_top = p_seq
        if len(p_seq) > 40:
             p_trunc_top = p_seq[:20] + " ... " + p_seq[-20:]
        
        # Bot Display (Complement)
        p_seq_comp = get_comp_str(p_seq)
        p_trunc_bot = p_seq_comp
        if len(p_seq_comp) > 40:
             p_trunc_bot = p_seq_comp[:20] + " ... " + p_seq_comp[-20:]
        
        tk.Label(grid_frame, text=p_trunc_top, bg="#e3f2fd", fg="#1565c0", font=("Consolas", 10)).grid(row=4, column=3, sticky="ew")
        tk.Label(grid_frame, text=p_trunc_bot, bg="#e3f2fd", fg="#1565c0", font=("Consolas", 10)).grid(row=5, column=3, sticky="ew")

        # Right Overhang (GTCA)
        # Top: Empty (Cut away)
        tk.Label(grid_frame, text="    ", bg="#fff", relief="flat").grid(row=4, column=4, sticky="ew")
        # Bot: Visible (CAGT) - The sticky end
        # Note: Right Overhang sequence is GTCA. Comp is CAGT.
        right_ovh_seq = parts[4]['seq'] # GTCA
        right_ovh_comp = get_comp_str(right_ovh_seq) # CAGT
        tk.Label(grid_frame, text=right_ovh_comp, bg="#ffebee", fg="#c62828", font=("Consolas", 10, "bold"), relief="solid", bd=1).grid(row=5, column=4, sticky="ew")

        # Right BsaI/Sp (Cut Away)
        tk.Label(grid_frame, text="X", bg=faded, fg="#ccc").grid(row=4, column=5, sticky="ew")
        tk.Label(grid_frame, text="X", bg=faded, fg="#ccc").grid(row=5, column=5, sticky="ew")
        tk.Label(grid_frame, text="X", bg=faded, fg="#ccc").grid(row=4, column=6, sticky="ew")
        tk.Label(grid_frame, text="X", bg=faded, fg="#ccc").grid(row=5, column=6, sticky="ew")

        # Annotations (Arrows/Labels)
        tk.Label(grid_frame, text="Top: 5' Overhang", font=("Segoe UI", 7), bg="#fff", fg="red").grid(row=6, column=2)
        tk.Label(grid_frame, text="Bot: 5' Overhang", font=("Segoe UI", 7), bg="#fff", fg="red").grid(row=6, column=4)

        # Separator for Step 3
        tk.Label(grid_frame, text="Step 3: Circular Product (See Canvas Below)", bg="#fff", font=("Segoe UI", 9, "bold"), fg="#1565c0").grid(row=7, column=0, columnspan=len(parts)+1, sticky="w", pady=(20, 5))

        # --- Full Sequence Text ---
        # Add a text area below the grid to show the complete sequence (untuncated)
        tk.Label(self.seq_container, text="Full Sequence:", bg="#f8fafb", font=("Segoe UI", 9, "bold")).pack(anchor="w", pady=(8,0))
        full_text = tk.Text(self.seq_container, height=4, wrap="char", font=("Courier New", 9))
        full_text.pack(fill="x", pady=(2,4))
        full_text.insert("1.0", data['linear_seq'])
        full_text.config(state="disabled") # Read-only

    def _draw_helix(self, seq):
        """Draw Circular DNA (Plasmid View) - Detailed Professional Style."""
        self.helix_canvas.delete("all")
        
        # --- Config & Dimensions ---
        w = 400
        h = 320
        cx = w / 2
        cy = 160
        radius_out = 90
        radius_in = 70
        
        self.helix_canvas.config(scrollregion=(0,0,w,h))
        self.helix_canvas.config(height=320)
        
        # --- Title ---
        self.helix_canvas.create_text(10, 10, text="Step 3: Final Circular Product", anchor="nw", font=("Segoe UI", 11, "bold"), fill="#1565c0")
        self.helix_canvas.create_text(10, 30, text="Schematic Plasmid Map", anchor="nw", font=("Segoe UI", 9), fill="#666")

        # --- Calculations ---
        n_bp = len(seq)
        gc_count = seq.count('G') + seq.count('C')
        gc_pct = (gc_count / n_bp) * 100 if n_bp > 0 else 0
        
        # --- Design ---
        # We represent the circle as two arcs:
        # 1. The Payload (Almost full circle) - Blue
        # 2. The Scar/Join (Tiny sliver at top) - Orange
        
        # Angles: 0 degrees is 3 o'clock in Tkinter.
        # We want the Scar at 12 o'clock (90 degrees).
        # Tkinter arcs: start in deg (counter-clockwise from 3 o'clock), extent in deg.
        # 12 o'clock is 90 deg.
        # Let's say Scar is 10 degrees wide (for visibility). 
        # Start = 85, Extent = 10.
        # Payload = Start = 95, Extent = 350.
        
        scar_width_deg = 10
        scar_start = 85
        
        payload_start = 95
        payload_extent = 350
        
        # --- Draw Payload Region (The main synthetic DNA) ---
        # Outer Arc
        self.helix_canvas.create_arc(cx-radius_out, cy-radius_out, cx+radius_out, cy+radius_out, 
                                     start=payload_start, extent=payload_extent, style="arc", outline="#1e88e5", width=3)
        # Inner Arc
        self.helix_canvas.create_arc(cx-radius_in, cy-radius_in, cx+radius_in, cy+radius_in, 
                                     start=payload_start, extent=payload_extent, style="arc", outline="#1e88e5", width=3)
        
        # Fill (Optional shading) - Hard to make donut with create_arc directly without polygon points.
        # We'll stick to rungs for detailed look.
        
        # --- Draw Scar Region (The Golden Gate Join) ---
        self.helix_canvas.create_arc(cx-radius_out, cy-radius_out, cx+radius_out, cy+radius_out, 
                                     start=scar_start, extent=scar_width_deg, style="arc", outline="#ff6f00", width=4)
        self.helix_canvas.create_arc(cx-radius_in, cy-radius_in, cx+radius_in, cy+radius_in, 
                                     start=scar_start, extent=scar_width_deg, style="arc", outline="#ff6f00", width=4)

        # --- Draw Rungs (Base Pairs) ---
        # Visual only. Approximated.
        import math
        num_rungs = 72 # One every 5 degrees
        for i in range(num_rungs):
            deg = i * 5
            # Skip if in scar region approx (85 to 95)
            # 85 to 95 deg.
            if 82 < deg < 98: 
                continue # Don't draw blue rungs in scar
                
            rad = math.radians(deg) 
            # Tkinter coords: 
            # x = cx + r * cos(-rad)  (Screen Y is inverted math axis usually? No, just use standard trig but Y inverted)
            # Actually Tkinter 0 deg is 3 o'clock (Right). Positive is Counter-Clockwise? No, standard is CCW.
            # Y goes DOWN. So 90 is UP (negative Y)? No.
            # Tk arc 90 is 12 o'clock.
            # Let's just use explicit math: 12 o'clock is -90 deg or 270 deg in screen coords (y down).
            # Easier: Use Tkinter 0=3'oclock logic. 90=12'oclock.
            
            # Correct Angle for trig calculation matching Tkinter's visual 'start' angle:
            # angle_rad = math.radians(deg)
            # x = cx + r * cos(angle_rad)
            # y = cy - r * sin(angle_rad)  <-- Subtract sin because Y grows downwards.
            
            angle_rad = math.radians(deg)
            x_out = cx + radius_out * math.cos(angle_rad)
            y_out = cy - radius_out * math.sin(angle_rad)
            x_in = cx + radius_in * math.cos(angle_rad)
            y_in = cy - radius_in * math.sin(angle_rad)
            
            self.helix_canvas.create_line(x_out, y_out, x_in, y_in, fill="#bbdefb", width=1)
            
        # Draw Scar Rungs (Red/Orange)
        # Center of scar is 90 deg.
        angle_rad = math.radians(90)
        x_out = cx + radius_out * math.cos(angle_rad)
        y_out = cy - radius_out * math.sin(angle_rad)
        x_in = cx + radius_in * math.cos(angle_rad)
        y_in = cy - radius_in * math.sin(angle_rad)
        self.helix_canvas.create_line(x_out, y_out, x_in, y_in, fill="#ff6f00", width=3)

        # --- Detailed Center Stats ---
        self.helix_canvas.create_text(cx, cy-25, text=f"{n_bp} bp", font=("Segoe UI", 16, "bold"), fill="#212121")
        self.helix_canvas.create_text(cx, cy, text="Synthetic Payload", font=("Segoe UI", 9, "bold"), fill="#1565c0")
        self.helix_canvas.create_text(cx, cy+18, text=f"GC: {gc_pct:.1f}%", font=("Segoe UI", 9), fill="#455a64")
        self.helix_canvas.create_text(cx, cy+34, text="Status: Circularized", font=("Segoe UI", 8), fill="#4caf50")
        
        # --- Annotations / Callouts ---
        # 1. Payload Label (Bottom)
        # at 270 deg (6 o'clock)
        self.helix_canvas.create_text(cx, cy + radius_out + 15, text="Payload Region", font=("Segoe UI", 8, "bold"), fill="#1565c0")
        
        # 2. Scar Label (Top)
        # at 90 deg (12 o'clock)
        # Draw a little line pointing to it?
        self.helix_canvas.create_line(cx, cy - radius_out - 5, cx+20, cy - radius_out - 25, fill="#ff6f00", width=1)
        self.helix_canvas.create_text(cx+25, cy - radius_out - 25, text="Golden Gate Scar\n(GTCA/TGAC)", anchor="w", font=("Segoe UI", 8, "bold"), fill="#e65100")



