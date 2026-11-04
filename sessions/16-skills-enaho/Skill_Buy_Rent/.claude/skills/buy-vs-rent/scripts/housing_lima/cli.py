"""Command line used by the skills and agents: `python .claude/skills/buy-vs-rent/scripts/hl.py <command>`."""

from __future__ import annotations

import argparse
import importlib.util
import json
import shutil
import subprocess
import sys
from datetime import date, datetime
from pathlib import Path

import pandas as pd

from .loaders import load_defaults, read_json, write_json
from .paths import APP_FILE, FIXTURE_RUN, HL, PACKAGE_DIR, figures_dir, runs_root


def _print(obj) -> None:
    sys.stdout.write(json.dumps(obj, ensure_ascii=False, indent=2, default=str) + "\n")


def cmd_check_env(_args) -> int:
    mods = ["pandas", "numpy", "streamlit", "plotly", "matplotlib", "jsonschema", "yaml", "pytest"]
    status = {m: importlib.util.find_spec(m) is not None for m in mods}
    ok = sys.version_info >= (3, 11) and all(v for k, v in status.items() if k != "pytest")
    _print({"python": sys.version.split()[0], "python_ok": sys.version_info >= (3, 11), "packages": status,
            "engine": str(PACKAGE_DIR), "hl": str(HL), "salidas": str(runs_root()), "ok": ok})
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
    report = write_validation_report(Path(args.run), args.stage, errors)
    _print({"ok": not errors, "stage": args.stage, "errors": errors, "report": str(report)})
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
           "dashboard": f'python "{HL}" dashboard --run "{run_dir}"',
           "figures": f'python "{HL}" figures --run "{run_dir}"'}
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
    report = write_validation_report(run_dir, "all", errors)
    _print({"ok": not errors, "run_dir": str(run_dir), "errors": errors, "report": str(report)})
    return 0 if not errors else 1


def write_validation_report(run_dir: Path, stage: str, errors: list[str]) -> Path:
    """Human-readable check list, saved as <run_dir>/validacion.txt and copied to salidas/validacion.txt."""
    lines = [f"Validación de {run_dir.name} · etapa {stage} · {datetime.now():%Y-%m-%d %H:%M}", ""]
    lines.append("RESULTADO: OK" if not errors else f"RESULTADO: {len(errors)} ERROR(ES)")
    lines += [f"  - {e}" for e in errors]
    try:
        inputs = read_json(run_dir / "inputs.json")
        lines += ["", f"Búsqueda: S/ {inputs['price_min_pen']:,.0f}–{inputs['price_max_pen']:,.0f}, "
                      f">= {inputs['min_area_m2']:g} m², >= {inputs['min_bedrooms']} dorm., "
                      f"cuota inicial {inputs['down_payment_pct']:g}%, distritos: {', '.join(inputs['districts'])}"]
        if inputs.get("synthetic"):
            lines.append("DATOS SINTÉTICOS de prueba")
    except (FileNotFoundError, KeyError):
        pass
    if (run_dir / "market_summary.json").exists():
        m = read_json(run_dir / "market_summary.json")
        lines += ["", f"Avisos (modo {m['source_mode']}, recolectados {m['collected_at']}); "
                      f"descartados sin URL: {m.get('dropped_without_url', 0)}"]
        for d in m["districts"]:
            flag = "  BAJA CONFIANZA" if d["low_confidence"] else ""
            price = d["sale"]["realistic_price"]
            rent = d["rent"]["realistic_rent"]
            lines.append(f"  {d['district']}: venta n={d['sale']['n']} (de {d['sale'].get('n_found', '?')}), "
                         f"alquiler n={d['rent']['n']} (de {d['rent'].get('n_found', '?')}), "
                         f"precio realista {'S/ {:,.0f}'.format(price) if price else 's/d'}, "
                         f"alquiler realista {'S/ {:,.0f}'.format(rent) if rent else 's/d'}{flag}")
    if (run_dir / "listings.csv").exists():
        df = pd.read_csv(run_dir / "listings.csv")
        lines.append(f"  Filas: {len(df)}; con URL: {int(df['source_url'].notna().sum())}; duplicados marcados: "
                     f"{int(df['duplicate_of'].notna().sum())}; atípicos marcados: {int(df['outlier_flag'].sum())}")
    unknowns = []
    for name in ("housing_params.json", "opportunity_costs.json"):
        if (run_dir / name).exists():
            unknowns += read_json(run_dir / name).get("unknowns", [])
    if unknowns:
        lines += ["", "Datos sin fuente (se usan supuestos y se muestran como advertencia):"] + [f"  - {u}" for u in unknowns]
    if (run_dir / "analysis_summary.json").exists():
        s = read_json(run_dir / "analysis_summary.json")
        lines += ["", "Veredicto (% de escenarios en que comprar gana):"]
        for d in s["districts"]:
            v = ", ".join(f"{x['horizon']}a {x['label']} ({x['share_buy_wins']:.0%})" for x in d["verdicts"]) or "no analizado"
            lines.append(f"  {d['district']}: {v}")
    text = "\n".join(lines) + "\n"
    (run_dir / "validacion.txt").write_text(text, encoding="utf-8")
    latest = run_dir.parent / "validacion.txt"
    latest.write_text(text, encoding="utf-8")
    return latest


def cmd_figures(args) -> int:
    from .figures import make_figures
    from .loaders import load_run
    out = Path(args.out) if args.out else figures_dir()
    paths = make_figures(load_run(Path(args.run)), out)
    _print({"ok": True, "figures": [str(p) for p in paths]})
    return 0


def cmd_check_app(args) -> int:
    """AppTest smoke check that works anywhere (no repo tests needed): starts the app, moves three sliders."""
    import os
    from streamlit.testing.v1 import AppTest
    os.environ["HOUSING_LIMA_RUN"] = str(Path(args.run).resolve())
    at = AppTest.from_file(str(APP_FILE), default_timeout=120)
    at.run()
    errors = [e.message for e in at.exception]
    changed = {}
    if not errors:
        snap = lambda: [(m.label, m.value, m.delta) for m in at.metric]  # noqa: E731
        before = snap()
        for key, step in (("mortgage_rate", 1.0), ("down_payment", 10), ("discount", 5.0)):
            s = at.slider(key=key)
            s.set_value(s.value + step if s.value + step <= s.max else s.value - step).run()
            errors += [e.message for e in at.exception]
            now = snap()
            changed[key] = now != before
            before = now
    ok = not errors and all(changed.values())
    _print({"ok": ok, "metrics": len(at.metric), "controls_change_output": changed, "errors": errors})
    return 0 if ok else 1


def cmd_dashboard(args) -> int:
    cmd = [sys.executable, "-m", "streamlit", "run", str(APP_FILE), "--server.port", str(args.port)]
    if args.headless:
        cmd += ["--server.headless", "true"]
    cmd += ["--", "--run", str(Path(args.run).resolve())] if args.run else []
    return subprocess.call(cmd)


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

    s = sub.add_parser("figures", help="PNG figures of a run in figuras/")
    s.add_argument("--run", required=True)
    s.add_argument("--out")
    s.set_defaults(fn=cmd_figures)

    s = sub.add_parser("check-app", help="AppTest smoke check of the dashboard on a run")
    s.add_argument("--run", required=True)
    s.set_defaults(fn=cmd_check_app)

    s = sub.add_parser("dashboard", help="open the Streamlit dashboard for a run")
    s.add_argument("--run")
    s.add_argument("--port", type=int, default=8501)
    s.add_argument("--headless", action="store_true")
    s.set_defaults(fn=cmd_dashboard)

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
