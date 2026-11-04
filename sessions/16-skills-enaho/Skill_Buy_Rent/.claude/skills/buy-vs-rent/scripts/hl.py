"""Launcher for the housing_lima CLI that works without `pip install`.

Usage: python "${CLAUDE_SKILL_DIR}/scripts/hl.py" <command> [options]
Commands: check-env, new-run, listings, validate, analyze, summary, figures, dashboard, returns, fixture-run
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))  # housing_lima sits next to this file

from housing_lima.cli import main  # noqa: E402

if __name__ == "__main__":
    raise SystemExit(main())
