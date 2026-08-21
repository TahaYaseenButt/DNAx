import math
from utils.bio_math import calculate_gc, calculate_tm

# Standard Bioinformatics Alignment Scoring
DEFAULT_MATCH_SCORE = 2
DEFAULT_MISMATCH_PENALTY = -1
DEFAULT_GAP_PENALTY = -2

def needleman_wunsch(seq1: str, seq2: str, match_score=DEFAULT_MATCH_SCORE,
                     mismatch_penalty=DEFAULT_MISMATCH_PENALTY,
                     gap_penalty=DEFAULT_GAP_PENALTY) -> dict:
    """
    Computes standard Needleman-Wunsch Global Sequence Alignment between seq1 and seq2.
    Returns optimal score, aligned sequences, match representation, and percentage identity.
    """
    s1 = seq1.upper().strip()
    s2 = seq2.upper().strip()
    n = len(s1)
    m = len(s2)

    if n == 0 or m == 0:
        return {
            'score': 0,
            'aligned_seq1': s1,
            'aligned_seq2': s2,
            'match_line': '',
            'matches': 0,
            'mismatches': 0,
            'gaps': max(n, m),
            'alignment_length': max(n, m),
            'identity_pct': 0.0,
            'similarity_pct': 0.0
        }

    # Initialize DP score matrix
    # Row: i (0..n), Col: j (0..m)
    dp = [[0] * (m + 1) for _ in range(n + 1)]

    for i in range(n + 1):
        dp[i][0] = i * gap_penalty
    for j in range(m + 1):
        dp[0][j] = j * gap_penalty

    # Fill DP matrix
    for i in range(1, n + 1):
        ch1 = s1[i - 1]
        for j in range(1, m + 1):
            ch2 = s2[j - 1]
            match_val = match_score if ch1 == ch2 else mismatch_penalty
            score_diag = dp[i - 1][j - 1] + match_val
            score_up = dp[i - 1][j] + gap_penalty
            score_left = dp[i][j - 1] + gap_penalty
            dp[i][j] = max(score_diag, score_up, score_left)

    # Traceback
    aligned1 = []
    aligned2 = []
    match_line = []
    matches = 0
    mismatches = 0
    gaps = 0

    i, j = n, m
    while i > 0 or j > 0:
        current_score = dp[i][j]
        if i > 0 and j > 0:
            ch1 = s1[i - 1]
            ch2 = s2[j - 1]
            match_val = match_score if ch1 == ch2 else mismatch_penalty
            if current_score == dp[i - 1][j - 1] + match_val:
                aligned1.append(ch1)
                aligned2.append(ch2)
                if ch1 == ch2:
                    match_line.append('|')
                    matches += 1
                else:
                    match_line.append('.')
                    mismatches += 1
                i -= 1
                j -= 1
                continue

        if i > 0 and current_score == dp[i - 1][j] + gap_penalty:
            aligned1.append(s1[i - 1])
            aligned2.append('-')
            match_line.append(' ')
            gaps += 1
            i -= 1
        elif j > 0:
            aligned1.append('-')
            aligned2.append(s2[j - 1])
            match_line.append(' ')
            gaps += 1
            j -= 1
        else:
            break

    aligned_s1 = ''.join(reversed(aligned1))
    aligned_s2 = ''.join(reversed(aligned2))
    match_str = ''.join(reversed(match_line))
    alignment_length = len(aligned_s1)

    identity_pct = round((matches / max(1, alignment_length)) * 100, 2)
    similarity_pct = round((matches / max(1, min(n, m))) * 100, 2)

    return {
        'score': dp[n][m],
        'aligned_seq1': aligned_s1,
        'aligned_seq2': aligned_s2,
        'match_line': match_str,
        'matches': matches,
        'mismatches': mismatches,
        'gaps': gaps,
        'alignment_length': alignment_length,
        'identity_pct': identity_pct,
        'similarity_pct': similarity_pct,
        'gc_delta': round(abs(calculate_gc(s1) - calculate_gc(s2)), 2),
        'tm_delta': round(abs(calculate_tm(s1) - calculate_tm(s2)), 2),
        'length_delta': abs(n - m)
    }

