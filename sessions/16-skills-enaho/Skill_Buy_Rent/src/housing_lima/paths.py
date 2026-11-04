"""Locations of the plugin folders, resolved from this file so they work from the repo and after install."""

from __future__ import annotations

import os
from pathlib import Path

def _plugin_root() -> Path:
    # Repo or editable install: src/housing_lima/paths.py -> plugin root two levels up.
    here = Path(__file__).resolve().parents[2]
    if (here / "schemas").exists():
        return here
    env = os.environ.get("CLAUDE_PLUGIN_ROOT")
    return Path(env) if env else here


PLUGIN_ROOT = _plugin_root()
SCHEMAS_DIR = PLUGIN_ROOT / "schemas"
CONFIG_DIR = PLUGIN_ROOT / "config"
DEFAULTS_FILE = CONFIG_DIR / "defaults.yaml"
FALLBACK_DIR = PLUGIN_ROOT / "data" / "fallback"
FIXTURE_RUN = PLUGIN_ROOT / "tests" / "fixtures" / "sample_run"


def runs_root() -> Path:
    """Folder that holds run folders. Override with HOUSING_LIMA_RUNS."""
    return Path(os.environ.get("HOUSING_LIMA_RUNS") or PLUGIN_ROOT / "runs")
