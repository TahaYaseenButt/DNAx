# DNAₓ Lab: Step-by-Step Biological Guide

## Overview
This guide explains the scientific workflow your software follows for DNA generation, primer design, and probe design—with biological reasoning at each step.

---

# PART 1: DNA GENERATION WORKFLOW

## What is DNA Generation in Your Software?

Your software generates **synthetic DNA constructs** for forensic authentication  a real molecular cloning technique. The goal is to create a unique, traceable DNA sequence that can be authenticated later.

---

## Step 1: Payload Generation (Random DNA Sequence)

### Biological Context
The **payload** is the "core" synthetic DNA that carries forensic information. It must be:
- **Random** (not found in nature)
- **Stable** (proper base composition)
- **Amplifiable** (good GC content for PCR)

### What Your Software Does

```
User Input: 500 bp (desired payload length)
                    ↓
          [Generate Random DNA]
                    ↓
         Sequence like: ATGCTAGCCGATCGATCGTAGCC...
```

### Code Reference: `_safe_random_dna()` in `dna_generate.py`

```python
def _safe_random_dna(self, length: int) -> str:
    res = []
    for _ in range(length):
        allowed = ['A', 'T', 'C', 'G']
        # CONSTRAINT: Prevent homopolymer runs (≥3 consecutive same base)
        if len(res) >= 3 and res[-1] == res[-2] == res[-3]:
            allowed.remove(res[-1])  # Remove the problematic base
        res.append(random.choice(allowed))
    return ''.join(res)
```

**Why this matters biologically:**
- Homopolymer runs (AAAAA) cause **polymerase slippage** during PCR → amplification errors
- Random selection ensures the DNA isn't naturally occurring (authenticity marker)

---

## Step 2: Validate Payload (Quality Control)

### Biological Requirements

Your software validates the generated sequence against 3 constraints:

### Constraint 1: GC Content (40-60%)

**Biological Principle:**
- **G-C base pairs** have 3 hydrogen bonds (stronger)
- **A-T base pairs** have 2 hydrogen bonds (weaker)
- Too high GC% → sequence too stable → hard to denature during PCR
- Too low GC% → sequence too unstable → poor primer binding

**Your Software Check:**
```python
gc_percent = (payload.count('G') + payload.count('C')) / len(payload) * 100

if 40 <= gc_percent <= 60:
    ✓ PASS - Good balance for PCR amplification
else:
    ✗ FAIL - Retry generation
```

---

### Constraint 2: No Homopolymer Runs (≥5 consecutive bases)

**Biological Principle:**
- Repeating bases (AAAAA) cause **polymerase slippage**
- DNA polymerase can "slip" and insert extra bases → artifacts
- Blocks 3-base minimum to prevent this

**Your Software Check:**
```python
def has_nucleotide_runs(seq, max_run=4):
    for i in range(1, len(seq)):
        if seq[i] == seq[i-1]:
            if run_length > 4:
                return True  # ✗ FAIL
    return False  # ✓ PASS
```

---

### Constraint 3: No BsaI Restriction Sites (GGTCTC or GAGACC)

**Biological Principle:**
- **BsaI** is a restriction enzyme (molecular scissors) used in Golden Gate Assembly
- If your payload contains BsaI recognition sites, the enzyme will **cut your DNA internally** → assembly fails
- Must eliminate these sequences to ensure integrity

**Your Software Check:**
```python
if "GGTCTC" in payload or "GAGACC" in payload:
    ✗ FAIL - Remove BsaI sites, retry
else:
    ✓ PASS - Safe for assembly
```

---

## Step 3: Smart Payload Construction (If Primers/Probes Needed)

### Biological Context
If you selected **Universal Primers** or want probes embedded, your software structures the payload strategically:

```
Structure:
[Good 5' Primer Site] -- [Spacer] -- [Probe 1] -- [Spacer] -- [Probe 2] -- ... -- [Good 3' Primer Site]
```

### Why This Layout?

1. **5' Primer Binding Site** (25bp GC-rich region)
   - Ensures PCR primers can bind at the start → full-length amplification

2. **Spacer Regions** (5-10bp random DNA)
   - Provides breathing room between functional elements
   - Reduces secondary structure (hairpins)

3. **Probe Binding Sites** (22-24bp each)
   - Pre-embedded locations for TaqMan probes
   - Ensures probes anneal during qPCR

4. **3' Primer Binding Site** (25bp GC-rich region)
   - Ensures PCR primers can bind at the end → defined product size

### Code Reference: `_generate_smart_payload()` in `dna_generate.py`

```python
def _generate_smart_payload(self, length, ideal_probes):
    # 1. Create 5' primer binding site
    fwd_seed = self._safe_random_dna(25) + "GC"  # GC clamp for stability
    
    # 2. Create 3' primer binding site (reverse complement)
    rev_seed = reverse_complement(self._safe_random_dna(25) + "GC")
    
    # 3. Calculate remaining space
    remaining = length - len(fwd_seed) - len(rev_seed)
    
    # 4. Distribute probes evenly through remaining space with spacers
    parts = [fwd_seed]
    for probe in ideal_probes:
        parts.append(spacer)  # 5bp spacer
        parts.append(probe['seq'])  # Probe sequence
        parts.append(spacer)
    
    parts.append(rev_seed)
    
    return ''.join(parts)
```

---

## Step 4: Linear Construction (Assemble Final Construct)

### For Linear Mode
```
Simply output the payload as-is:
Output: [Payload DNA]
        Example: ATGCTAGCCGATCGATCGTAGCC...
```

### For Circular Mode (Golden Gate Assembly)
```
[BsaI Site] - [Spacer] - [L-Overhang] - [Payload] - [R-Overhang] - [Spacer] - [BsaI Rev]
   6bp           1bp        4bp         N bp         4bp          1bp        6bp
```

**What is "Golden Gate"?**

Golden Gate is a **DNA assembly technique** using:
- **BsaI enzyme**: Cuts at recognition sites, creating **sticky ends** (overhangs)
- **Compatible sticky ends**: Allow fragments to ligate (join) in a specific order
- **Type IIS enzymes**: Cut outside their recognition site, enabling scarless assembly

**Biological Sequence:**

```
STEP 1: Construct Assembly (Your Software Creates This)
┌──────────────────────────────────────────────────────┐
│ [BsaI]--[Spacer]--[GTCA]--[PAYLOAD]--[TGAC]--[Spacer]--[BsaI-Rev] │
└──────────────────────────────────────────────────────┘

STEP 2: BsaI Digestion (In Real Lab)
The enzyme recognizes GGTCTC and cuts, leaving sticky ends:
┌──────┐ GTCA [PAYLOAD] TGAC ┌──────┐
│ Gone │  ↑               ↑  │ Gone │
└──────┘ [Sticky Ends Exposed - Now they stick together!]

STEP 3: Ligation (In Real Lab)
DNA ligase seals the backbone, creating a circle:
        ↓ (Circularization)
    ╔═══════════════╗
    ║  PAYLOAD DNA  ║ (Circular plasmid)
    ║ (Closed ring) ║
    ╚═══════════════╝
```

### Code Reference: `dna_generate.py`

```python
if mode == "circular":
    linear_seq = (f"{BSAI_SITE}{SPACER}{OVERHANG_FWD}"
                  f"{payload}"
                  f"{OVERHANG_REV}{SPACER}{BSAI_REV}")
    # BSAI_SITE = "GGTCTC" (recognition site)
    # OVERHANG_FWD = "GTCA" (sticky end top)
    # OVERHANG_REV = "GTCA" (sticky end bottom)
```

---

## Step 5: Analysis & Output

Your software calculates:

```python
data = {
    'payload': payload,           # The core DNA
    'linear_seq': linear_seq,     # Full construct (with BsaI ends if circular)
    'gc_pct': (G+C) / length * 100,  # GC content
    'length': len(payload),       # Payload length (bp)
    'total_length': len(linear_seq),  # Including assembly components
    'primers': designed_primers,  # Forward & Reverse primers
    'probes': designed_probes     # TaqMan probes
}
```

---

---

# PART 2: PRIMER DESIGN WORKFLOW

## What is a PCR Primer?

