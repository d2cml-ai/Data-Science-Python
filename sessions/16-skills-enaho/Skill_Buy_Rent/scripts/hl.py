"""Launcher for the housing_lima CLI that works without `pip install`.

Usage: python "${CLAUDE_PLUGIN_ROOT}/scripts/hl.py" <command> [options]
Commands: check-env, new-run, listings, validate, analyze, summary, returns, fixture-run
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from housing_lima.cli import main  # noqa: E402

if __name__ == "__main__":
    raise SystemExit(main())
