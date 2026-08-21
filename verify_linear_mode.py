
import sys
import os
import unittest
import tkinter as tk

# Add src to path
sys.path.append(os.path.join(os.getcwd(), 'src'))

from tools.dna_generate import DNAGeneratePage, BSAI_SITE, BSAI_REV

class TestDNAModes(unittest.TestCase):
    def setUp(self):
        self.root = tk.Tk()
        self.page = DNAGeneratePage(self.root)

    def tearDown(self):
        self.root.destroy()

    def test_linear_mode(self):
        print("\nTesting Linear Mode...")
        # Mock mode
        self.page.mode_var.set("linear")
        
        # Override _display_results to capture data instead of updating UI
        self.captured_data = {}
        def mock_display(data):
            self.captured_data = data
        
        self.page._display_results = mock_display
        
        # Run generation directly (synchronously)
        self.page._run_generation(100, "linear")
        
        # Process pending 'after' events
        self.root.update()
        
        self.assertEqual(self.captured_data.get('mode'), 'linear')
        self.assertEqual(self.captured_data.get('length'), 100)
        self.assertEqual(self.captured_data.get('total_length'), 100)
        self.assertEqual(self.captured_data.get('payload'), self.captured_data.get('linear_seq'))
        
        # Ensure no BsaI sites in linear result (since it's just payload)
        self.assertNotIn(BSAI_SITE, self.captured_data.get('linear_seq', ''))
        print("Linear Mode OK")

    def test_circular_mode(self):
        print("\nTesting Circular Mode...")
        self.page.mode_var.set("circular")
        
        self.captured_data = {}
        def mock_display(data):
            self.captured_data = data
        
        self.page._display_results = mock_display
        
        self.page._run_generation(100, "circular")
        
        self.root.update()
        
        self.assertEqual(self.captured_data.get('mode'), 'circular')
        self.assertEqual(self.captured_data.get('length'), 100)
        # Total length should be > 100 due to tails
        self.assertTrue(self.captured_data.get('total_length', 0) > 100)
        # Should contain BsaI sites
        self.assertIn(BSAI_SITE, self.captured_data.get('linear_seq', ''))
        print("Circular Mode OK")

if __name__ == '__main__':
    unittest.main()