A **primer** is a short DNA oligonucleotide (18-25bp) that:
- **Binds** to your template DNA (complementary base pairing)
- **Initiates** DNA synthesis by DNA polymerase
- **Defines** the boundaries of PCR amplification

```
DNA Template:  5'---[LEFT REGION]---[TARGET REGION]---[RIGHT REGION]---3'
                          ↑                                      ↑
                    Fwd Primer Binds                      Rev Primer Binds
```

---

## Step 1: Determine Primer Length Target

### Biological Principle: Melting Temperature (Tm)

The **Tm (melting temperature)** is the temperature at which 50% of DNA duplexes dissociate.

**Formula (for qPCR, salt-adjusted 350mM Na+):**
```
Tm = 81.5 + 16.6×log₁₀[Na⁺] + 41×(%GC) - 675/length
```

**Your Software Calculation:**
```python
def calculate_tm(seq):
    # For sequences < 14bp: Wallace Rule (simple)
    if len(seq) < 14:
        return (A+T)×2 + (G+C)×4
    
    # For longer sequences: Salt-adjusted formula
    else:
        na_conc = 0.35  # 350mM Na+ equivalent
        tm = (81.5 + 16.6*log10(na_conc) + 
              41*(G+C)/len + 
              - 675/len)
        return tm
```

**Biological Goal: Tm = 60°C (standard PCR)**
- Too low Tm (<55°C) → primers bind weakly → no amplification
- Too high Tm (>65°C) → off-target binding → contamination
- Tm 60-64°C → optimal PCR conditions

---

## Step 2: Find Forward Primer Candidates (5' End)

### Biological Context
The **forward primer** must:
- Bind to the **5' end** of your target (ensures you capture the start)
- Allow full-length amplification
- Have optimal Tm (60°C ± 5°C)

### Your Software Strategy

```
Target DNA: 5'---[GCCTAGCATGCAT...ATCGATCGTA]---3'
                    ↑ Must start HERE (or very close)
            Forward primer binds here
```

**Algorithm:**
```python
# Search only near the 5' start region
for primer_length in range(18, 26):  # Try 18-25bp
    candidate = target[0:primer_length]  # Always start at position 0
    
    tm = calculate_tm(candidate)
    gc = calculate_gc(candidate)
    
    # Check if candidate meets criteria
    if 55 <= tm <= 65 and 40 <= gc <= 60:
        fwd_candidates.append({
            'seq': candidate,
            'tm': tm,
            'gc': gc,
            'len': primer_length
        })
```

**Why start at position 0?**
- You want to amplify from the very beginning
- If you start at position 100, you lose the first 100bp!

---

## Step 3: Find Reverse Primer Candidates (3' End)

### Biological Context
The **reverse primer** must:
- Bind to the **reverse complement** of the 3' end
- Ensure the PCR product is the desired length
- Have Tm matching the forward primer (within 5°C)

### Your Software Strategy

```
Target DNA (5'->3'): ...ATCGATCGATCGTAGGC
Complement (3'<-5'): ...TAGCTAGCTAGCATCCG

Reverse primer is the reverse-complement of the 3' end:
Written 5'->3': GCCTAGCTAGCTAGCAT
                 (This is what you order from the synthesizer)
```

**Algorithm:**
```python
seq_len = len(target)

for primer_length in range(18, 26):
    # Extract the 3' end region
    start_idx = seq_len - primer_length  # E.g., 500-20 = 480
    subseq = target[start_idx:seq_len]   # Bases 480-500
    
    # Convert to reverse-complement (this is the primer)
    candidate_rc = reverse_complement(subseq)
    
    tm = calculate_tm(candidate_rc)
    gc = calculate_gc(candidate_rc)
    
    if 55 <= tm <= 65 and 40 <= gc <= 60:
        rev_candidates.append({
            'seq': candidate_rc,
            'tm': tm,
            'gc': gc,
            'pos': start_idx
        })
```

**Result:**
- PCR product size = `(reverse_primer_pos + reverse_primer_len) - forward_primer_pos`
- Example: If Fwd at 0 and Rev at 480, product = 480bp (full sequence amplified)

---

## Step 4: Screen for Secondary Structures

### Biological Problem: Self-Dimerization

Primers can form **dimers** (two primers stick together) instead of binding to the template:

```
PROBLEM (Primer Dimer):
    Fwd Primer: 5'-ATGCTAGC-3'
                     ||||
    Rev Primer: 3'-TACGATCG-5'
    
    They bind to each other! → No template amplification → PCR fails
```

### Your Software Checks

#### Check 1: Hairpin Formation
```python
def check_hairpin(seq, min_stem=3):
    # Hairpins: A primer folds back on itself
    # Example: 5'-ATGC...GCAT-3'
    #            ||||   ||||
    #          (ATGC complementary to GCAT)
    
    for stem_len in range(3, len(seq)//2):
        for loop in range(3, 8):  # 3-8bp loop
            left = seq[:stem_len]
            right = seq[loop:loop+stem_len]
            
            if left == reverse_complement(right):
                return True  # ✗ Hairpin found!
    return False  # ✓ No hairpin
```

**Why it matters:**
- Hairpins reduce primer availability → weak PCR
- Hairpin melts at lower temp → non-specific binding

#### Check 2: Self-Dimer Check
```python
def check_self_dimer(seq):
    # Two primer molecules binding end-to-end
    rc = reverse_complement(seq)
    
    # Check if 3' end complements with reverse-complement
    three_prime = seq[-6:]
    
    if three_prime in rc:
        return True  # ✗ Can form self-dimer
    return False  # ✓ Safe
```

#### Check 3: Primer-Dimer Formation (Fwd + Rev)
```python
def check_primer_dimer(fwd_seq, rev_seq):
    # Forward and reverse primers stick to each other
    fwd_3prime = fwd_seq[-6:]  # Last 6bp of forward
    rev_3prime = rev_seq[-6:]  # Last 6bp of reverse
    rev_rc = reverse_complement(rev_seq)
    
    # If forward 3' matches reverse complement anywhere
    if fwd_3prime in rev_rc:
        return True  # ✗ Will form dimer
    return False  # ✓ Safe pairing
```

---

## Step 5: 3' End Stability (GC Clamp)

### Biological Principle

The **3' end** (the end with the -OH group) is where DNA polymerase adds nucleotides. If it's unstable, it dissociates and polymerase falls off.

```
Primer 3' End Stability:
✓ GOOD:    ...GC (G-C base pairs = 3 H-bonds = strong)
✗ BAD:     ...AT (A-T base pairs = 2 H-bonds = weak)
✗ WORSE:   ...T  (T alone = extremely weak)
```

### Your Software Check

```python
def check_3prime_stability(seq):
    last_5 = seq[-5:]
    last_base = seq[-1]
    score = 5  # baseline
    
    # Bonus for G/C at 3' end
    if last_base in ['G', 'C']:
        score += 2  # ✓ Stable
    elif last_base == 'T':
        score -= 2  # ✗ Weak
    
    # Penalty for too many G/C (>3 in last 5)
    gc_count = last_5.count('G') + last_5.count('C')
    if gc_count >= 4:
        score -= 2  # Might cause secondary structures
    
    return max(0, min(10, score))
```

---

## Step 6: Score and Rank Primer Candidates

### Your Software Scoring System

```python
def score_primer(seq, target_tm=60.0):
    score = 100  # Start perfect
    
    tm = calculate_tm(seq)
    gc = calculate_gc(seq)
    
    # Penalty for Tm deviation
    tm_diff = abs(tm - 60.0)
    score -= tm_diff * 2  # Each °C off = -2 points
    
    # Penalty for GC content
    if gc < 40:
        score -= (40 - gc) * 0.5  # Too AT-rich
    elif gc > 60:
        score -= (gc - 60) * 0.5  # Too GC-rich
    
    # Penalty for homopolymer runs
    if has_runs(seq, 4):
        score -= 15  # ✗ Bad
    if has_runs(seq, 3):
        score -= 5   # ✗ Suboptimal
    
    # Penalty for hairpins
    if check_hairpin(seq):
        score -= 20  # ✗ Major problem
    
    # Penalty for self-dimers
    if check_self_dimer(seq):
        score -= 15  # ✗ Major problem
    
    # Bonus for 3' stability
    stability = check_3prime_stability(seq)
    score += (stability - 5) * 2
    
    # Bonus for ideal length (20-22bp)
    if 20 <= len(seq) <= 22:
        score += 3  # ✓ Sweet spot for PCR
    
    return score
```

