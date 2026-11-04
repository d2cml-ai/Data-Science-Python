"""Financial-analysis agent engine: parameter resolution, scenario grid, verdicts and reports.

Market numbers come only from the run folder. When a researched value is null, a clearly
named fallback from config/defaults.yaml is used and a warning is recorded; nothing is
silently set to zero.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Optional

import pandas as pd

from . import DISCLAIMER
from .loaders import RunData, load_defaults, load_run, write_json
from .model import Scenario, rate_grid, simulate
from .validate import ValidationFailed, validate_json

OPTION_NAMES_EN = {"deposit": "the fixed-term deposit", "sp500": "the S&P 500", "bvl": "the S&P/BVL Peru General"}


class AnalysisError(Exception):
    pass


@dataclass
class ResolvedParams:
    values: dict
    sources: dict
    warnings: list[str] = field(default_factory=list)


def _sv(obj: Optional[dict]) -> tuple[Optional[float], dict]:
    obj = obj or {}
    return obj.get("value"), obj


def market_mortgage_rate(params: dict) -> tuple[float, dict, list[str]]:
    value, src = _sv(params["mortgage"].get("average_tea"))
    if value is not None:
        return float(value), {"origin": "researched", **src}, []
    banks = params["mortgage"].get("by_bank") or []
    if banks:
        avg = sum(b["tea"] for b in banks) / len(banks)
        return avg, {"origin": "mean of bank rates", "source_url": banks[0]["source_url"], "as_of": banks[0]["as_of"]}, [
            "average mortgage rate (SBS) unknown: used the simple mean of the bank rates found"]
    raise AnalysisError("The market mortgage rate is unknown and no bank rates were found; the user must supply one.")


def resolve_params(run: RunData, district: str, defaults: dict) -> ResolvedParams:
    p, fb = run.params, defaults["fallbacks"]
    values, sources, warnings = {}, {}, []

    def take(name: str, sourced: Optional[dict], fallback):
        value, src = _sv(sourced)
        if value is not None:
            values[name], sources[name] = float(value), {"origin": "researched", **src}
            return
        if fallback == "inflation":
            fallback = values["inflation"]
            label = "assumed equal to inflation (0% real)"
        else:
            label = f"assumption from defaults.yaml = {fallback}"
        values[name], sources[name] = float(fallback), {"origin": "fallback", "note": label}
        warnings.append(f"{name} unknown: {label}")

    take("inflation", p.get("inflation"), fb["inflation"])
    take("price_growth", (p.get("price_growth_by_district") or {}).get(district) or p.get("price_growth"), fb["price_growth"])
    take("rent_growth", (p.get("rent_growth_by_district") or {}).get(district) or p.get("rent_growth"), fb["rent_growth"])
    for name in ("buy_cost_pct", "sell_cost_pct", "property_tax_pct", "insurance_pct"):
        take(name, p.get(name), fb[name])

    md = run.district(district)
    fee = md["rent"].get("maintenance_fee_median") or md["sale"].get("maintenance_fee_median")
    if fee is not None:
        values["maintenance_fee_monthly"] = float(fee)
        sources["maintenance_fee_monthly"] = {"origin": "researched", "note": "median of listings", "source_url": "listings.csv",
                                              "as_of": run.market["collected_at"]}
    else:
        values["maintenance_fee_monthly"] = float(fb["maintenance_fee_monthly"])
        sources["maintenance_fee_monthly"] = {"origin": "fallback", "note": "no fee listed"}
        warnings.append(f"maintenance fee unknown in {district}: assumption {fb['maintenance_fee_monthly']} soles/month")

    rate, rate_src, rate_warn = market_mortgage_rate(p)
    values["mortgage_rate"], sources["mortgage_rate"] = rate, rate_src
    warnings.extend(rate_warn)
    return ResolvedParams(values, sources, warnings)


def build_scenario(run: RunData, district: str, defaults: dict, resolved: Optional[ResolvedParams] = None,
                   **overrides) -> Scenario:
    """Scenario for one district from the run folder; keyword overrides win (used by the dashboard)."""
    resolved = resolved or resolve_params(run, district, defaults)
    md = run.district(district)
    price, rent = md["sale"]["realistic_price"], md["rent"]["realistic_rent"]
    if price is None or rent is None:
        raise AnalysisError(f"{district}: no realistic price or rent (no usable listings)")
    base_option = sorted(run.opportunity["options"], key=lambda o: o["risk_rank"])[0]
    v = resolved.values
    kwargs = dict(
        price=price, monthly_rent=rent,
        down_payment_pct=run.inputs["down_payment_pct"] / 100.0,
        mortgage_rate=v["mortgage_rate"], opportunity_return=base_option["return_base"],
        price_growth=v["price_growth"], rent_growth=v["rent_growth"], inflation=v["inflation"],
        buy_cost_pct=v["buy_cost_pct"], sell_cost_pct=v["sell_cost_pct"],
        property_tax_pct=v["property_tax_pct"], insurance_pct=v["insurance_pct"],
        maintenance_fee_monthly=v["maintenance_fee_monthly"],
        loan_term_years=defaults["loan_term_years"],
        negotiation_discount=run.market.get("negotiation_discount", defaults["negotiation_discount"]),
        renter_pays_maintenance=defaults["renter_pays_maintenance"],
    )
    kwargs.update(overrides)
    return Scenario(**kwargs)


def verdict_label(share: float, thresholds: dict) -> str:
    if share >= thresholds["buy"]:
        return "buy"
    if share <= thresholds["rent"]:
        return "rent"
    return "depends"


def run_global_warnings(run: RunData) -> list[str]:
    warnings = [f"unknown: {u}" for u in run.params.get("unknowns", [])]
    warnings += [f"unknown: {u}" for u in run.opportunity.get("unknowns", [])]
    if run.market["source_mode"] != "live":
        warnings.append(f"listings source_mode is '{run.market['source_mode']}': data came (partly) from a CSV file, not a live search")
    if run.synthetic:
        warnings.append("SYNTHETIC fixture data: not real market information")
    return warnings


def analyze(run: RunData, defaults: Optional[dict] = None) -> tuple[pd.DataFrame, dict]:
    defaults = defaults or load_defaults()
    horizons = defaults["horizons"]
    years = max(defaults["scan_years"], max(horizons))
    market_rate, _, _ = market_mortgage_rate(run.params)
    grid = rate_grid(market_rate, defaults["mortgage_rate_offsets"], defaults["min_mortgage_rate"])
    options = sorted(run.opportunity["options"], key=lambda o: o["risk_rank"])
    thresholds = defaults["verdict_thresholds"]

    rows, districts_out = [], []
    global_warnings = run_global_warnings(run)
    for md in run.market["districts"]:
        name = md["district"]
        d_warn = list(md.get("warnings", []))
        try:
            resolved = resolve_params(run, name, defaults)
            base = build_scenario(run, name, defaults, resolved)
        except AnalysisError as exc:
            districts_out.append({"district": name, "low_confidence": True, "verdicts": [], "break_even": [],
                                  "sensitivity": [], "verdict_text": f"{name}: not analysed ({exc}).",
                                  "warnings": d_warn + [str(exc)]})
            continue
        d_warn += resolved.warnings
        break_evens = []
        exhausted_any = False
        for rate in grid:
            for opt in options:
                sim = simulate(base.with_(mortgage_rate=rate, opportunity_return=opt["return_base"]), years=years)
                be_year, be_reverts = sim.break_even()
                exhausted_any |= sim.renter_budget_exhausted
                if abs(rate - market_rate) < 1e-9:
                    break_evens.append({"option_id": opt["id"], "mortgage_rate": rate,
                                        "break_even_year": be_year, "reverts": be_reverts})
                for h in horizons:
                    r = sim.at(h)
                    rows.append({
                        "district": name, "horizon": h, "mortgage_rate": rate,
                        "rate_offset": round(rate - market_rate, 6), "option_id": opt["id"],
                        "opportunity_return": opt["return_base"],
                        "w_buy": round(r["w_buy"], 2), "w_rent": round(r["w_rent"], 2), "delta": round(r["delta"], 2),
                        "w_buy_real": round(r["w_buy_real"], 2), "w_rent_real": round(r["w_rent_real"], 2),
                        "delta_real": round(r["delta_real"], 2), "buy_wins": bool(r["delta"] > 0),
                        "break_even_year": be_year, "break_even_reverts": be_reverts,
                        "renter_budget_exhausted": sim.renter_budget_exhausted,
                        "low_confidence": md["low_confidence"],
                    })
        if exhausted_any:
            d_warn.append("renter_budget_exhausted: in some scenarios the renter's portfolio goes negative")

        d_rows = pd.DataFrame([r for r in rows if r["district"] == name])
        verdicts = []
        for h in horizons:
            sub = d_rows[d_rows["horizon"] == h]
            share = float(sub["buy_wins"].mean())
            at_market = sub[(sub["rate_offset"].abs() < 1e-9)]
            verdicts.append({"horizon": h, "share_buy_wins": round(share, 4), "label": verdict_label(share, thresholds),
                             "delta_market_rate_by_option": {r.option_id: r.delta for r in at_market.itertuples()}})

        districts_out.append({
            "district": name, "low_confidence": md["low_confidence"],
            "price_used": base.price, "rent_used": base.monthly_rent,
            "parameters": resolved.values, "parameter_sources": resolved.sources,
            "verdicts": verdicts, "break_even": break_evens,
            "sensitivity": sensitivity(base, market_rate, options, defaults),
            "verdict_text": verdict_text(name, market_rate, break_evens, verdicts, md["low_confidence"]),
            "warnings": sorted(set(d_warn)),
        })

    results = pd.DataFrame(rows)
    summary = {
        "run_id": run.run_id,
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "synthetic": run.synthetic,
        "source_mode": run.market["source_mode"],
        "horizons": horizons,
        "mortgage_rate_grid": grid,
        "market_mortgage_rate": market_rate,
        "options": [{"id": o["id"], "name": o["name"], "return_base": o["return_base"], "risk_rank": o["risk_rank"]} for o in options],
        "parameters": {"loan_term_years": defaults["loan_term_years"], "down_payment_pct": run.inputs["down_payment_pct"],
                       "verdict_thresholds": thresholds, "renter_pays_maintenance": defaults["renter_pays_maintenance"],
                       "negotiation_discount": run.market.get("negotiation_discount", defaults["negotiation_discount"])},
        "districts": districts_out,
        "warnings": global_warnings,
        "disclaimer": DISCLAIMER,
    }
    return results, summary


def sensitivity(base: Scenario, market_rate: float, options: list[dict], defaults: dict) -> list[dict]:
    cfg = defaults["sensitivity"]
    out = []
    years = max(cfg["horizons"])
    for opt in options:
        s0 = base.with_(mortgage_rate=market_rate, opportunity_return=opt["return_base"])
        cases = [("price_growth", s0.price_growth + d, {"price_growth": s0.price_growth + d}) for d in cfg["price_growth_delta"]]
        cases += [("rent_growth", s0.rent_growth + d, {"rent_growth": s0.rent_growth + d}) for d in cfg["rent_growth_delta"]]
        cases += [("negotiation_discount", d, {"negotiation_discount": d}) for d in cfg["negotiation_discount"]]
        for param, value, change in cases:
            sim = simulate(s0.with_(**change), years=years)
            for h in cfg["horizons"]:
                out.append({"option_id": opt["id"], "parameter": param, "value": round(value, 6),
                            "horizon": h, "delta": round(float(sim.at(h)["delta"]), 2)})
    return out


def verdict_text(name: str, market_rate: float, break_evens: list[dict], verdicts: list[dict], low_conf: bool) -> str:
    parts = []
    for be in break_evens:
        opt = OPTION_NAMES_EN.get(be["option_id"], be["option_id"])
        if be["break_even_year"] is None:
            parts.append(f"renting wins for all 30 years against {opt}")
        else:
            tail = " (but the advantage reverses later)" if be["reverts"] else ""
            parts.append(f"buying wins from year {be['break_even_year']} against {opt}{tail}")
    shares = ", ".join(f"{v['share_buy_wins']:.0%} at {v['horizon']}y" for v in verdicts)
    text = (f"{name}: at the market mortgage rate ({market_rate:.2%}), " + "; ".join(parts) +
            f". Share of grid scenarios where buying wins: {shares}.")
    if low_conf:
        text += " Low confidence: few listings."
    return text


def write_report(path: Path, run: RunData, summary: dict) -> None:
    lines = [f"# Buy vs rent analysis: {run.run_id}", ""]
    if summary["synthetic"]:
        lines += ["> **SYNTHETIC DATA.** This run uses a labelled fixture, not real listings.", ""]
    lines += [
        "## Method", "",
        "For each district, the buyer pays the realistic price (median of in-range listings) with the user's down payment "
        "and a fixed-payment mortgage. The renter rents a comparable home and invests the down payment, the buying costs "
        "and every monthly difference between the buyer's outflow and the rent at the opportunity-cost return. "
        "Buying wins at horizon H when the buyer's net wealth (sale value after selling costs minus the remaining balance) "
        "exceeds the renter's portfolio.", "",
        f"- Mortgage rate grid (TEA): {', '.join(f'{r:.2%}' for r in summary['mortgage_rate_grid'])} "
        f"(market average {summary['market_mortgage_rate']:.2%})",
        f"- Opportunity-cost options (base return): " + ", ".join(f"{o['name']} {o['return_base']:.2%}" for o in summary["options"]),
        f"- Loan term: {summary['parameters']['loan_term_years']} years (assumption); down payment: {summary['parameters']['down_payment_pct']}%",
        f"- Verdict: 'buy' when buying wins in >= {summary['parameters']['verdict_thresholds']['buy']:.0%} of the grid, "
        f"'rent' when <= {summary['parameters']['verdict_thresholds']['rent']:.0%}, otherwise 'depends'.", "",
        "## Results", "",
        "| District | Price | Rent/month | " + " | ".join(f"{h}y" for h in summary["horizons"]) + " |",
        "| --- | ---: | ---: | " + " | ".join("---" for _ in summary["horizons"]) + " |",
    ]
    for d in summary["districts"]:
        if not d["verdicts"]:
            lines.append(f"| {d['district']} | - | - | " + " | ".join("n/a" for _ in summary["horizons"]) + " |")
            continue
        cells = " | ".join(f"{v['label']} ({v['share_buy_wins']:.0%})" for v in d["verdicts"])
        flag = " (low confidence)" if d["low_confidence"] else ""
        lines.append(f"| {d['district']}{flag} | S/ {d['price_used']:,.0f} | S/ {d['rent_used']:,.0f} | {cells} |")
    lines += ["", "## Verdicts", ""] + [f"- {d['verdict_text']}" for d in summary["districts"]]
    lines += ["", "## Warnings and caveats", ""]
    all_warn = summary["warnings"] + [f"{d['district']}: {w}" for d in summary["districts"] for w in d.get("warnings", [])]
    lines += [f"- {w}" for w in all_warn] or ["- None"]
    lines += ["- Asking prices are not transaction prices; see the negotiation discount.",
              "- Deposit rates observed today are not guaranteed for 30 years.",
              "- Subsidies (e.g. Bono del Buen Pagador) are not modelled in v1.",
              "", "## Disclaimer", "", summary["disclaimer"], ""]
    Path(path).write_text("\n".join(lines), encoding="utf-8")


def run_analysis(run_dir: Path, defaults: Optional[dict] = None) -> dict:
    """Agent 3 entry point: read the research files, write the three analysis outputs."""
    run_dir = Path(run_dir)
    run = load_run(run_dir, validate=True)
    results, summary = analyze(run, defaults)
    validate_json(summary, "analysis_summary.schema.json")
    results.to_csv(run_dir / "analysis_results.csv", index=False)
    write_json(run_dir / "analysis_summary.json", summary)
    write_report(run_dir / "analysis_report.md", run, summary)
    return summary


__all__ = ["AnalysisError", "ValidationFailed", "analyze", "build_scenario", "resolve_params", "run_analysis",
           "market_mortgage_rate", "verdict_label"]
