"""Page wrapper to expose the ComparatorPage in the pages/ directory.

This module imports the real implementation from `tools.comparator` so the
UI file appears under `src/pages/` as requested without duplicating logic.
"""
from tools.comparator import ComparatorPage

__all__ = ["ComparatorPage"]
