import tkinter as tk
from tkinter import messagebox

# Need RE Data for overhang calculation
try:
    from tools.primer_designer import RESTRICTION_DATA
except Exception:
    RESTRICTION_DATA = {}

# --- Simulation Logic ---

def get_sticky_end(enzyme_name: str, direction: str) -> str:
    """
    Returns the overhang sequence for a given enzyme.
    RESTRICTION_DATA format: { "EcoRI": ("GAATTC", "GAATTC") ... }
    In this simplified simulation, we assume standard sticky ends.
    
    direction: '5' (start of fragment) or '3' (end of fragment)
    """
    if not enzyme_name or enzyme_name == "None":
        return ""
    
    # For simulation purposes, we need to know the actual cut pattern.
    # Since we don't have a full cut database here, we will infer overhangs 
    # based on common knowledge or assume a standard 4bp overhang from the recognition site
    # if it's a palindromic Type II enzyme.
    
    site = RESTRICTION_DATA.get(enzyme_name, ("", ""))[0]
    if len(site) < 6:
        return "" # Blunt or unknown
        
    # Approximation for standard cohesive ends:
    # Most common enzymes (EcoRI, BamHI, etc.) leave a 4bp overhang.
    # We'll validatate based on the idea that Fragment A's 3' overhang must match Fragment B's 5' overhang.
    
    # Actually, for ligation to work:
    # The 3' end of Frag 1 usually produces an overhang that pairs with the 5' end of Frag 2.
    # If Frag 1 is cut with BamHI (G^GATCC), the 3' end leaves 'GATC...' overhang on the bottom strand? 
    # Let's verify compatibility simply by Enzyme Name matching for now (Industrial Standard v1).
    # If Frag 1 Ends with BamHI, Frag 2 MUST Start with BamHI.
    
    return enzyme_name

def reverse_complement(seq: str) -> str:
    mp = {'A':'T','T':'A','C':'G','G':'C','N':'N'}
    return "".join(mp.get(c, 'N') for c in reversed(seq.upper()))

def run_simulation(fragments: list):
    """
    Validates the assembly pipeline.
    fragments: list of dicts [{'seq':..., 'start_enzyme':..., 'end_enzyme':...}]
    
    Returns: A list of result dicts for each step.
    """
    report = {
        "steps": [],
        "success": True,
        "final_seq": ""
    }
    
    if not fragments:
        return {"error": "No fragments provided."}

    # 1. PCR Validation (Primers Check)
    # We verify if we can hypothetically design primers (length > 20, GC ok)
    step_pcr = {"name": "Phase 1: PCR Amplification", "logs": [], "status": True}
    for i, frag in enumerate(fragments):
        s = frag.get('seq', '')
        # Simple heuristics for "Is this amplifiable?"
        if len(s) < 20:
            step_pcr["logs"].append(f"Fragment {i+1}: FAIL - Too short for PCR (<20bp).")
            step_pcr["status"] = False
        else:
            gc = (s.count('G') + s.count('C')) / len(s)
            if 0.2 < gc < 0.8:
                step_pcr["logs"].append(f"Fragment {i+1}: PASS - PCR viable (GC={gc:.0%}).")
            else:
                step_pcr["logs"].append(f"Fragment {i+1}: WARN - Extreme GC content ({gc:.0%}). PCR may be difficult.")
    
    if not step_pcr["status"]:
        report["success"] = False
    report["steps"].append(step_pcr)
    
    # 2. Digestion Validation
    step_dig = {"name": "Phase 2: Restriction Digestion", "logs": [], "status": True}
    for i, frag in enumerate(fragments):
        s = frag.get('seq', '')
        start = frag.get('start_enzyme')
        end = frag.get('end_enzyme')
        
        # Site must exist in the sequence (usually at ends)
        start_site = RESTRICTION_DATA.get(start, ("", ""))[0] if start else ""
        end_site = RESTRICTION_DATA.get(end, ("", ""))[0] if end else ""
        
        # Check if sites exist
        errs = []
        if start_site and start_site not in s:
            errs.append(f"Start site {start} ({start_site}) not found in sequence.")
        if end_site and end_site not in s:
            errs.append(f"End site {end} ({end_site}) not found in sequence.")
            
        # Internal sites check (forbidden internal cuts)
        # Scan for ANY chosen enzyme inside the body (excluding ends)
        # Cut the ends off to check body
        inner = s[len(start_site):-len(end_site)] if (start_site and end_site) else s
        
        # Check all enzymes used in the assembly
        used_enzymes = set()
        for f in fragments:
            if f.get('start_enzyme'): used_enzymes.add(f.get('start_enzyme'))
            if f.get('end_enzyme'): used_enzymes.add(f.get('end_enzyme'))
            
        for enz in used_enzymes:
            if enz == 'None': continue
            site = RESTRICTION_DATA.get(enz, ("", ""))[0]
            if site and site in inner:
                errs.append(f"FAIL - Internal cut site found for {enz}. Fragment will be chopped.")
                
        if errs:
            step_dig["status"] = False
            for e in errs:
                step_dig["logs"].append(f"Fragment {i+1}: {e}")
        else:
            step_dig["logs"].append(f"Fragment {i+1}: PASS - Sites valid, no internal cuts.")
            
    if not step_dig["status"]:
        report["success"] = False
    report["steps"].append(step_dig)
    
    # 3. Ligation / Assembly Validation
    step_lig = {"name": "Phase 3: Ligation & Circularization", "logs": [], "status": True}
    
    # Check 1->2, 2->3, 3->4, 4->1 (Circle)
    n = len(fragments)
    for i in range(n):
        curr = fragments[i]
        next_frag = fragments[(i + 1) % n]
        
        # Connection: End of i connects to Start of i+1
        e1 = curr.get('end_enzyme')
        e2 = next_frag.get('start_enzyme')
        
        # Strict compatibility: Enzymes must be identical (or compatible ends, but we assume identical for this sim)
        if e1 != e2:
            step_lig["status"] = False
            step_lig["logs"].append(f"Junction {i+1}-{((i+1)%n)+1}: FAIL - Mismatched ends ({e1} vs {e2}). cannot ligate.")
        elif e1 == 'None' or not e1:
            step_lig["status"] = False
            step_lig["logs"].append(f"Junction {i+1}-{((i+1)%n)+1}: FAIL - Missing enzyme site.")
        else:
            step_lig["logs"].append(f"Junction {i+1}-{((i+1)%n)+1}: PASS - Compatible sticky ends ({e1}).")
            
    if step_lig["status"]:
        step_lig["logs"].append("Circularization: PASS - All junctions compatible. closed circle formed.")
        # Construct final validation seq
        full = "".join((f.get('start_site','')+f.get('core','')) for f in fragments)
        report["final_seq"] = full
    else:
        report["success"] = False
        step_lig["logs"].append("Circularization: FAIL - Open circle or mismatched ends.")
        
    report["steps"].append(step_lig)
    
    return report

