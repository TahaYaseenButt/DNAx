import sys
import os

# Add src to path just in case
sys.path.append(os.path.join(os.getcwd(), 'src'))

try:
    from tools.primer_designer import RESTRICTION_DATA
    print("RESTRICTION_DATA keys:")
    keys = list(RESTRICTION_DATA.keys())
    print("\n".join(keys))
    
    if "Bsa1" in keys:
        print("\nSUCCESS: Bsa1 found.")
    else:
        print("\nFAILURE: Bsa1 NOT found.")
        
except Exception as e:
    print(f"Import failed: {e}")
    import traceback
    traceback.print_exc()
