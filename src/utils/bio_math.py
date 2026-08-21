import math

# --- DNA Math Utilities ---

def get_rev_complement(seq):
    """Returns the reverse complement of a DNA sequence."""
    if not seq: return ""
    complement = {'A': 'T', 'T': 'A', 'C': 'G', 'G': 'C', 'N': 'N', 
                  'a': 't', 't': 'a', 'c': 'g', 'g': 'c', 'n': 'n'}
    return "".join(complement.get(base, base) for base in reversed(seq))

def calculate_tm(seq):
    """
    Calculates melting temperature (Tm) for oligos under real-world qPCR assay conditions.
    Uses Wallace rule for <14bp, Salt-adjusted formula with monovalent + magnesium equivalent (~350mM Na+).
    """
    if not seq: return 0.0
    seq = seq.upper()
    a = seq.count('A')
    t = seq.count('T')
    c = seq.count('C')
    g = seq.count('G')
    n = len(seq)
    
    if n < 14:
        # Wallace rule
        return (a + t) * 2 + (g + c) * 4
    else:
        # Real-world qPCR salt-adjusted (350mM Na+ equivalent to account for Mg2+ stabilization)
        na_conc = 0.35
        tm = 81.5 + 16.6 * math.log10(na_conc) + 41 * (g + c) / n - 675 / n
        return tm

def calculate_gc(seq):
    """Calculates GC content percentage."""
    if not seq: return 0.0
    seq = seq.upper()
    g = seq.count('G')
    c = seq.count('C')
    return ((g + c) / len(seq)) * 100

def has_nucleotide_runs(seq, max_run=4):
    """Check if sequence has runs of same nucleotide > max_run."""
    if not seq: return False
    seq = seq.upper()
    run = 1
    for i in range(1, len(seq)):
        if seq[i] == seq[i-1]:
            run += 1
            if run > max_run:
                return True
        else:
            run = 1
    return False

def check_hairpin(seq, min_stem=4, max_loop=8):
    """Check for potential hairpin formation."""
    if not seq: return False
    seq = seq.upper()
    n = len(seq)
    for stem_len in range(min_stem, n // 2):
        for loop_start in range(stem_len, n - stem_len - 3):
            loop_end = loop_start + 3
            while loop_end <= min(loop_start + max_loop, n - stem_len):
                left = seq[:stem_len]
                right = seq[loop_end:loop_end + stem_len]
                # Simple check: direct reverse complement match
                if left == get_rev_complement(right):
                    return True
                loop_end += 1
    return False

def check_self_dimer(seq, min_complementary=4):
    """Check for self-dimerization."""
    if not seq: return False
    seq = seq.upper()
    rc = get_rev_complement(seq)
    n = len(seq)
    
    # Critical 3' end check
    three_prime = seq[-6:]
    if three_prime in rc:
        return True
        
    for i in range(n - min_complementary + 1):
        segment = seq[i:i + min_complementary]
        if segment in rc:
            return True
    return False
