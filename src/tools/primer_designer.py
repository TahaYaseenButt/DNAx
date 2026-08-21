import sys
import os
# Adjust sys.path to support running directly as a standalone script
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import tkinter as tk
from tkinter import ttk, messagebox
import threading
from utils.bio_math import (
    get_rev_complement, calculate_tm, calculate_gc, 
    has_nucleotide_runs, check_hairpin, check_self_dimer
)

# --- Restriction Enzyme Data ---
# Format: { "EnzymeName": ("RecognitionSite", "StickyEndTail"), ... }
# The recognition site is the sequence the enzyme cuts.
# The sticky end tail is used when designing primers with enzyme overhangs.

RESTRICTION_DATA = {
    "None": ("", ""),
    # Type IIS Enzymes
    "BsaI":     ("GGTCTC", "GGTCTC"),
    "Bsa1":     ("GGTCTC", "GGTCTC"), # Alias for user convenience
}

# --- Backend Logic: PCR Primer Design ---

def check_3prime_stability(seq):
    """
    Check 3' end stability for PCR.
    - Should end in G or C (GC clamp) but not more than 3 G/C in last 5 bases
    - Avoid ending in T (weak binding)
    Returns score: higher is better (0-10 scale)
    """
    seq = seq.upper()
    last_5 = seq[-5:]
    last_base = seq[-1]
    
    score = 5  # baseline
    
    # GC clamp bonus
    if last_base in ['G', 'C']:
        score += 2
    elif last_base == 'T':
        score -= 2  # T at 3' end is weak
    
    # Count G/C in last 5 bases
    gc_count = last_5.count('G') + last_5.count('C')
    if gc_count >= 4:
        score -= 2  # Too stable, might cause mispriming
    elif gc_count <= 1:
        score -= 1  # Too weak
    
    return max(0, min(10, score))

def check_primer_dimer(fwd_seq, rev_seq, min_complementary=4):
    """
    Check if forward and reverse primers can form dimers with each other.
    Critical for PCR efficiency.
    """
    fwd = fwd_seq.upper()
    rev = rev_seq.upper()
    rev_rc = get_rev_complement(rev)
    
    # Check if 3' ends are complementary (most problematic)
    fwd_3prime = fwd[-6:]
    rev_3prime = rev[-6:]
    
    if fwd_3prime in get_rev_complement(rev):
        return True
    if rev_3prime in get_rev_complement(fwd):
        return True
    
    # General complementarity check
    for i in range(len(fwd) - min_complementary + 1):
        segment = fwd[i:i + min_complementary]
        if segment in rev_rc:
            return True
    return False

def score_primer(seq, target_tm=60.0):
    """
    Score a primer candidate for PCR suitability (higher is better).
    Considers: Tm, GC%, 3' stability, runs, hairpins, self-dimers.
    """
    seq = seq.upper()
    tm = calculate_tm(seq)
    gc = calculate_gc(seq)
    
    score = 100  # Start with perfect score
    
    # Tm penalty (want close to target)
    tm_diff = abs(tm - target_tm)
    score -= tm_diff * 2
    
    # GC content penalty (want 40-60%)
    if gc < 40:
        score -= (40 - gc) * 0.5
    elif gc > 60:
        score -= (gc - 60) * 0.5
    
    # Nucleotide runs penalty
    if has_nucleotide_runs(seq, 4):
        score -= 15
    if has_nucleotide_runs(seq, 3):
        score -= 5
    
    # Hairpin penalty
    if check_hairpin(seq):
        score -= 20
    
    # Self-dimer penalty
    if check_self_dimer(seq):
        score -= 15
    
    # 3' stability bonus/penalty
    stability = check_3prime_stability(seq)
    score += (stability - 5) * 2  # centered around 5
    
    # Length preference (20-22 is ideal for standard PCR)
    length = len(seq)
    if 20 <= length <= 22:
        score += 3
    
    return score