def compute_fast_similarity(seq1: str, seq2: str, k: int = 4) -> float:
    """
    Computes rapid k-mer Jaccard/Identity similarity for high-throughput batch filtering.
    For sequences under 800bp, uses full Needleman-Wunsch.
    """
    s1 = seq1.upper().strip()
    s2 = seq2.upper().strip()
    if s1 == s2:
        return 100.0
    if not s1 or not s2:
        return 0.0

    # If sequences are reasonable size, compute exact Needleman-Wunsch identity
    if len(s1) <= 800 and len(s2) <= 800:
        res = needleman_wunsch(s1, s2)
        return res['identity_pct']

    # Fast k-mer profile similarity for ultra-long constructs
    k = min(k, len(s1), len(s2))
    if k <= 1:
        res = needleman_wunsch(s1[:400], s2[:400])
        return res['identity_pct']

    kmers1 = {}
    for i in range(len(s1) - k + 1):
        km = s1[i:i+k]
        kmers1[km] = kmers1.get(km, 0) + 1

    kmers2 = {}
    for i in range(len(s2) - k + 1):
        km = s2[i:i+k]
        kmers2[km] = kmers2.get(km, 0) + 1

    all_keys = set(kmers1.keys()).union(set(kmers2.keys()))
    intersection = sum(min(kmers1.get(k_val, 0), kmers2.get(k_val, 0)) for k_val in all_keys)
    union = sum(max(kmers1.get(k_val, 0), kmers2.get(k_val, 0)) for k_val in all_keys)

    jaccard = (intersection / max(1, union)) * 100
    return round(jaccard, 2)

def compute_vectorized_kmer_matrix(sequences: list, k: int = 4) -> list:
    """
    High-performance O(N*L + N^2) vectorized k-mer cosine similarity matrix.
    Industry standard method (Mash / CD-HIT / QIIME) for scaling to hundreds/thousands of sequences.
    """
    try:
        import numpy as np
        n = len(sequences)
        if n == 0:
            return []

        # 4-mer index mapping (4^4 = 256 dimensions)
        bases = ['A', 'C', 'G', 'T']
        kmers = [a+b+c+d for a in bases for b in bases for c in bases for d in bases]
        kmer_to_idx = {km: idx for idx, km in enumerate(kmers)}
        dim = len(kmers)

        vectors = np.zeros((n, dim), dtype=np.float32)
        for i, s in enumerate(sequences):
            seq_u = s.upper()
            seq_len = len(seq_u)
            if seq_len < k:
                continue
            for j in range(seq_len - k + 1):
                sub = seq_u[j:j+k]
                idx = kmer_to_idx.get(sub)
                if idx is not None:
                    vectors[i, idx] += 1.0

        # Vector normalization (L2 norm)
        norms = np.linalg.norm(vectors, axis=1, keepdims=True)
        norms[norms == 0] = 1.0
        norm_vecs = vectors / norms

        # Cosine similarity matrix in percentage (0% to 100%)
        sim_mat = np.clip(norm_vecs @ norm_vecs.T, 0.0, 1.0) * 100.0
        
        # Ensure diagonal is exactly 100%
        np.fill_diagonal(sim_mat, 100.0)

        return np.round(sim_mat, 2).tolist()
    except Exception:
        # Fallback to pairwise loop if numpy is unavailable
        n = len(sequences)
        mat = [[0.0] * n for _ in range(n)]
        for i in range(n):
            mat[i][i] = 100.0
            for j in range(i + 1, n):
                val = compute_fast_similarity(sequences[i], sequences[j])
                mat[i][j] = val
                mat[j][i] = val
        return mat