**Example Scoring:**
```
Candidate 1: ATGCTAGCCGATCGATCGTA (20bp, Tm=60°C, GC=50%)
  ✓ Tm deviation: 0°C (-0 points)
  ✓ GC: 50% (-0 points)
  ✓ No runs (-0 points)
  ✓ No hairpin (-0 points)
  ✓ 3' stable (+4 points)
  ✓ Ideal length (+3 points)
  = Score: 107/100 (Excellent!)

Candidate 2: AAAAAAAAATGCTAGCCGAT (20bp, Tm=52°C, GC=40%)
  ✗ Tm deviation: 8°C (-16 points)
  ✗ Homopolymer run: AAAAAAAAA (-15 points)
  ✓ No hairpin (-0 points)
  = Score: 69/100 (Poor)
```

---

## Step 7: Find Best Primer Pair

### Biological Requirement: Tm Matching

The forward and reverse primers must have **similar Tm** (within 5°C) for efficient PCR:

```
PCR Cycle Temperature Program:
1. Denature: 94°C (separate DNA strands)
2. Anneal: Tm°C (primers bind to template)
3. Extend: 72°C (polymerase adds nucleotides)

If Tm_fwd = 64°C and Tm_rev = 54°C:
  → At 64°C, fwd binds but rev doesn't → uneven amplification
  → At 54°C, rev binds but fwd dissociates → uneven amplification
  Result: Asymmetric PCR (biased towards one strand)
```

### Your Software Algorithm

```python
best_pair = None
best_score = -999

# Check top forward and reverse candidates
for fwd in fwd_candidates[:20]:  # Top 20
    for rev in rev_candidates[:20]:
        
        # Requirement 1: Tm within 5°C
        tm_diff = abs(fwd['tm'] - rev['tm'])
        if tm_diff > 5:
            continue  # ✗ Skip
        
        # Requirement 2: No primer-dimer formation
        if check_primer_dimer(fwd['seq'], rev['seq']):
            continue  # ✗ Skip
        
        # Requirement 3: Sensible product size
        product_size = (rev['pos'] + rev['len']) - fwd['pos']
        if product_size < 20:
            continue  # ✗ Skip (too small)
        
        # Calculate pair score
        pair_score = (fwd['score'] + rev['score'] - tm_diff*2)
        
        if pair_score > best_score:
            best_score = pair_score
            best_pair = (fwd, rev, product_size)

return {
    'fwd': best_pair[0],
    'rev': best_pair[1],
    'product_size': best_pair[2],
    'tm_difference': abs(fwd['tm'] - rev['tm'])
}
```

---

## Step 8: Cloning Primers (Optional - Restriction Enzymes)

### What is a Cloning Primer?

A **cloning primer** adds extra sequences to enable **restriction enzyme digestion**:

```
Standard PCR Primer:
5'---[ATGCTAGCCGATCGATCGTA]---3'  (20bp annealing region)

Cloning PCR Primer:
5'---[GCGC]-[GGTCTC]-[ATGCTAGCCGATCGATCGTA]---3'
      ^^^^   ^^^^^^  ^^^^^^^^^^^^^^^^^^^^
     Clamp  BsaI    Annealing Region
```

### Purpose

1. **Clamp** (GCGC): Helps DNA polymerase
2. **Enzyme Site** (GGTCTC for BsaI): Gets cut after PCR
3. **Annealing Region**: Binds to template → amplification

### Biological Process

```
Before PCR:
Template: ---[LEFT]---[Target]---[RIGHT]---
           ↑ Fwd primer with BsaI    ↑ Rev primer with BsaI

After PCR Amplification:
PCR Product: [CLAMP][BSAI][TARGET][BSAI][CLAMP]
                              (500bp)

After BsaI Digestion:
    X   [STICKY]---[TARGET]---[STICKY]   X
Cut off   (GTCA)   (500bp)   (TGAC)   Cut off
      
Result: Fragment with defined sticky ends
        Ready for Golden Gate ligation!
```

---

---

# PART 3: PROBE DESIGN WORKFLOW

## What is a qPCR Probe?

A **qPCR probe** is a short DNA or RNA sequence (18-28bp) that:
- **Hybridizes** to the PCR amplicon (the target product)
- **Reports** in real-time when PCR product accumulates
- **Stops** from fluorescing until it hybridizes (key feature!)

**Common Type: TaqMan Probe**
```
5'---[Reporter Dye]---[Probe Sequence]---[Quencher Dye]---3'
      (e.g., FAM)      (18-28bp)        (e.g., TAMRA)

When free:
  Reporter & Quencher are close → No fluorescence (quenched)

When bound to PCR product:
  Taq polymerase cuts the reporter off probe
  Reporter far from Quencher → Fluorescence!
  
This allows real-time PCR monitoring!
```

---

## Why Multiple Probes?

Your software designs **4 independent probes** from different regions:

```
[Probe 1]   [Spacer]   [Probe 2]   [Spacer]   [Probe 3]   [Spacer]   [Probe 4]
   ↓                      ↓                      ↓                      ↓
Region 1               Region 2               Region 3               Region 4

Benefits:
- Redundancy: If one probe fails, others still work
- Validation: All probes should amplify equivalently
- Authenticity: Forensic "fingerprint" with 4-point validation
```

---

## Step 1: Determine Probe Length and Count

### Biological Principle: Tm and Specificity

**Probe Tm requirements (qPCR):**
- Target Tm: **68-72°C** (higher than primers!)
- Why? Probes must be stable on the PCR product
- Tm = 70°C ± 2°C is ideal for TaqMan assays

**Length vs. Tm Relationship:**
```
Longer probe → Higher Tm → More stable but harder to synthesize
Shorter probe → Lower Tm → Easier to synthesize but less specific

Your software adapts:
```python
if target_payload < 150bp:
    probe_length = 18  # Short & simple
elif target_payload < 300bp:
    probe_length = 20  # Moderate
elif target_payload < 600bp:
    probe_length = 22  # Standard
else:
    probe_length = 24  # Long & very specific
```

**Probe Count:**
```python
# How many probes can fit?
if primer_length + (4 probes × probe_length) + spacers < remaining_space:
    num_probes = 4  # Maximum
elif (3 probes × probe_length) + spacers < remaining_space:
    num_probes = 3
elif (2 probes × probe_length) + spacers < remaining_space:
    num_probes = 2
else:
    num_probes = 1
```

---

## Step 2: Generate De Novo Probes (Ideal Synthesis)

### Strategy: Create Perfect Probes from Scratch

Instead of finding probes in the sequence, your software can **generate synthetic probes** with perfect specifications:

```python
def generate_ideal_probes(num_probes=4, length=24):
    """
    Creates absolutely perfect probes with:
    - Zero secondary structures
    - Balanced base composition
    - Exact Tm specifications
    - Proper 3' stability
    """
```

---

## Step 3: Tier-1 STRICT Probe Design (From Sequence)

### Biological Requirements

#### Requirement 1: No 5' G (Quencher Interference)

```
TaqMan Probe Structure:
5'---[FAM Reporter]---[Probe Seq]---[TAMRA Quencher]---3'

If 5' base is G:
  5'-[FAM]---G---...---[TAMRA]---3'
     Guanine is near FAM
     G can quench FAM fluorescence!
     Result: No signal even when probe is free

Solution: Ensure first base is A, T, or C (not G)
```

#### Requirement 2: GC Clamp at 3' End

```
Probe 3' end stability:
✓ GOOD: ...GC (strong H-bonds)
✓ GOOD: ...GG (very stable, but avoid strong homopolymers)
✗ BAD:  ...AT (weak H-bonds)
✗ BAD:  ...T  (single base, very weak)

Your software requires: Last 2-3 bases include ≥2 G/C
```

#### Requirement 3: GC Content (45-60%)

```
Why 45-60% for probes (not 40-60%)?
- Probes are shorter (18-28bp) → narrower optimal range
- Too much A/T → Tm too low → specificity lost
- Too much G/C → Tm too high → hard to synthesize

Calculation:
gc_percent = (count_G + count_C) / length * 100
if 45 <= gc_percent <= 60:
    ✓ PASS