def find_primers(sequence, min_len=18, max_len=25, target_tm=60.0):
    """
    Design optimal PCR primer pair for amplification.
    
    Features:
    - Forward primer from 5' end region
    - Reverse primer from 3' end region (reverse complement)
    - Tm matching between primers (within 5°C)
    - GC content 40-60%
    - Avoids hairpins, self-dimers, and primer-dimers
    - Checks 3' end stability
    - Avoids nucleotide runs
    
    Returns dict with 'fwd', 'rev', and 'product_size'.
    """
    seq = sequence.upper().strip()
    if len(seq) < 20:
        return {"error": "Sequence too short for PCR (min 20bp required)."}

    # --- 1. Find Forward Primer Candidates (Must start at 0 for full length) ---
    fwd_candidates = []
    # If we want full length, we MUST start near 0. 
    # To be safe, let's allow a tiny wiggle room (0-5bp) but prioritize 0 for exact end.
    # User Request: "end product to be of the same bp". So it MUST start at 0.
    search_region_fwd = seq[0:30] # Limit search to just the start to force 5' binding

    for length in range(min_len, max_len + 1):
        if length > len(search_region_fwd): continue
        
        # Only check the candidate starting exactly at 0 to guarantee 5' end inclusion
        # Or very close if GC is terrible? No, user wants SAME bp. So must be 0.
        candidate = seq[0:length]
        
        tm = calculate_tm(candidate)
        gc = calculate_gc(candidate)
        
        # We might need to relax constraints if the user forced a specific sequence
        # Relaxed checks for mandatory positions
        primer_score = score_primer(candidate, target_tm)
        fwd_candidates.append({
            'seq': candidate,
            'tm': round(tm, 1),
            'gc': round(gc, 1),
            'len': length,
            'pos': 0,
            'score': primer_score
        })

    # --- 2. Find Reverse Primer Candidates (Must end at strict 3' end) ---
    rev_candidates = []
    # We want the primer to align with the very end of the sequence.
    # Reverse primer binds to the sense strand.
    # The read (seq) is 5'->3'.
    # Rev primer is 5'->3' complement of the end.
    # It must bind to the last 'length' bases of the seq.
    
    seq_len = len(seq)
    
    for length in range(min_len, max_len + 1):
        # Candidate is the end snippet
        # e.g. if seq is 100bp, and len is 20.
        # We want bases 80-100.
        start_idx = seq_len - length
        if start_idx < 0: continue
        
        subseq = seq[start_idx:] # The target binding site on Sense strand
        candidate_rc = get_rev_complement(subseq) # The actual primer sequence
        
        tm = calculate_tm(candidate_rc)
        gc = calculate_gc(candidate_rc)
        
        primer_score = score_primer(candidate_rc, target_tm)
        rev_candidates.append({
            'seq': candidate_rc,
            'bind_seq': subseq,
            'tm': round(tm, 1),
            'gc': round(gc, 1),
            'len': length,
            'pos': start_idx,
            'score': primer_score
        })

    if not fwd_candidates:
        return {"error": "Could not design Forward primer at 5' end. Sequence might be too GC-rich/poor at the start."}
    if not rev_candidates:
        return {"error": "Could not design Reverse primer at 3' end. Sequence might be too GC-rich/poor at the end."}

    # --- 3. Find Best Primer Pair (Tm matching + no primer-dimer) ---
    best_pair = None
    best_pair_score = -999

    # Sort by score descending
    fwd_candidates.sort(key=lambda x: x['score'], reverse=True)
    rev_candidates.sort(key=lambda x: x['score'], reverse=True)

    # Check top candidates for compatibility
    for fwd in fwd_candidates[:20]:  # top 20
        for rev in rev_candidates[:20]:
            # Tm difference (should be < 5°C for PCR)
            tm_diff = abs(fwd['tm'] - rev['tm'])
            if tm_diff > 5:
                continue
            
            # Check for primer-dimer formation
            if check_primer_dimer(fwd['seq'], rev['seq']):
                continue
            
            # Calculate product size
            product_size = (rev['pos'] + rev['len']) - fwd['pos']
            if product_size < 20:
                continue
            
            # Combined score
            pair_score = fwd['score'] + rev['score'] - tm_diff * 2
            
            if pair_score > best_pair_score:
                best_pair_score = pair_score
                best_pair = (fwd, rev, product_size)

    if not best_pair:
        return {"error": "Could not find compatible primer pair. Primers may form dimers or have mismatched Tm."}

    fwd, rev, product_size = best_pair

    return {
        "success": True,
        "fwd": fwd,
        "rev": rev,
        "product_size": product_size,
        "tm_difference": abs(fwd['tm'] - rev['tm'])
    }


