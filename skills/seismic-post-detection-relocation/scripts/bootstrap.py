"""Shared maintained modules, without modifying pinned upstream repositories."""
import sys
from pathlib import Path
ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / 'contracts'))
sys.path.insert(0, str(ROOT / 'skills/seismic-relocation/scripts'))
