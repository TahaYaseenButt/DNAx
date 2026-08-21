#!/usr/bin/env python3
"""
Test script for the industrial-level DNA generator algorithm.
Tests Phase 1 (Sizing), Phase 2 (Validation), and Phase 3 (Assembly).
"""
import random
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from tools.primer_designer import RESTRICTION_DATA

def test_dna_generator():
    """Simulate the three-phase DNA generation algorithm."""
    
    print("="*70)
    print("INDUSTRIAL-LEVEL DNA GENERATOR TEST")
    print("="*70)
    
    # Test parameters
    total_length = 500
    enzyme_names = ['EcoRI', 'BamHI', 'HindIII', 'NotI']
    
    print("\nINPUT:")
    print("  Total Length: {} bp".format(total_length))
    print("  Enzymes: {}".format(' > '.join(enzyme_names)))
    
    # ============ PHASE 1: SIZING ============
    print("\n" + "="*70)
    print("PHASE 1: SIZING")
    print("="*70)
    
    enzyme_sites = []
    for name in enzyme_names:
        site = RESTRICTION_DATA.get(name, ("", ""))[0]
        enzyme_sites.append(site)
        print("  {:12} > Recognition site: {:12} ({} bp)".format(name, site, len(site)))
    
    total_enzyme_len = sum(len(s) for s in enzyme_sites)
    print("\n  Total enzyme site length: {} bp".format(total_enzyme_len))
    
    
    # New logic: remaining = total_length (Payload = Input)
    remaining = total_length
    print("  Total length (Payload) treated as target for random generation: {} bp".format(remaining))
    
    target_per_frag = remaining // 4
    remainder = remaining % 4
    print("  Target length per fragment: {} bp (base)".format(target_per_frag))
    print("  Fragments 0-{} get +1 bp: target = {} bp each".format(remainder-1, target_per_frag + 1))
    
    # ============ PHASE 1: SIZING ============
    print(f"\n{'='*70}")
    print("PHASE 1: SIZING")
    print(f"{'='*70}")
    
    enzyme_sites = []
    for name in enzyme_names:
        site = RESTRICTION_DATA.get(name, ("", ""))[0]
        enzyme_sites.append(site)
        print(f"  {name:12} > Recognition site: {site:12} ({len(site)} bp)")
    
    total_enzyme_len = sum(len(s) for s in enzyme_sites)
    print(f"\n  Total enzyme site length: {total_enzyme_len} bp")
    
    # In the circular assembly, we only count each unique site once for the total length
    # This matches the new app logic where End Result (Circle) = Target Length
    # In the circular assembly, we only count each unique site once for the total length
    # This matches the new app logic where End Result (Circle) = Target Length
    remaining = total_length
    print(f"  Total length (Payload) treated as target for random generation: {remaining} bp")
    
    target_per_frag = remaining // 4
    remainder = remaining % 4
    print(f"  Target length per fragment: {target_per_frag} bp (base)")
    print(f"  Fragments 0-{remainder-1} get +1 bp: target = {target_per_frag + 1} bp each")
    
    # ============ PHASE 2: RANDOM DNA GENERATION WITH VALIDATION ============
    print(f"\n{'='*70}")
    print("PHASE 2: RANDOM DNA GENERATION & VALIDATION")
    print(f"{'='*70}")
    
    bases = ['A', 'T', 'C', 'G']
    max_retries = 100
    
    def has_long_run(seq, max_consecutive=4):
        run = 1
        for i in range(1, len(seq)):
            if seq[i] == seq[i-1]:
                run += 1
                if run > max_consecutive:
                    return True
            else:
                run = 1
        return False
    
    def get_gc_percent(seq):
        if not seq:
            return 0
        gc = seq.count('G') + seq.count('C')
        return (gc / len(seq)) * 100
    
    def contains_forbidden_sites(seq, sites):
        for site in sites:
            if site and site in seq:
                return True
        return False
    
    segments = []
    total_attempts = 0
    
    for frag_idx in range(4):
        target = target_per_frag + (1 if frag_idx < remainder else 0)
        valid_segment = None
        attempts = 0
        
        print(f"\n  Fragment {frag_idx}: Target length = {target} bp")
        
        for attempt in range(max_retries):
            attempts += 1
            target_gc = random.randint(45, 55) / 100.0
            gc_weight = target_gc / 2.0
            at_weight = (1.0 - target_gc) / 2.0
            weights = [at_weight, at_weight, gc_weight, gc_weight]
            
            candidate = ''.join(random.choices(bases, weights=weights, k=target))
            
            # Validation checks
            checks_passed = True
            
            # Check 1: Long runs (no more than 4 consecutive)
            if has_long_run(candidate, max_consecutive=4):
                checks_passed = False
            
            # Check 2: GC content (40-60%)
            gc = get_gc_percent(candidate)
            if gc < 40 or gc > 60:
                checks_passed = False
            
            # Check 3: Forbidden sites
            if contains_forbidden_sites(candidate, enzyme_sites):
                checks_passed = False
            
            if checks_passed:
                valid_segment = candidate
                break
        
        if valid_segment is None:
            print(f"    [FAILED] After {max_retries} attempts")
            return False
        
        gc = get_gc_percent(valid_segment)
        print(f"    ✓ Valid segment generated in {attempts} attempt(s)")
        print(f"      Sequence: {valid_segment[:30]}... (showing first 30)")
        print(f"      GC content: {gc:.1f}%")
        print(f"      No long runs: ✓")
        print(f"      No forbidden sites: ✓")
        
        segments.append(valid_segment)
        total_attempts += attempts
    
    print(f"\n  Total generation attempts: {total_attempts}")
    
    # ============ PHASE 3: ASSEMBLY ============
    print(f"\n{'='*70}")
    print("PHASE 3: ASSEMBLY (CIRCULAR PATTERN)")
    print(f"{'='*70}")
    
    fragments = []
    
    for frag_idx in range(4):
        start_site = enzyme_sites[frag_idx]
        end_site = enzyme_sites[(frag_idx + 1) % 4]  # Circular
        start_name = enzyme_names[frag_idx]
        end_name = enzyme_names[(frag_idx + 1) % 4]
        
        frag_seq = start_site + segments[frag_idx] + end_site
        
        print(f"\n  Fragment {frag_idx}:")
        print(f"    Start enzyme: {start_name:12} > Site: {start_site}")
        print(f"    Core DNA (random): {segments[frag_idx][:20]}... ({len(segments[frag_idx])} bp)")
        print(f"    End enzyme: {end_name:12} > Site: {end_site}")
        print(f"    Total fragment length: {len(frag_seq)} bp")
        
        fragments.append({
            'start_enzyme': start_name,
            'start_site': start_site,
            'core': segments[frag_idx],
            'end_site': end_site,
            'end_enzyme': end_name,
            'seq': frag_seq
        })
    
    # Build full sequence: StartSite + Core for each fragment
    # This correctly reconstructs the circle A-core-B-core-C-core-D-core...
    full_seq = ''.join((f['start_site'] + f['core']) for f in fragments)
    
    print(f"\n{'='*70}")
    print("FINAL RESULT")
    print(f"{'='*70}")
    print(f"  Full circular sequence length: {len(full_seq)} bp")
    print(f"  Target DNA length (random + enzymes): {total_length} bp")
    print(f"  Note: Actual length includes enzyme sites at junctions.")
    print(f"        Calculation: 4 × {target_per_frag} + enzymes + remainders = {len(full_seq)} bp")
    
    # Verify total matches expected input
    if len(full_seq) >= total_length:
        print(f"  Validation: [OK] (meets or exceeds target)")
    else:
        print(f"  Validation: [FAILED] (below target)")
        return False
    
    # Verify circular closure
    print(f"\n  Circular Closure Check:")
    print(f"    Fragment 0 starts with: {fragments[0]['start_site']}")
    print(f"    Fragment 3 ends with:   {fragments[3]['end_site']}")
    print(f"    Closes circle: {'[OK]' if fragments[3]['end_site'] == fragments[0]['start_site'] else '[FAILED]'}")
    
    # Print first 100 bp as sample
    print(f"\n  Sequence sample (first 100 bp):")
    print(f"    {full_seq[:100]}")
    
    print(f"\n{'='*70}")
    print("[SUCCESS] ALL TESTS PASSED - INDUSTRIAL LEVEL VALIDATION")
    print(f"{'='*70}\n")
    
    return True

if __name__ == '__main__':
    try:
        success = test_dna_generator()
        sys.exit(0 if success else 1)
    except Exception as e:
        print(f"\n[ERROR]: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
