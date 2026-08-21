
import sys
import os
import unittest
import tkinter as tk

# Add src to path
sys.path.append(os.path.join(os.getcwd(), 'src'))

from tools.dna_generate import DNAGeneratePage, BSAI_SITE, BSAI_REV, OVERHANG_FWD, OVERHANG_REV

class TestGoldenGateGeneration(unittest.TestCase):
    def setUp(self):
        self.root = tk.Tk()
        # Mock parent
        self.page = DNAGeneratePage(self.root)

    def tearDown(self):
        self.root.destroy()

    def test_overhangs(self):
        # Bug 1 Fix Check
        self.assertEqual(OVERHANG_FWD, "GTCA", "Left overhang invalid")
        self.assertEqual(OVERHANG_REV, "GTCA", "Right overhang invalid (Must match Left for circularization)")

    def test_constraints(self):
        print("\nTesting 100 generated sequences for updated constraints...")
        n = 500
        for i in range(100):
            seq = self.page._generate_valid_payload(n)
            self.assertIsNotNone(seq, "Failed to generate sequence within attempts")
            
            # Check length
            self.assertEqual(len(seq), n)
            
            # Check BsaI
            self.assertNotIn(BSAI_SITE, seq)
            self.assertNotIn(BSAI_REV, seq)
            
            # Check GC > 50%
            gc = (seq.count('G') + seq.count('C')) / len(seq)
            self.assertTrue(0.50 <= gc <= 0.70, f"GC content {gc} out of range (must be 0.50-0.70)")
            
            # Check Homopolymers
            for base in "ATCG":
                self.assertNotIn(base * 6, seq, f"Homopolymer {base*6} found")
        print("All 100 sequences passed updated High-Performance constraints.")

if __name__ == '__main__':
    unittest.main()