def find_primers_for_cloning(sequence, start_enzyme=None, end_enzyme=None, clamp='GCGC'):
    """
    Design PCR primers for cloning with restriction enzyme overhangs.
    
    This produces primers that:
    1. Have a 5' clamp sequence (typically 4-6 bases for efficient cutting)
    2. Include the restriction enzyme recognition site
    3. Anneal to the target sequence (the actual primer part)
    
    After PCR amplification and restriction digestion, the fragments will have
    compatible sticky ends for ligation into a circular plasmid.
    
    Args:
        sequence: The DNA fragment to amplify
        start_enzyme: Enzyme name for forward primer (5' end)
        end_enzyme: Enzyme name for reverse primer (3' end)  
        clamp: Extra bases before enzyme site for efficient cutting
    
    Returns:
        Dict with 'fwd', 'rev', primer details including full sequence with tails
    """
    # First, find basic primers without tails
    result = find_primers(sequence)
    
    if "error" in result:
        return result
    
    # Get enzyme recognition sites
    fwd_enzyme_site = ""
    rev_enzyme_site = ""
    
    if start_enzyme and start_enzyme != 'None':
        fwd_enzyme_site = RESTRICTION_DATA.get(start_enzyme, ("", ""))[0]
    
    if end_enzyme and end_enzyme != 'None':
        rev_enzyme_site = RESTRICTION_DATA.get(end_enzyme, ("", ""))[0]
    
    # Build full primers with tails
    fwd_core = result['fwd']['seq']
    rev_core = result['rev']['seq']
    
    # Forward primer: 5'-[clamp]-[enzyme site]-[annealing region]-3'
    fwd_full = clamp + fwd_enzyme_site + fwd_core
    
    # Reverse primer: 5'-[clamp]-[enzyme site]-[annealing region]-3'
    rev_full = clamp + rev_enzyme_site + rev_core
    
    # Calculate Tm for annealing region only (this is what matters for PCR)
    fwd_annealing_tm = result['fwd']['tm']
    rev_annealing_tm = result['rev']['tm']
    
    # Update result with full primers
    fwd_data = result['fwd'].copy()
    fwd_data['core_seq'] = fwd_core
    fwd_data['full_seq'] = fwd_full
    fwd_data['enzyme'] = start_enzyme or 'None'
    fwd_data['enzyme_site'] = fwd_enzyme_site
    fwd_data['clamp'] = clamp
    fwd_data['total_len'] = len(fwd_full)
    
    rev_data = result['rev'].copy()
    rev_data['core_seq'] = rev_core
    rev_data['full_seq'] = rev_full
    rev_data['enzyme'] = end_enzyme or 'None'
    rev_data['enzyme_site'] = rev_enzyme_site
    rev_data['clamp'] = clamp
    rev_data['total_len'] = len(rev_full)
    
    # Product size after digestion (original product minus the tails that get cut)
    # The PCR product includes the tails, but after digestion you get sticky ends
    pcr_product_size = result['product_size'] + len(clamp + fwd_enzyme_site) + len(clamp + rev_enzyme_site)
    digested_product_size = result['product_size']  # After cutting off the overhangs
    
    return {
        "success": True,
        "is_cloning": True,
        "fwd": fwd_data,
        "rev": rev_data,
        "product_size": result['product_size'],
        "pcr_product_size": pcr_product_size,
        "tm_difference": result['tm_difference'],
        "start_enzyme": start_enzyme,
        "end_enzyme": end_enzyme
    }


# --- UI Components ---

