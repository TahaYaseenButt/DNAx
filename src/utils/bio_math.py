"""Small, dependency-free DNA sequence and oligonucleotide utilities.

The melting-temperature calculation uses the SantaLucia DNA/DNA nearest-
neighbor model with the monovalent-equivalent salt correction used by
Primer3. It is an in-silico estimate only: the final assay must be checked
under the actual master-mix conditions.
"""

import math


DNA_BASES = frozenset("ATCG")
DNA_WITH_N = DNA_BASES | {"N"}
GAS_CONSTANT_CAL_PER_MOL_K = 1.9872

# SantaLucia 1998 DNA/DNA nearest-neighbor parameters.
# Values are (delta H kcal/mol, delta S cal/(mol K)).
_NN_PARAMS = {
    "AA": (-7.9, -22.2), "TT": (-7.9, -22.2),
    "AT": (-7.2, -20.4),
    "TA": (-7.2, -21.3),
    "CA": (-8.5, -22.7), "TG": (-8.5, -22.7),
    "GT": (-8.4, -22.4), "AC": (-8.4, -22.4),
    "CT": (-7.8, -21.0), "AG": (-7.8, -21.0),
    "GA": (-8.2, -22.2), "TC": (-8.2, -22.2),
    "CG": (-10.6, -27.2),
    "GC": (-9.8, -24.4),
    "GG": (-8.0, -19.9), "CC": (-8.0, -19.9),
}


def normalize_dna(seq, allow_n=False):
    """Return upper-case DNA without whitespace, rejecting invalid bases."""
    if seq is None:
        return ""
    normalized = "".join(str(seq).upper().split())
    allowed = DNA_WITH_N if allow_n else DNA_BASES
    invalid = set(normalized) - allowed
    if invalid:
        bad = ", ".join(sorted(invalid))
        raise ValueError(f"DNA sequence contains unsupported base(s): {bad}")
    return normalized


def get_rev_complement(seq):
    """Return the reverse complement of an A/C/G/T/N DNA sequence."""
    normalized = normalize_dna(seq, allow_n=True)
    if not normalized:
        return ""
    complement = str.maketrans("ATCGN", "TAGCN")
    return normalized.translate(complement)[::-1]


def calculate_tm(
    seq,
    monovalent_salt_mM=50.0,
    magnesium_mM=1.5,
    dntp_mM=0.6,
    oligo_concentration_nM=50.0,
):
    """Estimate DNA/DNA oligo Tm in degrees C using nearest-neighbor physics.

    Defaults mirror the standard Primer3 reaction assumptions. Callers that
    know the assay mix should pass the actual salt, magnesium, dNTP, and
    oligo concentration values. Ambiguous bases cannot be evaluated and
    return ``0.0`` so they are rejected by design filters.
    """
    sequence = normalize_dna(seq, allow_n=True)
    if not sequence or "N" in sequence:
        return 0.0
    if len(sequence) == 1:
        return 2.0 if sequence in "AT" else 4.0

    if min(monovalent_salt_mM, magnesium_mM, dntp_mM, oligo_concentration_nM) < 0:
        raise ValueError("Reaction concentrations cannot be negative")

    # The Wallace rule is preferable to a misleading NN extrapolation for
    # very short oligos, which are not valid qPCR candidates in any case.
    if len(sequence) < 8:
        return float(2 * (sequence.count("A") + sequence.count("T")) + 4 * (sequence.count("G") + sequence.count("C")))

    delta_h = 0.0
    delta_s = 0.0
    for dinucleotide in (sequence[index:index + 2] for index in range(len(sequence) - 1)):
        enthalpy, entropy = _NN_PARAMS[dinucleotide]
        delta_h += enthalpy
        delta_s += entropy

    # Terminal base-pair initiation parameters from the SantaLucia table.
    for terminal_base in (sequence[0], sequence[-1]):
        if terminal_base in "AT":
            delta_h += 2.3
            delta_s += 4.1
        else:
            delta_h += 0.1
            delta_s -= 2.8

    self_complementary = sequence == get_rev_complement(sequence)
    if self_complementary:
        delta_s -= 1.4

    # Primer3's von Ahsen monovalent-equivalent correction. Inputs and
    # output are millimolar in this expression.
    free_magnesium_mM = max(0.0, magnesium_mM - dntp_mM)
    effective_monovalent_mM = monovalent_salt_mM + 120.0 * math.sqrt(free_magnesium_mM)
    if effective_monovalent_mM <= 0.0 or oligo_concentration_nM <= 0.0:
        raise ValueError("Salt and oligo concentrations must be greater than zero")

    salt_molar = effective_monovalent_mM / 1000.0
    delta_s += 0.368 * (len(sequence) - 1) * math.log(salt_molar)

    concentration_molar = oligo_concentration_nM * 1e-9
    concentration_term = concentration_molar / (2.0 if self_complementary else 4.0)
    denominator = delta_s + GAS_CONSTANT_CAL_PER_MOL_K * math.log(concentration_term)
    return (1000.0 * delta_h / denominator) - 273.15


