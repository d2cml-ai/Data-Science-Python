"""Command line used by the skills and agents: `python -m housing_lima.cli <command>`."""

from __future__ import annotations

import argparse
import importlib.util
import json
import shutil
import sys
from datetime import date, datetime
from pathlib import Path

import pandas as pd

from .loaders import load_defaults, read_json, write_json
from .paths import FIXTURE_RUN, PLUGIN_ROOT, runs_root


def _print(obj) -> None:
    sys.stdout.write(json.dumps(obj, ensure_ascii=False, indent=2, default=str) + "\n")


def cmd_check_env(_args) -> int:
    mods = ["pandas", "numpy", "streamlit", "plotly", "jsonschema", "yaml", "pytest"]
    status = {m: importlib.util.find_spec(m) is not None for m in mods}
    ok = sys.version_info >= (3, 11) and all(v for k, v in status.items() if k != "pytest")
    _print({"python": sys.version.split()[0], "python_ok": sys.version_info >= (3, 11), "packages": status,
            "plugin_root": str(PLUGIN_ROOT), "runs_root": str(runs_root()), "ok": ok})
    return 0 if ok else 1


def cmd_new_run(args) -> int:
    from .intake import IntakeError, create_run
    answers = read_json(args.answers)
    try:
        run_dir = create_run(answers, Path(args.runs_root) if args.runs_root else None)
    except IntakeError as exc:
        _print({"ok": False, "code": exc.code, "error": str(exc), "suggestions": exc.suggestions})
        return 2
    _print({"ok": True, "run_dir": str(run_dir), "inputs": read_json(run_dir / "inputs.json")})
    return 0


def cmd_listings(args) -> int:
    from .listings import build_market
    run_dir = Path(args.run)
    inputs = read_json(run_dir / "inputs.json")
    defaults = load_defaults()
    raw = pd.concat([pd.read_csv(p) for p in args.raw], ignore_index=True)
    fx = {"usd_pen": args.fx, "as_of": args.fx_date, "source_url": args.fx_source} if args.fx else None
    index = None
    params_path = run_dir / "housing_params.json"
    if params_path.exists():
        index = read_json(params_path).get("price_index_ppm2_by_district")
    df, summary, report = build_market(raw, inputs, defaults, args.source_mode, fx,
                                       args.collected_at or date.today().isoformat(), index)
    df.to_csv(run_dir / "listings.csv", index=False)
    write_json(run_dir / "market_summary.json", summary)
    brief = [{"district": d["district"], "sale_n": d["sale"]["n"], "rent_n": d["rent"]["n"],
              "realistic_price": d["sale"]["realistic_price"], "realistic_rent": d["rent"]["realistic_rent"],
              "low_confidence": d["low_confidence"], "warnings": d["warnings"]} for d in summary["districts"]]
    _print({"ok": True, "report": report, "districts": brief})
    return 0


def cmd_validate(args) -> int:
    from .validate import validate_run
    errors = validate_run(Path(args.run), args.stage)
    _print({"ok": not errors, "stage": args.stage, "errors": errors})
    return 0 if not errors else 1


def cmd_analyze(args) -> int:
    from .analysis import AnalysisError, run_analysis
    from .validate import ValidationFailed
    try:
        summary = run_analysis(Path(args.run))
    except (ValidationFailed, AnalysisError) as exc:
        _print({"ok": False, "error": str(exc)})
        return 1
    _print({"ok": True, "verdicts": [d["verdict_text"] for d in summary["districts"]], "warnings": summary["warnings"]})
    return 0


def cmd_summary(args) -> int:
    run_dir = Path(args.run)
    summary = read_json(run_dir / "analysis_summary.json")
    market = read_json(run_dir / "market_summary.json")
    out = {"run_id": summary["run_id"], "source_mode": market["source_mode"], "synthetic": summary.get("synthetic", False),
           "districts": [], "warnings": summary["warnings"],
           "dashboard": f'streamlit run "{PLUGIN_ROOT / "app" / "app.py"}" -- --run "{run_dir}"'}
    for d, m in zip(summary["districts"], market["districts"]):
        out["districts"].append({
            "district": d["district"], "sale_n": m["sale"]["n"], "rent_n": m["rent"]["n"],
            "price": d.get("price_used"), "rent": d.get("rent_used"), "low_confidence": d["low_confidence"],
            "verdicts": {v["horizon"]: v["label"] for v in d["verdicts"]}, "text": d["verdict_text"]})
    _print(out)
    return 0