class PrimerResultCard(tk.Frame):
    """Displays Fwd/Rev primer details nicely, including cloning tails if present."""
    def __init__(self, parent, title, data, color):
        super().__init__(parent, bg="white", bd=1, relief="solid")
        self.pack(fill="x", pady=5, padx=5)

        header = tk.Frame(self, bg=color, height=25)
        header.pack(fill="x")
        tk.Label(header, text=title, bg=color, fg="white", font=("Segoe UI", 9, "bold")).pack(side="left", padx=5)
        
        # Show enzyme if cloning primer
        # Show enzyme if cloning primer
        if data.get('enzyme') and data.get('enzyme') != 'None':
            tk.Label(header, text=f"[Enzyme: {data['enzyme']}]", bg=color, fg="#ffffff", font=("Segoe UI", 9)).pack(side="right", padx=5)

        content = tk.Frame(self, bg="white", padx=10, pady=10)
        content.pack(fill="x")

        # Check if this is a cloning primer with tails
        is_cloning = 'full_seq' in data
        
        if is_cloning:
            # Show full primer with color-coded regions
            full_frame = tk.Frame(content, bg="white")
            full_frame.pack(fill="x", pady=(0, 5))
            
            tk.Label(full_frame, text="Full Primer (order this):", bg="white", fg="#666", font=("Segoe UI", 8)).pack(anchor="w")
            
            seq_frame = tk.Frame(full_frame, bg="#f4f4f4", relief="flat", padx=5, pady=2)
            seq_frame.pack(fill="x", pady=2)
            
            # Clamp (gray)
            clamp = data.get('clamp', '')
            if clamp:
                tk.Label(seq_frame, text=clamp, font=("Consolas", 11), bg="#f4f4f4", fg="#999").pack(side="left")
            
            # Enzyme site (green)
            enzyme_site = data.get('enzyme_site', '')
            if enzyme_site:
                tk.Label(seq_frame, text=enzyme_site, font=("Consolas", 11, "bold"), bg="#f4f4f4", fg="#388e3c").pack(side="left")
            
            # Core annealing region (black/bold)
            core = data.get('core_seq', data['seq'])
            tk.Label(seq_frame, text=core, font=("Consolas", 11, "bold"), bg="#f4f4f4", fg="#333").pack(side="left")
            
            # Copy button for full sequence
            btn_copy = tk.Button(seq_frame, text="Copy", font=("Segoe UI", 8), bg="white", bd=1,
                                 command=lambda: self._copy_to_clipboard(data['full_seq']))
            btn_copy.pack(side="right", padx=5)
            
            # Legend
            legend_frame = tk.Frame(content, bg="white")
            legend_frame.pack(fill="x", pady=(0, 5))
            tk.Label(legend_frame, text="Parts:", bg="white", fg="#666", font=("Segoe UI", 9, "bold")).pack(side="left")
            tk.Label(legend_frame, text="[clamp]", bg="white", fg="#999", font=("Segoe UI", 9)).pack(side="left", padx=(5,0))
            tk.Label(legend_frame, text="[enzyme site]", bg="white", fg="#388e3c", font=("Segoe UI", 9)).pack(side="left", padx=(5,0))
            tk.Label(legend_frame, text="[binding part]", bg="white", fg="#333", font=("Segoe UI", 9, "bold")).pack(side="left", padx=(5,0))

            
            # Stats for full primer
            total_len = data.get('total_len', len(data.get('full_seq', data['seq'])))
            stats = f"Primer Length: {total_len} bp (Order this one)"

        else:
            # Standard primer display (no cloning tails)
            seq_frame = tk.Frame(content, bg="white")
            seq_frame.pack(fill="x", pady=(0, 5))
            
            lbl_seq = tk.Label(seq_frame, text=data['seq'], font=("Consolas", 11, "bold"), bg="#f4f4f4", fg="#333", padx=5, pady=2, relief="flat")
            lbl_seq.pack(side="left", fill="x", expand=True)

            btn_copy = tk.Button(seq_frame, text="Copy", font=("Segoe UI", 8), bg="white", bd=1,
                                 command=lambda: self._copy_to_clipboard(data['seq']))
            btn_copy.pack(side="left", padx=5)

            # Stats - include score if available
            score_text = f"  |  Score: {data['score']:.0f}" if 'score' in data else ""
            stats = f"Primer Length: {data['len']} bp (Order this one)"

        
        tk.Label(content, text=stats, bg="white", fg="#666", font=("Segoe UI", 9)).pack(anchor="w")

    def _copy_to_clipboard(self, text):
        self.clipboard_clear()
        self.clipboard_append(text)
        self.update() # Keep clipboard after app close (optional)
        messagebox.showinfo("Copied", "Sequence copied to clipboard!", parent=self)

