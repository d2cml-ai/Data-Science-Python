"""Run selection, cached loading and control defaults for the dashboard."""

from __future__ import annotations

import os
import sys
from pathlib import Path
from typing import Optional

import streamlit as st

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT / "src") not in sys.path:
    sys.path.insert(0, str(ROOT / "src"))

from housing_lima.analysis import resolve_params  # noqa: E402
from housing_lima.loaders import RunData, list_runs, load_defaults, load_run  # noqa: E402
from housing_lima.paths import FIXTURE_RUN  # noqa: E402


def cli_run_arg(argv: Optional[list[str]] = None) -> Optional[str]:
    """`streamlit run app/app.py -- --run runs/<id>` puts --run in sys.argv."""
    argv = sys.argv if argv is None else argv
    for i, a in enumerate(argv):
        if a == "--run" and i + 1 < len(argv):
            return argv[i + 1]
        if a.startswith("--run="):
            return a.split("=", 1)[1]
    return None


def available_runs() -> list[Path]:
    """Explicit run first, then runs/ newest first, then the synthetic fixture."""
    found: list[Path] = []
    explicit = cli_run_arg() or os.environ.get("HOUSING_LIMA_RUN")
    if explicit:
        found.append(Path(explicit).resolve())
    for p in list_runs():
        if p.resolve() not in found and (p / "analysis_summary.json").exists():
            found.append(p.resolve())
    if FIXTURE_RUN.resolve() not in found:
        found.append(FIXTURE_RUN.resolve())
    return found


@st.cache_data(show_spinner=False)
def cached_run(path: str) -> RunData:
    return load_run(Path(path), validate=True)


@st.cache_data(show_spinner=False)
def cached_defaults() -> dict:
    return load_defaults()


def district_defaults(run: RunData, district: str, defaults: dict) -> dict:
    """Starting values for the controls: listings for price/rent, researched params, user's answers."""
    resolved = resolve_params(run, district, defaults)
    md = run.district(district)
    return {
        "price": md["sale"]["realistic_price"],
        "price_p25": md["sale"]["price_p25"],
        "price_p75": md["sale"]["price_p75"],
        "rent": md["rent"]["realistic_rent"],
        "values": resolved.values,
        "sources": resolved.sources,
        "warnings": resolved.warnings,
    }
