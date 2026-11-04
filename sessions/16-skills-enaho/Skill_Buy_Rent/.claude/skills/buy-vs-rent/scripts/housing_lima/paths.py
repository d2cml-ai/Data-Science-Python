"""Locations. Package files (schemas, config, app, fixture) live next to this file, so the skill folder
works the same from the repo (.claude/skills/) and from the personal folder (~/.claude/skills/).
Run outputs go to the working directory: salidas/, figuras/ and datos/."""

from __future__ import annotations

import os
from pathlib import Path

PACKAGE_DIR = Path(__file__).resolve().parent
SCRIPTS_DIR = PACKAGE_DIR.parent                 # .claude/skills/buy-vs-rent/scripts
SKILL_DIR = SCRIPTS_DIR.parent                   # .claude/skills/buy-vs-rent
SKILLS_DIR = SKILL_DIR.parent                    # .claude/skills
HL = SCRIPTS_DIR / "hl.py"
SCHEMAS_DIR = PACKAGE_DIR / "schemas"
CONFIG_DIR = PACKAGE_DIR / "config"
DEFAULTS_FILE = CONFIG_DIR / "defaults.yaml"
APP_FILE = PACKAGE_DIR / "app" / "app.py"
FIXTURE_RUN = PACKAGE_DIR / "fixtures" / "sample_run"
LISTINGS_TEMPLATE = SKILLS_DIR / "peru-listings-search" / "listings_template.csv"


def runs_root() -> Path:
    """Folder that holds run folders: ./salidas, or HOUSING_LIMA_RUNS."""
    return Path(os.environ.get("HOUSING_LIMA_RUNS") or Path.cwd() / "salidas")


def figures_dir() -> Path:
    return Path(os.environ.get("HOUSING_LIMA_FIGURES") or Path.cwd() / "figuras")


def data_dir() -> Path:
    """User-supplied files, e.g. datos/listings.csv for the CSV fallback (keep it out of git)."""
    return Path(os.environ.get("HOUSING_LIMA_DATA") or Path.cwd() / "datos")