class PrimerDesignPanel(tk.Frame):
    """Reusable panel for displaying results."""
    def __init__(self, parent):
        super().__init__(parent, bg="#f0f2f5")
        
        self.scroll_frame = tk.Canvas(self, bg="#f0f2f5", highlightthickness=0)
        self.scrollbar = ttk.Scrollbar(self, orient="vertical", command=self.scroll_frame.yview)
        self.inner = tk.Frame(self.scroll_frame, bg="#f0f2f5")

        self.inner.bind("<Configure>", lambda e: self.scroll_frame.configure(scrollregion=self.scroll_frame.bbox("all")))
        self.scroll_frame.create_window((0, 0), window=self.inner, anchor="nw", width=500)
        self.scroll_frame.bind('<Configure>', lambda e: self.scroll_frame.itemconfig(self.scroll_frame.find_all()[0], width=e.width))

        self.scroll_frame.pack(side="left", fill="both", expand=True, padx=10, pady=10)
        self.scrollbar.pack(side="right", fill="y")

        from ui_widgets import bind_mousewheel
        bind_mousewheel(self.scroll_frame, self.inner)

    def display_result(self, res):
        # Clear previous
        for w in self.inner.winfo_children(): w.destroy()

        if "error" in res:
            tk.Label(self.inner, text=res['error'], fg="red", bg="#f0f2f5", font=("Segoe UI", 10)).pack(pady=20)
            return

        # Summary Header
        summary_frame = tk.Frame(self.inner, bg="white", bd=1, relief="solid")
        summary_frame.pack(fill="x", padx=5, pady=5)
        
        # Check if this is a cloning primer result
        is_cloning = res.get('is_cloning', False)
        header_text = "✓ Cloning PCR Primers Designed" if is_cloning else "✓ PCR Primer Pair Designed"
        
        tk.Label(summary_frame, text=header_text, font=("Segoe UI", 12, "bold"), fg="#2e7d32", bg="white").pack(pady=(10,5))
        
        # Product info row
        info_frame = tk.Frame(summary_frame, bg="white")
        info_frame.pack(fill="x", padx=10, pady=(0, 10))
        
        if is_cloning:
            # Highlight the final product size dramatically
            tk.Label(info_frame, text=f"Final Result Size (PCR Product): {res.get('pcr_product_size', res['product_size'])} bp", 
                     font=("Segoe UI", 12, "bold"), bg="white", fg="#1565c0").pack(side="left", padx=10)
            
            # Subtle info about fragment
            tk.Label(info_frame, text=f"(Fragment starts as {res['product_size']} bp, primers add tails)", 
                     font=("Segoe UI", 9), bg="white", fg="#777").pack(side="left", padx=10)

        else:
            tk.Label(info_frame, text=f"Product Size: {res['product_size']} bp", font=("Segoe UI", 10), bg="white").pack(side="left", padx=10)
        
        # Tm difference indicator
        tm_diff = res.get('tm_difference', 0)
        tm_color = "#2e7d32" if tm_diff <= 2 else ("#ff9800" if tm_diff <= 4 else "#d32f2f")
        tk.Label(info_frame, text=f"ΔTm: {tm_diff:.1f}°C", font=("Segoe UI", 10), bg="white", fg=tm_color).pack(side="left", padx=10)

        # Cloning info banner
        if is_cloning:
            cloning_frame = tk.Frame(summary_frame, bg="#fff3e0")
            cloning_frame.pack(fill="x", padx=10, pady=(0, 10))
            
            enzymes_info = f"5' end: {res.get('start_enzyme', 'N/A')}  →  Fragment  →  {res.get('end_enzyme', 'N/A')} :3' end"
            tk.Label(cloning_frame, text="Restriction Sites:", bg="#fff3e0", fg="#e65100", font=("Segoe UI", 9, "bold")).pack(anchor="w", padx=5, pady=(5, 0))
            tk.Label(cloning_frame, text=enzymes_info, bg="#fff3e0", fg="#bf360c", font=("Segoe UI", 9)).pack(anchor="w", padx=15, pady=(0, 5))

        # Forward Primer Card
        PrimerResultCard(self.inner, "Forward Primer (5' → 3')", res['fwd'], "#1976d2") # Blue

        # Reverse Primer Card
        PrimerResultCard(self.inner, "Reverse Primer (5' → 3')", res['rev'], "#d32f2f") # Red

        # PCR Conditions advice
        avg_tm = (res['fwd']['tm'] + res['rev']['tm']) / 2
        annealing_temp = avg_tm - 5  # Standard rule: Ta = Tm - 5°C
        
        advice_frame = tk.Frame(self.inner, bg="#e3f2fd", bd=1, relief="solid")
        advice_frame.pack(fill="x", padx=5, pady=10)
        
        tk.Label(advice_frame, text="Suggested PCR Conditions", font=("Segoe UI", 10, "bold"), bg="#e3f2fd", fg="#1565c0").pack(anchor="w", padx=10, pady=(8,4))
        tk.Label(advice_frame, text=f"• Annealing Temperature: {annealing_temp:.0f}°C", bg="#e3f2fd", font=("Segoe UI", 9)).pack(anchor="w", padx=20)
        tk.Label(advice_frame, text=f"• Extension Time: ~1 min per kb ({res['product_size'] // 1000 + 1} min suggested)", bg="#e3f2fd", font=("Segoe UI", 9)).pack(anchor="w", padx=20)
        tk.Label(advice_frame, text="• Cycles: 25-35 (depending on template amount)", bg="#e3f2fd", font=("Segoe UI", 9)).pack(anchor="w", padx=20, pady=(0,8))