def cmd_returns(args) -> int:
    from .returns import summarize_index
    df = pd.read_csv(args.prices)
    levels = pd.Series(df[args.value_col].to_numpy(), index=pd.to_datetime(df[args.date_col]))
    _print(summarize_index(levels, band_window=args.band_window))
    return 0


def cmd_fixture_run(args) -> int:
    """End-to-end dry run on the synthetic fixture: intake -> listings (csv mode) -> analysis."""
    from .analysis import run_analysis
    from .listings import build_market
    from .validate import validate_run
    root = Path(args.runs_root) if args.runs_root else runs_root()
    fixture_inputs = read_json(FIXTURE_RUN / "inputs.json")
    run_id = f"{datetime.now():%Y%m%d-%H%M}-fixture-dry-run"
    run_dir = root / run_id
    if run_dir.exists():
        shutil.rmtree(run_dir)
    run_dir.mkdir(parents=True)
    write_json(run_dir / "inputs.json", {**fixture_inputs, "run_id": run_id})
    # Research agents in fixture mode: copy their synthetic outputs instead of searching the web.
    for name in ("housing_params.json", "opportunity_costs.json"):
        shutil.copy(FIXTURE_RUN / name, run_dir / name)
    inputs = read_json(run_dir / "inputs.json")
    params = read_json(run_dir / "housing_params.json")
    raw = pd.read_csv(FIXTURE_RUN / "raw_listings.csv")
    df, summary, _ = build_market(raw, inputs, load_defaults(), "csv", fx=read_json(FIXTURE_RUN / "fx.json"),
                                  collected_at=fixture_inputs["created_at"][:10],
                                  index_ppm2=params.get("price_index_ppm2_by_district"))
    df.to_csv(run_dir / "listings.csv", index=False)
    write_json(run_dir / "market_summary.json", summary)
    errors = validate_run(run_dir, "research")
    if errors:
        _print({"ok": False, "errors": errors})
        return 1
    run_analysis(run_dir)
    errors = validate_run(run_dir, "all")
    _print({"ok": not errors, "run_dir": str(run_dir), "errors": errors})
    return 0 if not errors else 1


def main(argv=None) -> int:
    p = argparse.ArgumentParser(prog="housing-lima")
    sub = p.add_subparsers(dest="cmd", required=True)
    sub.add_parser("check-env").set_defaults(fn=cmd_check_env)

    s = sub.add_parser("new-run", help="validate intake answers and create the run folder")
    s.add_argument("--answers", required=True)
    s.add_argument("--runs-root")
    s.set_defaults(fn=cmd_new_run)

    s = sub.add_parser("listings", help="normalize, dedupe, flag and summarize listings")
    s.add_argument("--run", required=True)
    s.add_argument("--raw", required=True, nargs="+", help="one or more raw listing CSV files")
    s.add_argument("--source-mode", choices=["live", "csv", "mixed"], required=True)
    s.add_argument("--fx", type=float, help="USD/PEN rate of the collection date")
    s.add_argument("--fx-date")
    s.add_argument("--fx-source")
    s.add_argument("--collected-at")
    s.set_defaults(fn=cmd_listings)

    s = sub.add_parser("validate")
    s.add_argument("--run", required=True)
    s.add_argument("--stage", default="research", choices=["inputs", "market", "opportunity", "research", "analysis", "all"])
    s.set_defaults(fn=cmd_validate)

    s = sub.add_parser("analyze")
    s.add_argument("--run", required=True)
    s.set_defaults(fn=cmd_analyze)

    s = sub.add_parser("summary")
    s.add_argument("--run", required=True)
    s.set_defaults(fn=cmd_summary)

    s = sub.add_parser("returns", help="annualized returns, volatility and worst year from index levels")
    s.add_argument("--prices", required=True)
    s.add_argument("--date-col", default="date")
    s.add_argument("--value-col", default="close")
    s.add_argument("--band-window", type=int, default=10)
    s.set_defaults(fn=cmd_returns)

    s = sub.add_parser("fixture-run", help="end-to-end dry run on the synthetic fixture")
    s.add_argument("--runs-root")
    s.set_defaults(fn=cmd_fixture_run)

    args = p.parse_args(argv)
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    return args.fn(args)


if __name__ == "__main__":
    raise SystemExit(main())
