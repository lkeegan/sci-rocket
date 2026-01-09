import sys
from pathlib import Path

# Add the root directory of the project to sys.path to allow imports from top-level workflow folder
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))