def calculate_gc(seq):
    """Return GC percentage for a DNA sequence (N bases remain in the denominator)."""
    sequence = normalize_dna(seq, allow_n=True)
    if not sequence:
        return 0.0
    return ((sequence.count("G") + sequence.count("C")) / len(sequence)) * 100.0


def has_nucleotide_runs(seq, max_run=4):
    """Return True when a homopolymer run is longer than ``max_run`` bases."""
    sequence = normalize_dna(seq, allow_n=True)
    if not sequence:
        return False
    run = 1
    for index in range(1, len(sequence)):
        if sequence[index] == sequence[index - 1]:
            run += 1
            if run > max_run:
                return True
        else:
            run = 1
    return False


def longest_complementary_run(seq_a, seq_b):
    """Return the longest contiguous anti-parallel complementarity run."""
    first = normalize_dna(seq_a, allow_n=True)
    second = get_rev_complement(seq_b)
    if not first or not second or "N" in first or "N" in second:
        return 0

    max_length = min(len(first), len(second))
    for length in range(max_length, 0, -1):
        for start in range(len(first) - length + 1):
            if first[start:start + length] in second:
                return length
    return 0


def longest_three_prime_complementarity(seq_a, seq_b):
    """Return the longest 3' suffix of either oligo complementary to the other."""
    first = normalize_dna(seq_a, allow_n=True)
    second = normalize_dna(seq_b, allow_n=True)
    if not first or not second or "N" in first or "N" in second:
        return 0

    first_target = get_rev_complement(second)
    second_target = get_rev_complement(first)
    best = 0
    for length in range(1, min(len(first), len(second)) + 1):
        if first[-length:] in first_target or second[-length:] in second_target:
            best = length
    return best


def get_oligo_structure(seq, min_loop=3, max_loop=12):
    """Return simple sequence-structure metrics suitable for design triage.

    This intentionally reports complementary runs rather than pretending to
    calculate a full secondary-structure delta G. A thermodynamic structure
    engine is still required before release to production.
    """
    sequence = normalize_dna(seq, allow_n=True)
    if not sequence or "N" in sequence:
        return {
            "max_hairpin_stem": 0,
            "max_self_dimer_run": 0,
            "max_three_prime_self_dimer": 0,
        }

    longest_stem = 0
    n = len(sequence)
    for left_start in range(n):
        for stem_length in range(2, (n - left_start) // 2 + 1):
            left_end = left_start + stem_length
            for loop_length in range(min_loop, max_loop + 1):
                right_start = left_end + loop_length
                right_end = right_start + stem_length
                if right_end > n:
                    break
                if sequence[left_start:left_end] == get_rev_complement(sequence[right_start:right_end]):
                    longest_stem = max(longest_stem, stem_length)

    return {
        "max_hairpin_stem": longest_stem,
        "max_self_dimer_run": longest_complementary_run(sequence, sequence),
        "max_three_prime_self_dimer": longest_three_prime_complementarity(sequence, sequence),
    }


def get_pairwise_complementarity(seq_a, seq_b):
    """Return total and 3' anti-parallel complementarity metrics for two oligos."""
    return {
        "max_complementary_run": longest_complementary_run(seq_a, seq_b),
        "max_three_prime_complementarity": longest_three_prime_complementarity(seq_a, seq_b),
    }


def check_hairpin(seq, min_stem=4, max_loop=8):
    """Compatibility wrapper returning whether a hairpin stem meets the threshold."""
    return get_oligo_structure(seq, min_loop=3, max_loop=max_loop)["max_hairpin_stem"] >= min_stem


def check_self_dimer(seq, min_complementary=4):
    """Compatibility wrapper emphasizing extension-prone 3' self-dimers."""
    structure = get_oligo_structure(seq)
    return (
        structure["max_three_prime_self_dimer"] >= min_complementary
        or structure["max_self_dimer_run"] >= min_complementary + 3
    )
