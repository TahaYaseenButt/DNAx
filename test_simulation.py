import unittest
import sys
import os

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from tools.simulation import run_simulation, RESTRICTION_DATA

class TestSimulation(unittest.TestCase):
    def setUp(self):
        # Setup mock fragments that should form a valid circle
        # Use EcoRI and BamHI for simplicity
        # EcoRI: GAATTC, BamHI: GGATCC
        
        # Frag 1: EcoRI -> BamHI
        self.frag1 = {
            'seq': 'GAATTCAAAAAAAAAAGGATCC',
            'start_enzyme': 'EcoRI',
            'end_enzyme': 'BamHI',
            'start_site': 'GAATTC',
            'end_site': 'GGATCC',
            'core': 'AAAAAAAAAA'
        }
        
        # Frag 2: BamHI -> EcoRI (To close the loop with Frag 1)
        self.frag2 = {
            'seq': 'GGATCCTTTTTTTTTTGAATTC',
            'start_enzyme': 'BamHI',
            'end_enzyme': 'EcoRI',
            'start_site': 'GGATCC',
            'end_site': 'GAATTC',
            'core': 'TTTTTTTTTT'
        }
        
    def test_successful_assembly(self):
        fragments = [self.frag1, self.frag2]
        report = run_simulation(fragments)
        self.assertTrue(report['success'], "Simulation should pass for valid fragments")
        
    def test_mismatched_junction(self):
        # Mismatch: Frag 1 ends BamHI, Frag 2 starts EcoRI
        frag2_bad = self.frag2.copy()
        frag2_bad['start_enzyme'] = 'EcoRI' # Expects BamHI
        
        fragments = [self.frag1, frag2_bad]
        report = run_simulation(fragments)
        self.assertFalse(report['success'], "Simulation should fail for mismatched junction")
        
        # Check logs for specific failure
        # logs structure: report['steps'][index]['logs']
        # Ligation is step 3 (index 2)
        lig_logs = report['steps'][2]['logs']
        found_error = any("Junction" in log and "FAIL" in log for log in lig_logs)
        self.assertTrue(found_error, "Should log junction failure")

    def test_missing_enzyme_in_sequence(self):
        # Frag 1 says it starts with EcoRI but sequence is random
        frag_bad = self.frag1.copy()
        frag_bad['seq'] = 'CCCCCCCCCCCCCCCCCCCCCC' 
        
        fragments = [frag_bad, self.frag2]
        report = run_simulation(fragments)
        self.assertFalse(report['success'], "Simulation should fail if enzyme site missing from seq")
        
        # Digestion is step 2 (index 1)
        dig_logs = report['steps'][1]['logs']
        found_error = any("not found in sequence" in log for log in dig_logs)
        self.assertTrue(found_error, "Should check for missing digest sites")

if __name__ == '__main__':
    unittest.main()