```

#### Requirement 4: Melting Temperature (68-72°C for STRICT)

```python
tm = calculate_tm(probe_seq)

# For STRICT tier (ideal production)
if 68 <= tm <= 72:
    ✓ PASS - Perfect for qPCR

# Why 68-72°C?
# - PCR annealing typically 60°C (lower)
# - Probes sit on double-stranded PCR product at ~72°C extension
# - Probe must stay bound: 68-72°C provides safety margin
```

#### Requirement 5: No Homopolymer Runs (≤3)

```
Polymerase slippage on runs:
...AAAA... → Polymerase might add extra A's
Result: Off-target amplification

Your software check for STRICT mode:
if has_runs(probe_seq, max_run=3):
    ✗ FAIL - Too many consecutive bases
```

#### Requirement 6: No Hairpins (Minimum 3bp stem)

```
Hairpin formation:
5'-ATGC...GCAT-3'
    ||||   ||||
  (Forms loop, reduces availability)

Check: Does first Xbp = reverse_complement of Ybp?
if yes → ✗ Hairpin detected

For STRICT mode: min_stem ≥ 3bp
```

#### Requirement 7: No Self-Dimers (Minimum 5bp complementary)

```
Self-dimer: Two probe molecules stick together
5'-ATGCTAGC-3' + 5'-ATGCTAGC-3' → They ligate!
Result: Reduced probe availability

Check: Does probe pair with its reverse complement?
if yes → ✗ Self-dimer risk
```

---

## Step 4: Probe Quality Scoring

### Your Software Scoring System

```python
def check_probe_quality(seq):
    """Returns quality score 0-100"""
    score = 100
    issues = []
    
    # 1. Length check
    if len(seq) < 18:
        score -= 20  # Too short = reduced specificity
    elif len(seq) > 28:
        score -= 10  # Too long = hard to synthesize
    
    # 2. GC content
    gc = calculate_gc(seq)
    if gc < 40 or gc > 60:
        score -= 15  # Outside optimal range
    
    # 3. 3' end stability
    last_3 = seq[-3:]
    gc_count_3prime = last_3.count('G') + last_3.count('C')
    if gc_count_3prime < 2:
        score -= 15  # Weak 3' end
    
    # 4. 5' G check
    if seq[0] == 'G':
        score -= 10  # Quencher interference risk
    
    # 5. No homopolymer runs
    if has_runs(seq, 4):
        score -= 20  # Synthesis issue
    
    # 6. No hairpins
    if check_hairpin(seq, min_stem=3):
        score -= 25  # Structural issue
    
    # 7. No self-dimers
    if check_self_dimer(seq, min_complementary=5):
        score -= 20  # Dimerization risk
    
    # 8. Balanced composition
    at_pct = (seq.count('A') + seq.count('T')) / len(seq) * 100
    if at_pct > 70 or at_pct < 30:
        score -= 10  # Extreme bias
    
    return max(0, score)
```

**Scoring Example:**
```
Probe 1: ATGCTAGCCGATCGATCGTAGCC (22bp, Tm=70°C, GC=50%)
  ✓ Length: 22bp (ideal, +0 penalty)
  ✓ GC: 50% (-0)
  ✓ 3' end: GCC (strong, -0)
  ✓ 5' start: A (not G, -0)
  ✓ No runs (-0)
  ✓ No hairpins (-0)
  ✓ No self-dimers (-0)
  = Quality Score: 100/100 (Perfect!)

Probe 2: AAAAAATGCTAGCATGCT (18bp, Tm=62°C, GC=44%)
  ✗ Homopolymer run: AAAAAA (-20)
  ✗ Tm deviation: 8°C off optimal (-penalty)
  ✗ GC at 44% (below 45%, -penalty)
  = Quality Score: ~65/100 (Acceptable)
```

---

## Step 5: Tier-2 FLEXIBLE Probe Design

### When to Use: If STRICT didn't find enough probes

Your software **relaxes constraints** but maintains quality:

```python
# TIER 2: FLEXIBLE (Relaxed but high-quality)

# Length: Wider range (19-30bp instead of 20-28bp)
# Tm: Wider window (67-73°C instead of 68-72°C)
# GC: Wider range (38-62% instead of 45-60%)
# Homopolymer runs: Allow up to 5bp (instead of 4bp)
# Hairpin check: Softer stem requirement (4bp instead of 3bp)
# Self-dimers: Softer complementary requirement (6bp instead of 5bp)
# Quality threshold: ≥70% (instead of ≥75%)
```

---

## Step 6: Tier-3 EMERGENCY Probe Design

### When to Use: If FLEXIBLE still insufficient (rare sequences)

```python
# TIER 3: EMERGENCY (Very relaxed)

# Tm: Very wide window (65-75°C)
# GC: Extreme range (35-65%)
# Homopolymer runs: Allow up to 6bp
# Hairpin check: Very relaxed stem (5bp)
# Self-dimers: Extremely relaxed (7bp)
# Quality threshold: ≥60%
```

---

## Step 7: Region-Based Selection

### Strategy: Distribute Probes Across Sequence

Your software ensures probes don't cluster in one region:

```python
# Divide sequence into regions
region_size = sequence_length / num_probes

# Example: 500bp sequence, 4 probes
# Region 1: 0-125bp (Probe 1)
# Region 2: 125-250bp (Probe 2)
# Region 3: 250-375bp (Probe 3)
# Region 4: 375-500bp (Probe 4)

# For each region, pick the best non-overlapping probe
for region_idx in range(num_probes):
    region_start = region_idx * region_size
    region_end = (region_idx + 1) * region_size
    
    best_probe = None
    best_score = -999
    
    for candidate in candidates:
        # Ensure 50%+ overlap with region (not outside)
        if candidate_overlap >= 0.5 * region_size:
            if candidate_score > best_score:
                best_probe = candidate
                best_score = candidate_score
    
    if best_probe:
        selected.append(best_probe)
```

**Result:**
```
Selected Probes:
Probe 1: Position 50-72bp   (Region 1) ✓
Probe 2: Position 175-197bp (Region 2) ✓
Probe 3: Position 275-297bp (Region 3) ✓
Probe 4: Position 425-447bp (Region 4) ✓

Benefits:
- No redundancy (different regions)
- Full sequence coverage
- Forensic validation (must all amplify)
```

---

---

# COMPLETE WORKFLOW SUMMARY

## DNA Generation → Primer Design → Probe Design

```
┌─────────────────────────────────────────────────────────────────────┐
│                    USER REQUEST: 500bp DNA                          │
└─────────────────────────────────────────────────────────────────────┘
                                ↓

┌─────────────────────────────────────────────────────────────────────┐
│                    STEP 1: DNA GENERATION                           │
├─────────────────────────────────────────────────────────────────────┤
│ 1. Generate random 500bp payload                                    │
│ 2. Validate:                                                        │
│    ✓ No homopolymer runs > 5bp                                      │
│    ✓ GC content 40-60%                                              │
│    ✓ No BsaI sites (GGTCTC/GAGACC)                                  │
│ 3. Structure for primers/probes if needed                           │
│ 4. Assemble with Golden Gate ends (circular mode)                  │
│                                                                      │
│ OUTPUT: Linear construct (500bp → ~533bp with assembly ends)       │
└─────────────────────────────────────────────────────────────────────┘
                                ↓

