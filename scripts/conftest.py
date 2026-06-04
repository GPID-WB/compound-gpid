"""pytest configuration for scripts/brain/ tests.

Inserts the scripts/ directory into sys.path so that ``from brain import ...``
resolves correctly when pytest is invoked from the repo root:

    python -m pytest scripts/brain/tests/ -v
"""
import sys
from pathlib import Path

# scripts/ directory — parent of this conftest.py
_SCRIPTS_DIR = str(Path(__file__).parent)
if _SCRIPTS_DIR not in sys.path:
    sys.path.insert(0, _SCRIPTS_DIR)