class SimulationResultsWindow(tk.Toplevel):
    def __init__(self, parent, report):
        super().__init__(parent)
        self.title("Industrial In Silico Validation")
        self.geometry("700x600")
        self.configure(bg="#f0f2f5")
        
        tk.Label(self, text="Validation Report", font=("Segoe UI", 16, "bold"), bg="#f0f2f5").pack(pady=10)
        
        # Summary Header
        status_color = "#2e7d32" if report["success"] else "#d32f2f"
        status_text = "PASSED" if report["success"] else "FAILED"
        tk.Label(self, text=f"Overall Status: {status_text}", font=("Segoe UI", 14, "bold"), fg=status_color, bg="#f0f2f5").pack(pady=(0,10))
        
        # Scrollable container
        canvas = tk.Canvas(self, bg="#ffffff")
        sb = tk.Scrollbar(self, orient="vertical", command=canvas.yview)
        canvas.configure(yscrollcommand=sb.set)
        
        inner = tk.Frame(canvas, bg="#ffffff")
        canvas.create_window((0,0), window=inner, anchor="nw")
        
        canvas.pack(side="left", fill="both", expand=True, padx=10, pady=10)
        sb.pack(side="right", fill="y", pady=10)
        
        inner.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
        
        # Render steps
        for step in report["steps"]:
            f = tk.Frame(inner, bg="#ffffff", bd=1, relief="solid")
            f.pack(fill="x", padx=5, pady=5)
            
            s_col = "#2e7d32" if step["status"] else "#c62828"
            icon = "✓" if step["status"] else "X"
            
            header = tk.Frame(f, bg="#f5f5f5")
            header.pack(fill="x")
            tk.Label(header, text=f"{icon} {step['name']}", font=("Segoe UI", 11, "bold"), fg=s_col, bg="#f5f5f5").pack(anchor="w", padx=5, pady=5)
            
            for log in step["logs"]:
                fg = "#333"
                if "FAIL" in log: fg = "#c62828"
                elif "WARN" in log: fg = "#ef6c00"
                tk.Label(f, text=f"• {log}", font=("Consolas", 9), bg="#ffffff", fg=fg, wraplength=600, justify="left").pack(anchor="w", padx=15, pady=2)

    