┌─────────────────────────────────────────────────────────────────────┐
│                  STEP 2: PRIMER DESIGN                              │
├─────────────────────────────────────────────────────────────────────┤
│ 1. Find forward primer candidates (from 5' end)                     │
│    - Length range: 18-25bp                                          │
│    - Target Tm: 60°C ± 5°C                                          │
│    - GC: 40-60%                                                     │
│ 2. Find reverse primer candidates (from 3' end complement)          │
│ 3. Screen for secondary structures                                  │
│    ✓ No hairpins                                                    │
│    ✓ No self-dimers                                                 │
│    ✓ GC clamp at 3' end                                             │
│ 4. Score each candidate                                             │
│ 5. Find best pair (Tm match ±5°C, no primer-dimers)                │
│ 6. Add restriction enzyme sites if cloning mode                     │
│                                                                      │
│ OUTPUT: Fwd primer + Rev primer (product size ~500bp)              │
└─────────────────────────────────────────────────────────────────────┘
                                ↓

┌─────────────────────────────────────────────────────────────────────┐
│                  STEP 3: PROBE DESIGN                               │
├─────────────────────────────────────────────────────────────────────┤
│ 1. Determine probe length (18-28bp based on target size)            │
│ 2. Calculate max probe count based on available space               │
│ 3. Generate de novo ideal probes (if not in sequence)               │
│ 4. Search sequence with tiers:                                      │
│    - TIER 1 STRICT:    Tm 68-72°C, GC 45-60%, quality ≥75%         │
│    - TIER 2 FLEXIBLE:  Tm 67-73°C, GC 38-62%, quality ≥70%         │
│    - TIER 3 EMERGENCY: Tm 65-75°C, GC 35-65%, quality ≥60%         │
│ 5. Screen for:                                                      │
│    ✓ Not 5' G (quencher interference)                               │
│    ✓ GC clamp at 3' end                                             │
│    ✓ No homopolymer runs > 4bp                                      │
│    ✓ No hairpins (3bp stem)                                         │
│    ✓ No self-dimers (5bp complementary)                             │
│ 6. Distribute across regions (no clustering)                        │
│                                                                      │
│ OUTPUT: 4 TaqMan probes (different regions, Tm 68-72°C each)       │
└─────────────────────────────────────────────────────────────────────┘
                                ↓

┌─────────────────────────────────────────────────────────────────────┐
│                    FINAL DELIVERABLE                                │
├─────────────────────────────────────────────────────────────────────┤
│ ✓ DNA Construct (500bp circular plasmid)                            │
│ ✓ Forward Primer (20bp, Tm 60°C, ready to order)                   │
│ ✓ Reverse Primer (20bp, Tm 60°C, ready to order)                   │
│ ✓ 4 TaqMan Probes (22bp each, Tm 70°C, ready to order)             │
│ ✓ PCR Protocol (product size 500bp)                                │
│ ✓ qPCR Validation Method (4 probes for confirmation)               │
└─────────────────────────────────────────────────────────────────────┘
```

---

# REAL-WORLD APPLICATION: Forensic Authentication

## How Your Software Enables Track & Trace

```
MANUFACTURING STAGE:
  Product (e.g., medicine/luxury item)
              ↓
  Embed synthetic DNA construct into product packaging
  (Your software generates unique "genetic barcode")
              ↓

AUTHENTICATION STAGE:
  Customer/Retailer extracts DNA from packaging
              ↓
  PCR amplification using your software's primers
  (Amplifies 500bp construct)
              ↓
  qPCR detection using your software's 4 probes
  (All 4 probes should light up = authentic)
              ↓
  Optional: Sequence verification (BLAST comparison)
              ↓
  Result: AUTHENTIC ✓ or COUNTERFEIT ✗
```

---

## Key Advantages of Your Software's Approach

| Feature | Benefit |
|---------|---------|
| **Random DNA Generation** | Each construct is unique (impossible to counterfeit without access to original sequence) |
| **Golden Gate Assembly** | Compatible sticky ends ensure correct ligation order in real lab |
| **Matched Primers** | Efficient full-length amplification (no biased PCR) |
| **4 Independent Probes** | Redundancy + validation (multiple independent measurements) |
| **Quality Scoring** | Ensures probes will work reliably in real qPCR assays |
| **Region Distribution** | Probes span entire sequence (detects any degradation/tampering) |

---

This comprehensive guide explains exactly how your DNA Lab software follows real biological principles!

---

---

# PART 4: SOFTWARE TOOLS & USE CASES

## Overview: When and How to Use Each Tool

Your DNAₓ Lab application contains **8 specialized tools**. This section explains the purpose, workflow, and real-world applications for each.

---

# Tool 1: HOME PAGE

## Purpose
**Introductory dashboard** - Starting point for the application

## When to Use
- First time launching the application
- Getting oriented with the interface
- Accessing application documentation

## What It Shows
- Welcome message
- Application logo/branding
- Quick navigation tips

## Use Case Example
```
Scenario: User launches DNAₓ Lab for the first time
1. Application opens → Home Page displays
2. User sees logo and welcome message
3. User navigates to desired tool using left sidebar menu
```

---

---

# Tool 2: SIZE CALCULATOR

## Purpose
**Convert DNA length (bp) to physical dimensions**

## Biological Background
DNA has a standard **rise per base pair = 0.34 nm** (B-form DNA)

## When to Use

### Use Case 1: Planning Physical DNA Storage
```
Scenario: You want to know the size of your DNA construct
1. Enter: 500 bp  
2. Output: 
   - Linear length: 170 nm (0.17 µm, 0.00017 mm)
   - Circular diameter: 54 nm (0.054 µm, 0.000054 mm)
   
Purpose: Understand if your DNA can fit in nanoscale containers
```

### Use Case 2: Estimating Molecular Weight
```
Scenario: You need molecular weight for cloning calculations
1. Enter: 1000 bp
2. Output:
   - Molecular weight: ~660 kDa (660,000 Daltons)
   - Average mass per base: 330 Da
   
Purpose: Calculate plasmid concentration for lab work
```

### Use Case 3: Pre-filling DNA Generator
```
Scenario: You calculated ideal DNA size, now want to generate it
1. Use Size Calculator to find optimal bp
2. Click "Use in DNA Generator →"
3. DNA Generator automatically pre-fills the bp value
4. Proceed to generate sequence

Purpose: Streamlined workflow between related tools
```

## Workflow
```
┌─────────────────────────────────┐
│  User Enters Base Pair Count    │
│  (e.g., 500 bp)                 │
└────────────┬────────────────────┘
             ↓
┌─────────────────────────────────┐
│  Software Calculates:            │
│  - Linear length (nm/µm/mm)      │
│  - Circular diameter             │
│  - Molecular weight              │
└────────────┬────────────────────┘
             ↓
┌─────────────────────────────────┐
│  User Can:                       │
│  1. Copy results                 │
│  2. Jump to DNA Generator        │
│  3. Note dimensions for project  │
└─────────────────────────────────┘
```

---

---

# Tool 3: DNA GENERATOR

## Purpose
**Create unique synthetic DNA constructs for forensic authentication**

## When to Use

### Use Case 1: Forensic Track & Trace (Primary Use)
```
Scenario: Manufacturer wants to embed DNA barcode in products
1. Select DNA length: 500 bp (common for pharmaceuticals)
2. Choose mode: CIRCULAR (for Golden Gate Assembly)
3. Choose primer type: SPECIFIC (de novo) or UNIVERSAL (provided)
4. Click "Generate Sequence"
5. Output: 
   - Unique DNA construct
   - PCR primers (ready to synthesize)
   - 4 qPCR probes (for validation)
   
Real-world application: 
→ Add DNA sequence to product packaging
→ Customers can verify authenticity with PCR/qPCR
```

### Use Case 2: Quality Control Database Building
```
Scenario: You want to build a reference database of authentic DNA
1. Generate 100 different DNA constructs (100 bp each)
2. Export all primers and probes
3. Store in database
4. Later: Compare customer samples against database using COMPARATOR
5. Matches → Authentic ✓ | No matches → Counterfeit ✗
```

### Use Case 3: Linear DNA for Direct PCR
```
Scenario: You want simple DNA without assembly complexity
1. Select DNA length: 300 bp
2. Choose mode: LINEAR
3. Generate
4. Output: Simple linear sequence without BsaI ends
5. Use directly in PCR (no assembly step needed)
```

## Workflow

```
                    ┌─── INPUT PARAMETERS ───┐
                    │ • DNA Length (bp)      │
                    │ • Mode (Linear/Circular)│
                    │ • Primer Type          │
                    └────────┬────────────────┘
                             ↓
        ┌────────────────────────────────────────────────┐
        │ STEP 1: Generate Random Payload               │
        │ • Create 300-500bp random sequence            │
        │ • Enforce no homopolymer runs                 │
        ├────────────────────────────────────────────────┤
        │ STEP 2: Validate Constraints                  │
        │ • Check GC content (40-60%)                   │
        │ • Remove BsaI sites                           │
        │ • Verify no problematic structures            │
        └────────────┬─────────────────────────────────┘
                     ↓
        ┌────────────────────────────────────────────────┐
        │ STEP 3: Add Functional Elements               │
        │ • Primer binding sites (if needed)            │
        │ • Probe binding regions                       │
        │ • Spacer sequences                            │
        └────────────┬─────────────────────────────────┘
                     ↓
        ┌────────────────────────────────────────────────┐
        │ STEP 4: Assemble Final Construct              │
        │ • Linear: Direct output                       │
        │ • Circular: Add BsaI sites & sticky ends      │
        └────────────┬─────────────────────────────────┘
                     ↓
        ┌────────────────────────────────────────────────┐
        │ STEP 5: Design Primers & Probes               │
        │ • Find optimal PCR primers (Tm matching)      │
        │ • Design 4 qPCR probes (region-distributed)   │
        │ • Quality score all designs                   │
        └────────────┬─────────────────────────────────┘
                     ↓
                 ┌─── OUTPUTS ───┐
                 │ • DNA sequence │
                 │ • Fwd primer   │
                 │ • Rev primer   │
                 │ • 4 probes     │
                 └────────────────┘
```

## Real-World Lab Protocol (After Generation)

### Scenario: Manufacturing DNA-Tagged Medication

```
STEP 1: SOFTWARE OUTPUT (Your DNAₓ Lab)
        DNA: 5'-ATGCTAGCCGATCGATCGTA...-3' (500bp)
        Fwd Primer: ATGCTAGCCGATCGATCGTA (20bp, Tm=60°C)
        Rev Primer: TAACGATCGATCGCTAGCGC (20bp, Tm=60°C)
        Probes: 4 different TaqMan probes

STEP 2: SYNTHESIS (Outside Lab)
        • Order DNA sequence from commercial synthesizer
        • Order primers from PCR primer supplier
        • Order probes from probe synthesizer
        • Receive: 100 µg DNA, 10 nmol primers, probes

STEP 3: EMBEDDING (Manufacturing)
        • Incorporate DNA into product packaging
        • (e.g., print on sticker, embed in ink)
        • Package product normally

STEP 4: QUALITY CONTROL (At warehouse)
        • Extract DNA from sample packages
        • Run PCR with primers → Amplify 500bp product
        • Run qPCR with 4 probes → Measure fluorescence
        • All 4 probes signal = AUTHENTIC ✓

STEP 5: END-USER VERIFICATION
        • Customer suspects counterfeit
        • Sends to authentication lab
        • Lab repeats Steps 4
        • Compare DNA sequence to manufacturer's database
        • Authentic or Counterfeit determined!
```

---

---

# Tool 4: COMPARATOR (BLAST Search)

## Purpose
**Search your DNA sequence against NCBI database to verify uniqueness/check for contamination**

## Biological Background
**BLAST** = Basic Local Alignment Search Tool
- Compares your sequence against millions of known sequences
- Returns natural matches vs synthetic/vector matches

## When to Use

### Use Case 1: Verify Uniqueness (Primary Use)
```
Scenario: You want to ensure your DNA doesn't accidentally match nature
1. Input your DNA sequence (500 bp)
2. Click "Run BLAST Scan"
3. Results show:
   - Natural matches (environmental DNA)
   - Synthetic matches (lab vectors/constructs)
4. Goal: No exact matches found!
   ✓ PASS = Your DNA is unique = Good for forensics
   ✗ FAIL = Your DNA matches existing sequence = Not unique
```

### Use Case 2: Contamination Detection
```
Scenario: Your PCR product doesn't amplify as expected
1. Sequence the product
2. Use COMPARATOR to search
3. Results show unexpected matches
   → Reveals contamination source
   → Explains why experiment failed
```

### Use Case 3: Design Primers for Existing Genes
```
Scenario: You want to amplify a natural gene (not synthetic)
1. Get gene sequence (e.g., SARS-CoV-2 spike protein)
2. Run BLAST to confirm it matches known sequences
3. Use results to validate sequence identity
4. Then use DNA GENERATOR to design primers
```

## Workflow

```
┌──────────────────────────────────┐
│ User Enters DNA Sequence         │
│ (Paste sequence or upload file)  │
└────────────┬─────────────────────┘
             ↓
┌──────────────────────────────────────────────────────────┐
│ SOFTWARE SUBMITS TO NCBI BLAST                          │
│ • Connects to live BLAST server                         │
│ • Sends sequence + parameters                           │
│ • Waits for results (1-2 minutes)                       │
└────────────┬─────────────────────────────────────────────┘
             ↓
┌──────────────────────────────────────────────────────────┐
│ RESULTS CATEGORIZATION                                  │
│ LEFT COLUMN: Natural/Genomic Matches                    │
│ RIGHT COLUMN: Synthetic/Vector Matches                  │
│ TOP BANNER: Uniqueness Summary (PASS/FAIL)             │
└────────────┬─────────────────────────────────────────────┘
             ↓
┌──────────────────────────────────────────────────────────┐
│ USER ANALYSIS                                           │
│ • Identify exact matches                                │
│ • Review e-values (lower = more significant)            │
│ • Check match % (100% = exact match)                    │
│ • Draw conclusions about sequence origin                │
└──────────────────────────────────────────────────────────┘
```

## Results Interpretation

```
SCENARIO 1: UNIQUE SEQUENCE (Good for DNA Barcoding)
└─ ✅ Sequence Appears Unique
   └─ No 100% matches found
   └─ Partial matches are noise
   └─ Suitable for forensic authentication

SCENARIO 2: EXACT MATCH FOUND (Problem for DNA Barcoding)
└─ ⚠️ Exact Matches Found (5 matches)
   └─ Your sequence already exists
   └─ Not unique!
   └─ Regenerate new DNA construct

SCENARIO 3: PARTIAL MATCHES (Usually OK)
└─ Sequence has some similarity to known DNA
   └─ But not exact matches
   └─ Suitable for forensic use (highly specific)
```

---

---

# Tool 5: PRIMER DESIGNER

## Purpose
**Design or refine PCR primers for amplifying your DNA**

## When to Use

### Use Case 1: Refine DNA Generator Primers
```
Scenario: DNA Generator created primers, but you want manual control
1. Go to PRIMER DESIGNER
2. Paste your sequence
3. Software finds alternative primer options
4. You can select different:
   - Primer length (18-25 bp)
   - Position in sequence
   - Tm matching priority
5. Export custom primer pair
```

### Use Case 2: Design Primers for BLAST Hit
```
Scenario: COMPARATOR found matching sequence, want to amplify it
1. Get the matching sequence from BLAST results
2. Paste into PRIMER DESIGNER
3. Software designs primers for that specific gene
4. Export primers for PCR
```

### Use Case 3: Cloning Primers (Advanced)
```
Scenario: You want to add restriction sites for assembly
1. Select primer type: CLONING (not standard)
2. Choose enzymes:
   - 5' end: BsaI
   - 3' end: BamHI
3. Software adds enzyme recognition sites to primers
4. Result: Primers with sticky ends for ligation
```

## Workflow

```
┌─────────────────────────────────┐
│ Paste Target Sequence           │
│ (DNA to amplify)                │
└────────────┬────────────────────┘
             ↓
┌────────────────────────────────────────┐
│ STEP 1: Find Forward Primer Candidates │
│ • Search 5' end region                 │
│ • Try lengths 18-25 bp                 │
│ • Calculate Tm for each                │
│ • Keep candidates: Tm 55-65°C, GC 40-60%
└────────────┬───────────────────────────┘
             ↓
┌────────────────────────────────────────┐
│ STEP 2: Find Reverse Primer Candidates│
│ • Search 3' end region (reverse-comp)  │
│ • Try lengths 18-25 bp                 │
│ • Calculate Tm for each                │
│ • Keep candidates: Tm 55-65°C, GC 40-60%
└────────────┬───────────────────────────┘
             ↓
┌────────────────────────────────────────┐
│ STEP 3: Screen for Problems            │
│ • Check for hairpins                   │
│ • Check for self-dimers                │
│ • Check 3' stability (GC clamp)        │
│ • Eliminate bad candidates             │
└────────────┬───────────────────────────┘
             ↓
┌────────────────────────────────────────┐
│ STEP 4: Score Remaining Candidates     │
│ • Calculate quality score (0-100)      │
│ • Higher score = better primer         │
│ • Rank all candidates                  │
└────────────┬───────────────────────────┘
             ↓
┌────────────────────────────────────────┐
│ STEP 5: Find Best Pair                 │
│ • Forward + Reverse must have:         │
│   - Tm within 5°C (e.g., 60°C ± 5°C)  │
│   - No primer-dimers                   │
│   - Good individual scores             │
│ • Return top-scoring pair              │
└────────────┬───────────────────────────┘
             ↓
┌────────────────────────────────────────┐
│ OUTPUTS                                │
│ • Fwd Primer (ready to order)          │
│ • Rev Primer (ready to order)          │
│ • Product size (bp)                    │
│ • Tm for each                          │
│ • Quality scores                       │
└────────────────────────────────────────┘
```

---

---

# Tool 6: qPCR ANALYSIS (Probe Designer & Validation)

## Purpose
**Design TaqMan probes for real-time PCR detection**

## When to Use

### Use Case 1: Validate DNA Generator Output
```
Scenario: DNA Generator created probes, want to review
1. DNA Generator already created 4 probes
2. Go to qPCR ANALYSIS
3. Review:
   - Probe sequences
   - Tm values (should be 68-72°C)
   - Quality scores (should be >75)
   - Regional distribution
```

### Use Case 2: Design Probes for Custom Sequence
```
Scenario: You have your own DNA sequence, want probes
1. Paste sequence into qPCR ANALYSIS
2. Software designs 4 independent probes
3. Probes distributed across sequence regions
4. All probes scored for quality
5. Export probes for synthesis
```

### Use Case 3: Forensic Validation
```
Scenario: You extracted DNA from suspect product
1. Amplify with PRIMER DESIGNER primers → PCR product
2. Run qPCR with probes from qPCR ANALYSIS
3. If all 4 probes signal = Authentic ✓
4. If fewer than 4 signal = Counterfeit ✗
```

## Workflow

```
┌─────────────────────────────────────────┐
│ Input DNA Sequence (from DNA Generator) │
└────────────┬────────────────────────────┘
             ↓
┌─────────────────────────────────────────────────────────┐
│ TIER 1: STRICT SEARCH                                   │
│ • Look for perfect probes                               │
│ • Requirements: Tm 68-72°C, GC 45-60%, quality ≥75%   │
│ • Screen for secondary structures                       │
│ • If found 4+ probes → Done!                           │
└────────────┬────────────────────────────────────────────┘
             ↓ (If <4 probes found)
┌─────────────────────────────────────────────────────────┐
│ TIER 2: FLEXIBLE SEARCH                                 │
│ • Relax constraints slightly                            │
│ • Requirements: Tm 67-73°C, GC 38-62%, quality ≥70%   │
│ • More lenient structural checks                        │
│ • If found 4+ probes → Done!                           │
└────────────┬────────────────────────────────────────────┘
             ↓ (If <4 probes found)
┌─────────────────────────────────────────────────────────┐
│ TIER 3: EMERGENCY SEARCH                                │
│ • Very relaxed constraints                              │
│ • Requirements: Tm 65-75°C, GC 35-65%, quality ≥60%   │
│ • Minimal structural requirements                       │
│ • Should find probes for almost any sequence            │
└────────────┬────────────────────────────────────────────┘
             ↓
┌─────────────────────────────────────────────────────────┐
│ STEP 4: REGION-BASED DISTRIBUTION                       │
│ • Divide sequence into 4 regions                        │
│ • Pick best probe from each region                      │
│ • Ensure no overlaps or clustering                      │
└────────────┬────────────────────────────────────────────┘
             ↓
┌─────────────────────────────────────────────────────────┐
│ OUTPUTS                                                 │
│ • Probe 1: Position 50-72bp, Tm 70°C, Score 95        │
│ • Probe 2: Position 150-172bp, Tm 70°C, Score 92      │
│ • Probe 3: Position 250-272bp, Tm 71°C, Score 94      │
│ • Probe 4: Position 350-372bp, Tm 69°C, Score 93      │
└─────────────────────────────────────────────────────────┘
```

## Real-World qPCR Workflow

```
SAMPLE PREPARATION
1. Extract DNA from product
2. Store in qPCR buffer

qPCR SETUP
1. Add sample DNA to qPCR tube
2. Add primers (Fwd + Rev) → PCR amplification
3. Add probes (from qPCR ANALYSIS) → Detection
4. Add qPCR master mix (with Taq polymerase)

qPCR RUNNING (30-40 cycles)
Cycle 1: Denature (94°C) → Separate DNA strands
Cycle 2: Anneal (60°C) → Primers bind
Cycle 3: Extend (72°C) → Polymerase adds nucleotides
         During extension, probes bind & fluoresce

RESULTS (After ~40 cycles)
If all 4 probes amplified:
    ✅ AUTHENTIC (All genetic markers present)
If 1-3 probes amplified:
    ❌ COUNTERFEIT or DEGRADED (Markers missing)
If 0 probes amplified:
    ❌ WRONG PRODUCT (No target DNA detected)
```

---

---

# Tool 7: EXPORT

## Purpose
**Export generated DNA data in professional formats (Excel, PDF, Cloud)**

## When to Use

### Use Case 1: Generate Lab-Ready Report (Excel)
```
Scenario: Need to document all design parameters
1. Click "Export to Excel (.xlsx)"
2. Choose save location
3. Output contains 4 sheets:
   - Summary (metadata, timestamps)
   - Sequences (full DNA, primers, probes)
   - Primers (detailed metrics)
   - Probes (quality scores, positions)
4. Use for lab records / ISO documentation
```

### Use Case 2: Create Professional Documentation (PDF)
```
Scenario: Need formatted report for stakeholders
1. Click "Export to PDF (.pdf)"
2. Software generates:
   - Custom QR code (unique ID for tracking)
   - Professional formatting
   - All design data
   - Summary tables
   - Circular plasmid visualization
3. Print or email to clients
```

### Use Case 3: Upload to Cloud Database
```
Scenario: Build central archive of DNA designs
1. Click "Save to Cloud ☁"
2. Select company/project from dropdown
3. Software uploads to Firebase with:
   - Timestamp
   - Batch number
   - All design parameters
   - Unique ID tracking
4. Accessible from any location
```

## Export Contents

### Excel Export
```
SHEET 1: SUMMARY
├─ DNA Construct Report
├─ Generated On: 2026-06-03 14:23:00
├─ Mode: Circular
├─ Payload Length: 500 bp
├─ Total Length: 533 bp

SHEET 2: SEQUENCES
├─ Payload (500 bp): ATGCTAGCCGATCGATCGTA...
├─ Payload Complement: TACGATCGGCTAGCTAGCTT...
├─ Full Linear Construct (533 bp): [Full sequence]

SHEET 3: PRIMERS
├─ Forward Primer: ATGCTAGCCGATCGATCGTA
│  ├─ Tm: 60.0°C
│  ├─ GC: 50%
│  ├─ Length: 20 bp
│  ├─ Score: 95/100
├─ Reverse Primer: TAACGATCGATCGCTAGCGC
│  ├─ Tm: 60.0°C
│  ├─ GC: 50%
│  ├─ Length: 20 bp
│  ├─ Score: 94/100

SHEET 4: PROBES
├─ Rank 1: ATGCTAGCCGATCGATCGTAGCC
│  ├─ Tm: 70.1°C | GC: 50% | Len: 22 | Score: 95
├─ Rank 2: TACGATCGATCGATCGATCGTA
│  ├─ Tm: 69.9°C | GC: 50% | Len: 22 | Score: 93
├─ Rank 3: GATCGATCGATCGATCGATCGTA
│  ├─ Tm: 70.0°C | GC: 50% | Len: 23 | Score: 94
├─ Rank 4: CGTAGCTAGCTAGCTAGCTAGC
│  ├─ Tm: 70.2°C | GC: 52% | Len: 22 | Score: 92
```

### PDF Export
```
PAGE 1:
├─ Header: "DNAₓ Construct Report"
├─ Timestamp & Unique ID (with QR code)
├─ Summary table
│  ├─ Mode: Circular
│  ├─ Payload Length: 500 bp
│  ├─ GC Content: 50%
│  ├─ Status: Circularized

PAGE 2:
├─ Primers Section
│  ├─ Forward Primer: [sequence] (20bp, Tm 60°C)
│  ├─ Reverse Primer: [sequence] (20bp, Tm 60°C)
│  ├─ PCR Product: 500 bp
├─ Probes Section (Top 5)
│  ├─ Probe 1: [sequence] (Tm 70°C, Quality 95)
│  ├─ [Additional probes...]

PAGE 3:
├─ Full Circular Sequence
│  ├─ Wrapped for readability
│  ├─ Color-coded by region
```

---

---

# Tool 8: VALIDATION (QC / In Silico Simulation)

## Purpose
**Simulate and validate DNA assembly process before lab work**

## Biological Background
Tests the **3-phase assembly process**:
1. **Phase 1: PCR Amplification** - Can primers amplify your DNA?
2. **Phase 2: Restriction Digestion** - Will enzymes cut correctly?
3. **Phase 3: Ligation** - Will fragments ligate into circle?

## When to Use

### Use Case 1: Pre-Lab Validation (Primary Use)
```
Scenario: Before ordering DNA/primers/enzymes, validate design
1. Generate DNA in DNA GENERATOR
2. Go to VALIDATION
3. Click "Fetch Latest Design"
4. Software runs 3-phase simulation
5. Results:
   ✅ PASS = Design is sound, proceed to lab
   ❌ FAIL = Design has issue, redesign first
```

### Use Case 2: Troubleshoot Failed Assembly
```
Scenario: Lab assembly failed - what went wrong?
1. Input your DNA design into VALIDATION
2. Check each phase:
   - Phase 1: PCR viable? (GC%, length checks)
   - Phase 2: Digestion works? (Enzyme sites present?)
   - Phase 3: Ligation possible? (Sticky ends match?)
3. Identify the failure point
4. Redesign or troubleshoot accordingly
```

## Workflow

```
┌──────────────────────────────────┐
│ Load Design from DNA Generator   │
│ or Manual Input                  │
└────────────┬─────────────────────┘
             ↓
┌──────────────────────────────────────────────────┐
│ PHASE 1: PCR AMPLIFICATION VALIDATION            │
├──────────────────────────────────────────────────┤
│ Check for each fragment:                         │
│ • Minimum length: ≥ 20 bp (PCR viable)          │
│ • GC content: 20-80% (not extreme)              │
│ • Result: PASS ✓ or FAIL ✗                       │
└────────────┬─────────────────────────────────────┘
             ↓
┌──────────────────────────────────────────────────┐
│ PHASE 2: RESTRICTION DIGESTION VALIDATION        │
├──────────────────────────────────────────────────┤
│ For each enzyme:                                 │
│ • Check: Recognition site in sequence?          │
│ • Check: No internal cuts (would destroy DNA)  │
│ • Check: 5' and 3' ends have enzyme sites       │
│ • Result: PASS ✓ or FAIL ✗                       │
└────────────┬─────────────────────────────────────┘
             ↓
┌──────────────────────────────────────────────────┐
│ PHASE 3: LIGATION & CIRCULARIZATION              │
├──────────────────────────────────────────────────┤
│ For circular assembly:                           │
│ • Check: Do fragments connect end-to-end?       │
│ • Check: Are sticky ends compatible?            │
│ • Check: All junctions match (same enzyme)      │
│ • Check: Forms closed circle (no gaps)          │
│ • Result: PASS ✓ or FAIL ✗                       │
└────────────┬─────────────────────────────────────┘
             ↓
┌──────────────────────────────────────────────────┐
│ FINAL REPORT                                     │
├──────────────────────────────────────────────────┤
│ Overall Status:                                  │
│   ✅ PASS - Design is valid, proceed to lab     │
│   ❌ FAIL - Design has issues, review below     │
│                                                  │
│ Detailed Logs:                                   │
│ • Phase 1 logs (PCR specific issues)            │
│ • Phase 2 logs (Digestion issues)               │
│ • Phase 3 logs (Ligation issues)                │
│                                                  │
│ Visualizations:                                  │
│ • Plasmid map (if circular)                     │
│ • Feature annotations                           │
│ • Step-by-step assembly diagram                 │
└──────────────────────────────────────────────────┘
```

## Plasmid Visualization

### Vector Map (Low Zoom - Overview)
```
Shows high-level features:

        [Probe 1]
           ↓
    ╔═══════════╗
    ║ Payload   ║ ← Colored arc = feature
    ║ (500bp)   ║
    ║ ╔─────┐   ║ ← Restriction sites marked
    ║ │Gene │   ║
    ║ └─────┘   ║
    ╚═══════════╝
           ↑
      [Probe 4]
      
Features visible at this zoom:
- Payload region (blue)
- Restriction enzyme sites (markers)
- Probe locations (labels)
```

### Atomic Map (High Zoom - Detail)
```
Shows individual bases:

    ╔═══════════╗
    ║ A·T G·C   ║ ← Individual base pairs
    ║ │\ /│     ║ ← Shown as "ladder"
    ║ │ X │     ║    on helix
    ║ │/ \│     ║
    ║ T·A C·G   ║
    ║ │\ /│     ║
    ║ │ X │     ║ ← Helix visualization
    ║ │/ \│     ║    at high resolution
    ║ G·C A·T   ║
    ╚═══════════╝
```

---

---

# COMPLETE APPLICATION WORKFLOW

## Typical User Journey: "Create and Validate DNA Barcode"

```
START
  ↓
[HOME] Review interface & capabilities
  ↓
[SIZE CALCULATOR] Determine ideal DNA size → 500 bp
  ↓
[DNA GENERATOR] Create unique DNA construct
  ├─ Mode: Circular
  ├─ Length: 500 bp
  ├─ Output: DNA + Primers + Probes
  ↓
[COMPARATOR] Verify DNA is unique
  ├─ Run BLAST search
  ├─ Check: No exact matches found
  ├─ Result: ✅ Unique sequence
  ↓
[PRIMER DESIGNER] (Optional) Refine primers if needed
  ├─ Review auto-generated primers
  ├─ Verify Tm matching (60°C ± 2°C)
  ├─ Confirm product size (500 bp)
  ↓
[qPCR ANALYSIS] Review probes for quality
  ├─ Check: All 4 probes Tm 68-72°C
  ├─ Check: Quality scores >90
  ├─ Check: Region distribution
  ↓
[VALIDATION] Simulate assembly before lab
  ├─ Phase 1: PCR viable? ✅ PASS
  ├─ Phase 2: Digestion works? ✅ PASS
  ├─ Phase 3: Circularization? ✅ PASS
  ├─ Overall: ✅ READY FOR LAB
  ↓
[EXPORT] Generate documentation
  ├─ Export to Excel (lab records)
  ├─ Export to PDF (stakeholder report)
  ├─ Save to Cloud (archive)
  ↓
[READY FOR MANUFACTURING]
  ├─ Synthesize DNA construct
  ├─ Embed in product packaging
  ├─ Quality control: Run qPCR
  ├─ Authentication: Store probes in database
  ↓
END
```

---

---

# QUICK REFERENCE: Tool Selection Guide

## "Which tool should I use?"

```
QUESTION: "What's the size of my DNA?"
ANSWER: → Use SIZE CALCULATOR

QUESTION: "I need unique DNA for authentication"
ANSWER: → Use DNA GENERATOR (automatically makes primers + probes)

QUESTION: "Is my DNA truly unique?"
ANSWER: → Use COMPARATOR (BLAST search)

QUESTION: "Can I improve the primers?"
ANSWER: → Use PRIMER DESIGNER (manual optimization)

QUESTION: "Are the probes good quality?"
ANSWER: → Use qPCR ANALYSIS (review & validate)

QUESTION: "Will my design work in the lab?"
ANSWER: → Use VALIDATION (3-phase simulation)

QUESTION: "I need professional documentation"
ANSWER: → Use EXPORT (Excel/PDF/Cloud)

QUESTION: "Is my assembly strategy sound?"
ANSWER: → Use VALIDATION + visualizations

QUESTION: "I want to verify a BLAST hit"
ANSWER: → Use PRIMER DESIGNER (design primers for that gene)
```

---

This completes the comprehensive guide to using each tool in DNAₓ Lab!