def compute_similarity_matrix(sequence_records: list, method: str = 'auto') -> dict:
    """
    Computes an N x N pairwise similarity matrix across a list of sequence records.
    Standardized bioinformatics pipeline:
    - If N <= 25 and sequences <= 600bp: uses exact Needleman-Wunsch global identity matrix (EMBOSS Needle standard).
    - If N > 25 or method == 'kmer': uses vectorized k-mer frequency alignment (Mash / CD-HIT standard).
    """
    n = len(sequence_records)
    if n == 0:
        return {
            'names': [],
            'ids': [],
            'matrix': [],
            'min_sim': 0.0,
            'max_sim': 0.0,
            'avg_sim': 0.0,
            'high_similarity_pairs': [],
            'method_used': 'None'
        }

    names = [r.get('name', f"Seq_{r.get('id', i+1)}") for i, r in enumerate(sequence_records)]
    ids = [r.get('id', i+1) for i, r in enumerate(sequence_records)]
    seqs = [r.get('payload') or r.get('linear_seq', '') for r in sequence_records]

    # Decide method
    use_exact_nw = False
    if method == 'exact':
        use_exact_nw = True
    elif method == 'auto':
        max_len = max((len(s) for s in seqs), default=0)
        if n <= 25 and max_len <= 600:
            use_exact_nw = True

    if use_exact_nw:
        method_used = 'Needleman-Wunsch (Exact Global Identity)'
        matrix = [[0.0] * n for _ in range(n)]
        for i in range(n):
            matrix[i][i] = 100.0
            for j in range(i + 1, n):
                res = needleman_wunsch(seqs[i], seqs[j])
                val = res['identity_pct']
                matrix[i][j] = val
                matrix[j][i] = val
    else:
        method_used = 'Vectorized 4-mer Genomic Distance (Mash / CD-HIT Standard)'
        matrix = compute_vectorized_kmer_matrix(seqs, k=4)

    off_diag_values = []
    high_similarity_pairs = []

    for i in range(n):
        for j in range(i + 1, n):
            val = matrix[i][j]
            off_diag_values.append(val)
            if val >= 60.0:
                high_similarity_pairs.append({
                    'seq1_id': ids[i],
                    'seq1_name': names[i],
                    'seq2_id': ids[j],
                    'seq2_name': names[j],
                    'similarity': val
                })

    min_sim = min(off_diag_values) if off_diag_values else 100.0
    max_sim = max(off_diag_values) if off_diag_values else 100.0
    avg_sim = sum(off_diag_values) / len(off_diag_values) if off_diag_values else 100.0

    return {
        'names': names,
        'ids': ids,
        'matrix': matrix,
        'records': sequence_records,
        'min_sim': round(min_sim, 2),
        'max_sim': round(max_sim, 2),
        'avg_sim': round(avg_sim, 2),
        'high_similarity_pairs': sorted(high_similarity_pairs, key=lambda x: x['similarity'], reverse=True),
        'method_used': method_used
    }

def compare_query_to_database(query_seq: str, db_records: list) -> list:
    """
    Compares a single query DNA sequence against all records in the database.
    Returns a sorted list of comparison matches from highest similarity to lowest.
    """
    if not query_seq or not db_records:
        return []

    results = []
    for r in db_records:
        target_seq = r.get('payload') or r.get('linear_seq', '')
        if not target_seq:
            continue
        sim = compute_fast_similarity(query_seq, target_seq)
        results.append({
            'id': r.get('id'),
            'name': r.get('name'),
            'similarity': sim,
            'length': r.get('length', len(target_seq)),
            'gc_pct': r.get('gc_pct', calculate_gc(target_seq)),
            'created_at': r.get('created_at', ''),
            'notes': r.get('notes', ''),
            'target_seq': target_seq
        })

    return sorted(results, key=lambda x: x['similarity'], reverse=True)

def get_similarity_status(max_similarity: float) -> tuple:
    """
    Evaluates barcode/taggant orthogonality based on maximum similarity with existing sequences.
    Returns (status_text, color_code, is_safe_bool).
    """
    if max_similarity < 30.0:
        return ("Highly Unique & Orthogonal (Safe)", "#2e7d32", True)
    elif max_similarity < 55.0:
        return ("Moderate Similarity (Acceptable)", "#0288d1", True)
    elif max_similarity < 75.0:
        return ("High Similarity Detected (Caution)", "#f57c00", False)
    else:
        return ("Very High Cross-Homology (Potential Clash)", "#d32f2f", False)

