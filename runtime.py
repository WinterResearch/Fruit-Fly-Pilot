"""Prefer project-local wheels; never modify the user's Python environment."""
from pathlib import Path
import sys
ROOT = Path(__file__).resolve().parent
if (ROOT / '.deps').exists():
    sys.path.insert(0, str(ROOT / '.deps'))

