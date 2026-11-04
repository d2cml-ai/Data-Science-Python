"""Load configuration and run folders."""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Optional

import pandas as pd
import yaml

from .paths import DEFAULTS_FILE, runs_root
from .validate import ValidationFailed, validate_run


def load_defaults(path: Optional[Path] = None) -> dict:
    with open(path or DEFAULTS_FILE, encoding="utf-8") as fh:
        return yaml.safe_load(fh)


def read_json(path: Path) -> Any:
    return json.loads(Path(path).read_text(encoding="utf-8"))


def write_json(path: Path, data: Any) -> None:
    Path(path).write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


@dataclass
class RunData:
    run_dir: Path
    inputs: dict
    market: dict
    params: dict
    opportunity: dict
    listings: pd.DataFrame
    results: Optional[pd.DataFrame] = None
    summary: Optional[dict] = None

    @property
    def run_id(self) -> str:
        return self.inputs["run_id"]

    @property
    def synthetic(self) -> bool:
        return bool(self.inputs.get("synthetic") or self.market.get("synthetic"))

    def district(self, name: str) -> dict:
        for d in self.market["districts"]:
            if d["district"] == name:
                return d
        raise KeyError(name)

    def option(self, option_id: str) -> dict:
        for o in self.opportunity["options"]:
            if o["id"] == option_id:
                return o
        raise KeyError(option_id)


def load_run(run_dir: Path, validate: bool = True) -> RunData:
    run_dir = Path(run_dir)
    if validate:
        errors = validate_run(run_dir, "research")
        if errors:
            raise ValidationFailed(errors)
    results_path = run_dir / "analysis_results.csv"
    summary_path = run_dir / "analysis_summary.json"
    return RunData(
        run_dir=run_dir,
        inputs=read_json(run_dir / "inputs.json"),
        market=read_json(run_dir / "market_summary.json"),
        params=read_json(run_dir / "housing_params.json"),
        opportunity=read_json(run_dir / "opportunity_costs.json"),
        listings=pd.read_csv(run_dir / "listings.csv"),
        results=pd.read_csv(results_path) if results_path.exists() else None,
        summary=read_json(summary_path) if summary_path.exists() else None,
    )


def list_runs(root: Optional[Path] = None) -> list[Path]:
    """Run folders that contain inputs.json, newest first (run ids start with a timestamp)."""
    root = Path(root or runs_root())
    if not root.exists():
        return []
    runs = [p for p in root.iterdir() if p.is_dir() and (p / "inputs.json").exists()]
    return sorted(runs, key=lambda p: p.name, reverse=True)


def latest_run(root: Optional[Path] = None) -> Optional[Path]:
    runs = list_runs(root)
    return runs[0] if runs else None