def check_oligo_cross_reactivity(oligo_seq: str, target_seq: str, min_seed_len: int = 10, max_identity: float = 65.0) -> bool:
    """
    Checks if an oligo (primer or probe) cross-hybridizes or binds to target_seq or its reverse complement.
    Returns True if a clash/cross-reactivity is detected, False if clean.
    """
    if not oligo_seq or not target_seq:
        return False

    o = oligo_seq.upper().strip()
    t = target_seq.upper().strip()
    from utils.bio_math import get_rev_complement
    t_rc = get_rev_complement(t)

    # 1. Exact match / substring check
    if o in t or o in t_rc or t in o:
        return True

    # 2. Critical 3' end seed check for primers (last 8bp)
    if len(o) >= 8:
        three_prime = o[-8:]
        if three_prime in t or three_prime in t_rc:
            return True

    # 3. K-mer exact seed match (min_seed_len continuous bases)
    for i in range(len(o) - min_seed_len + 1):
        kmer = o[i:i+min_seed_len]
        if kmer in t or kmer in t_rc:
            return True

    # 4. Global identity check
    sim = compute_fast_similarity(o, t)
    if sim >= max_identity:
        return True

    return False

def validate_primers_and_probes_against_db(fwd_seq: str, rev_seq: str, probes_list: list, db_records: list) -> dict:
    """
    Comprehensive validation ensuring primers and probes are 100% unique and orthogonal
    across all existing sequences, primers, and probes stored in the database.
    """
    primer_clashes = []
    probe_clashes = []

    fwd_u = (fwd_seq or '').upper().strip()
    rev_u = (rev_seq or '').upper().strip()

    # Extract all stored oligos
    existing_primers = []
    existing_probes = []

    for r in db_records:
        rec_name = r.get('name', f"ID_{r.get('id')}")
        rec_payload = r.get('payload') or r.get('linear_seq', '')

        # Check candidate primers against stored sequences
        if fwd_u and check_oligo_cross_reactivity(fwd_u, rec_payload):
            primer_clashes.append(f"Fwd primer shares homology with sequence '{rec_name}'")
        if rev_u and check_oligo_cross_reactivity(rev_u, rec_payload):
            primer_clashes.append(f"Rev primer shares homology with sequence '{rec_name}'")

        # Check candidate primers against stored primers
        primers_data = r.get('primers')
        if primers_data and isinstance(primers_data, dict):
            stored_fwd = primers_data.get('fwd', {}).get('seq', '')
            stored_rev = primers_data.get('rev', {}).get('seq', '')
            if stored_fwd:
                if fwd_u == stored_fwd.upper():
                    primer_clashes.append(f"Fwd primer is identical to Fwd primer of '{rec_name}'")
                elif fwd_u and check_oligo_cross_reactivity(fwd_u, stored_fwd):
                    primer_clashes.append(f"Fwd primer cross-hybridizes with Fwd primer of '{rec_name}'")
            if stored_rev:
                if rev_u == stored_rev.upper():
                    primer_clashes.append(f"Rev primer is identical to Rev primer of '{rec_name}'")
                elif rev_u and check_oligo_cross_reactivity(rev_u, stored_rev):
                    primer_clashes.append(f"Rev primer cross-hybridizes with Rev primer of '{rec_name}'")

        # Check candidate probes
        stored_probes = r.get('probes') or []
        for p in probes_list:
            p_seq = (p.get('seq') if isinstance(p, dict) else str(p)).upper().strip()
            if not p_seq:
                continue

            # Check against stored sequence
            if check_oligo_cross_reactivity(p_seq, rec_payload, min_seed_len=10):
                probe_clashes.append(f"Probe '{p_seq[:10]}...' binds to sequence '{rec_name}'")

            # Check against stored probes
            for sp in stored_probes:
                sp_seq = (sp.get('seq') if isinstance(sp, dict) else str(sp)).upper().strip()
                if p_seq == sp_seq:
                    probe_clashes.append(f"Probe '{p_seq}' is identical to a probe in '{rec_name}'")
                elif check_oligo_cross_reactivity(p_seq, sp_seq, min_seed_len=8, max_identity=60.0):
                    probe_clashes.append(f"Probe '{p_seq[:10]}...' cross-homologous with probe in '{rec_name}'")

    is_valid = len(primer_clashes) == 0 and len(probe_clashes) == 0

    return {
        'is_valid': is_valid,
        'primer_clashes': primer_clashes,
        'probe_clashes': probe_clashes,
        'status_text': "100% Unique & Orthogonal (0 Clashes)" if is_valid else f"Clashes detected ({len(primer_clashes)} primer, {len(probe_clashes)} probe)",
        'is_safe': is_valid
    }