# --- Main Page Class ---

class PrimerDesignerPage(tk.Frame):
    def __init__(self, parent):
        super().__init__(parent, bg="#f0f2f5")
        self.pack(fill="both", expand=True)

        # Header
        header = tk.Frame(self, bg="white", height=50)
        header.pack(fill="x", side="top")
        tk.Label(header, text="Primer Designer", font=("Segoe UI", 16, "bold"), bg="white", fg="#333").pack(side="left", padx=20, pady=10)

        nav_box = tk.Frame(header, bg="white")
        nav_box.pack(side="right", padx=15, pady=8)

        tk.Button(nav_box, text="Next: Review qPCR Probes ➡", command=lambda: self.master.show('qpcr'),
                  bg="#e8f5e9", fg="#2e7d32", font=("Segoe UI", 9, "bold"), padx=10, pady=4, relief="flat", cursor="hand2").pack(side="left", padx=4)

        tk.Button(nav_box, text="Proceed to Final Review & Save ➡", command=lambda: self.master.show('export'),
                  bg="#10b981", fg="white", font=("Segoe UI", 9, "bold"), padx=10, pady=4, relief="flat", cursor="hand2").pack(side="left", padx=4)

        # Tabs
        self.notebook = ttk.Notebook(self)
        self.notebook.pack(fill="both", expand=True, padx=10, pady=10)

        # Tab 1: Designed Primers
        self.tab_single = tk.Frame(self.notebook, bg="#f0f2f5")
        self.notebook.add(self.tab_single, text="  Designed Primers  ")
        self._init_single_ui()

        # Data Store
        self.fragments_data = [] 
        self.batch_results = {} 

    # --------------------------------------------------------------------------
    # TAB 1: Single Sequence UI
    # --------------------------------------------------------------------------
    def _init_single_ui(self):
        # Input Area (Created but not packed to keep the interface ultra-clean)
        input_frame = tk.Frame(self.tab_single, bg="white", padx=10, pady=10)
        
        tk.Label(input_frame, text="Paste DNA Sequence:", bg="white", font=("Segoe UI", 10)).pack(anchor="w")
        self.txt_single = tk.Text(input_frame, height=5, font=("Consolas", 10), bd=1, relief="solid")
        self.txt_single.pack(fill="x", pady=5)

        # Actions
        btn_frame = tk.Frame(input_frame, bg="white")
        btn_frame.pack(fill="x", pady=20)
        
        tk.Button(btn_frame, text="Find Primers", command=self._run_single_design, 
                  bg="#007bff", fg="white", font=("Segoe UI", 10, "bold"), padx=20, pady=5).pack(side="left", padx=5)
                  
        # Result Area
        self.single_panel = PrimerDesignPanel(self.tab_single)
        self.single_panel.pack(fill="both", expand=True)

    def _run_single_design(self):
        seq = self.txt_single.get("1.0", "end").strip()
        if not seq:
            messagebox.showwarning("Empty", "Please enter a DNA sequence.")
            return

        result = find_primers(seq)
        self.single_panel.display_result(result)



    # --------------------------------------------------------------------------
    # TAB 2: Batch UI (Master-Detail)
    # --------------------------------------------------------------------------
    def _init_batch_ui(self):
        # Top Bar
        bar = tk.Frame(self.tab_batch, bg="#e1e4e8", padx=10, pady=5)
        bar.pack(fill="x")
        self.lbl_batch_status = tk.Label(bar, text="No fragments loaded.", bg="#e1e4e8", fg="#555")
        self.lbl_batch_status.pack(side="left")

        # Split View
        paned = ttk.PanedWindow(self.tab_batch, orient="horizontal")
        paned.pack(fill="both", expand=True, padx=5, pady=5)

        # Left: List
        list_frame = tk.Frame(paned, bg="white", width=250)
        paned.add(list_frame, weight=1)

        cols = ("name", "len")
        self.tree = ttk.Treeview(list_frame, columns=cols, show="headings", selectmode="browse")
        self.tree.heading("name", text="Sequence Name")
        self.tree.heading("len", text="Template Size")
        self.tree.column("name", width=150)
        self.tree.column("len", width=80)
        
        ysb = ttk.Scrollbar(list_frame, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=ysb.set)
        
        self.tree.pack(side="left", fill="both", expand=True)
        ysb.pack(side="right", fill="y")
        
        self.tree.bind("<<TreeviewSelect>>", self._on_batch_select)

        # Right: Result
        detail_frame = tk.Frame(paned, bg="#f0f2f5")
        paned.add(detail_frame, weight=3)

        self.lbl_current_frag = tk.Label(detail_frame, text="Select a sequence to view primers", 
                                         font=("Segoe UI", 11, "bold"), bg="#f0f2f5", pady=10)
        self.lbl_current_frag.pack(fill="x")

        self.batch_panel = PrimerDesignPanel(detail_frame)
        self.batch_panel.pack(fill="both", expand=True)

    # --------------------------------------------------------------------------
    # Data Loading & Logic
    # --------------------------------------------------------------------------
    def load_sequences(self, full_seq, fragments):
        """
        Populate the batch list with Full DNA + All Fragments.
        Args:
            full_seq (str): The complete sequence.
            fragments (list): List of dicts [{'seq':..., 'start_enzyme':..., 'end_enzyme':...}, ...]
        """
        self.fragments_data = []
        self.batch_results = {}
        
        # Add Full Sequence (no enzyme tails needed - just for reference)
        self.fragments_data.append({
            'id': 'full',
            'name': 'Whole DNA Construct',
            'seq': full_seq,
            'start_enzyme': None,
            'end_enzyme': None
        })

        # Add Fragments with enzyme info for PCR primer design
        for i, frag in enumerate(fragments):
            start_enz = frag.get('start_enzyme')
            end_enz = frag.get('end_enzyme')
            name = f"Fragment {i+1}"
            if start_enz and end_enz:
                name += f" ({start_enz} → {end_enz})"
            
            self.fragments_data.append({
                'id': f'frag_{i}',
                'name': name,
                'seq': frag.get('seq', ''),
                'start_enzyme': start_enz,
                'end_enzyme': end_enz
            })

        self._refresh_tree()
        self.notebook.select(self.tab_batch)
        self.lbl_batch_status.config(text=f"Loaded {len(self.fragments_data)} sequences. Click a fragment to design PCR primers.")

    def _refresh_tree(self):
        for i in self.tree.get_children():
            self.tree.delete(i)
        
        for item in self.fragments_data:
            length = len(item['seq'])
            self.tree.insert("", "end", iid=item['id'], values=(item['name'], f"{length} bp"))

    def _on_batch_select(self, event):
        sel = self.tree.selection()
        if not sel: return
        
        frag_id = sel[0]
        data = next((f for f in self.fragments_data if f['id'] == frag_id), None)
        if not data: return

        self.lbl_current_frag.config(text=f"Designing for: {data['name']}")

        # Check if already calculated
        if frag_id in self.batch_results:
            self.batch_panel.display_result(self.batch_results[frag_id])
        else:
            # Design primers - for fragments, include enzyme tails for PCR cloning
            start_enz = data.get('start_enzyme')
            end_enz = data.get('end_enzyme')
            
            res = find_primers_for_cloning(data['seq'], start_enz, end_enz)
            self.batch_results[frag_id] = res
            self.batch_panel.display_result(res)

    # --- External API Hook ---
    def set_single_sequence(self, seq: str):
        """Called by other pages to set the Quick Design sequence."""
        self.notebook.select(self.tab_single)
        self.txt_single.delete("1.0", "end")
        self.txt_single.insert("1.0", seq)

    def set_precalculated_result(self, result: dict, seq: str = ""):
        """Called to show an already valid result (e.g. from DNA Fenerate)."""
        self.notebook.select(self.tab_single)
        if seq:
            self.txt_single.delete("1.0", "end")
            self.txt_single.insert("1.0", seq)
            
        self.single_panel.display_result(result)
