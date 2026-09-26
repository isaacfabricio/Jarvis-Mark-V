from __future__ import annotations

"""Environment bootstrap for Jupyter Notebooks.

Ensures the project root directory is cleanly injected into sys.path
for interactive prototyping and isolated service debugging.
"""

import sys
from pathlib import Path

# Resolve project root dynamically (parent of notebooks/)
PROJECT_ROOT = Path(__file__).resolve().parent.parent

if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))
    print(f"J.A.R.V.I.S. Mark V root injected into sys.path: {PROJECT_ROOT}")
