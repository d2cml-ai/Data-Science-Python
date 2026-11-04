"""Static PNG figures of a run (200 dpi) for figures/. Same model and colors as the dashboard."""

from __future__ import annotations

import re
import unicodedata
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402
from matplotlib.colors import LinearSegmentedColormap, TwoSlopeNorm  # noqa: E402

from . import explain  # noqa: E402
from .analysis import build_scenario  # noqa: E402
from .loaders import RunData, load_defaults  # noqa: E402
from .model import simulate  # noqa: E402

BUY, RENT, MUTED, INK = "#2a78d6", "#eb6834", "#898781", "#0b0b0b"
SERIES = ["#2a78d6", "#eb6834", "#1baf7a", "#eda100", "#e87ba4", "#008300"]
DIVERGING = LinearSegmentedColormap.from_list("buy_rent", ["#b8302f", "#e98584", "#f0efec", "#86b6ef", "#1c5cab"])
OPTION_NAMES = {"deposit": "Fixed-term deposit", "sp500": "S&P 500", "bvl": "S&P/BVL Peru General"}

plt.rcParams.update({"font.family": "sans-serif", "axes.spines.top": False, "axes.spines.right": False,
                     "axes.edgecolor": "#c3c2b7", "axes.labelcolor": "#52514e", "xtick.color": "#52514e",
                     "ytick.color": "#52514e", "axes.grid": True, "grid.color": "#e1e0d9", "grid.linewidth": 0.6})


def slug(text: str) -> str:
    text = unicodedata.normalize("NFKD", text).encode("ascii", "ignore").decode().lower()
    return re.sub(r"[^a-z0-9]+", "_", text).strip("_")


def _footer(fig, run: RunData) -> None:
    note = (f"Source: listings collected on {run.market['collected_at']} ({run.market['source_mode']}); "
            "assumptions in analysis_report.md. Educational use only.")
    if run.synthetic:
        note = "SYNTHETIC test data, not market information.\n" + note
    fig.text(0.01, 0.01, note, fontsize=7, color=MUTED, ha="left", va="bottom", linespacing=1.4)


def verdict_chart(run: RunData, out: Path) -> Path:
    summary = run.summary
    districts = [d for d in summary["districts"] if d["verdicts"]]
    horizons = summary["horizons"]
    thr = summary["parameters"]["verdict_thresholds"]
    fig, ax = plt.subplots(figsize=(9, 4.8))
    width = 0.8 / max(len(districts), 1)
    x = np.arange(len(horizons))
    for i, d in enumerate(districts):
        shares = [100 * v["share_buy_wins"] for v in d["verdicts"]]
        bars = ax.bar(x + (i - (len(districts) - 1) / 2) * width, shares, width * 0.92, color=SERIES[i % len(SERIES)],
                      label=d["district"] + (" (low confidence)" if d["low_confidence"] else ""), zorder=2)
        ax.bar_label(bars, fmt="%.0f", fontsize=7, color="#52514e", padding=2)
    for y, txt in ((100 * thr["buy"], "buy"), (100 * thr["rent"], "rent")):
        ax.axhline(y, color=MUTED, lw=0.8, ls=":", zorder=1)
        ax.text(1.01, y, f"{txt}\nthreshold", fontsize=7, color=MUTED, ha="left", va="center",
                transform=ax.get_yaxis_transform())
    ax.set_xticks(x, [f"{h} years" for h in horizons])
    ax.set_ylim(0, 105)
    ax.set_ylabel("% of scenarios where buying wins")
    ax.set_title(f"Buy or rent? Share of scenarios where buying wins, by district and horizon ({run.run_id[:8]})",
                 fontsize=11, loc="left")
    ax.legend(frameon=False, fontsize=8, ncol=min(3, len(districts)), loc="upper left")
    _footer(fig, run)
    fig.tight_layout(rect=(0, 0.07, 1, 1))
    path = out / "verdicts.png"
    fig.savefig(path, dpi=200)
    plt.close(fig)
    return path


def wealth_chart(run: RunData, district: str, out: Path, defaults: dict) -> Path:
    s = build_scenario(run, district, defaults)
    r = simulate(s, years=30)
    y = r.yearly
    be, _ = r.break_even()
    fig, ax = plt.subplots(figsize=(8, 4.5))
    for col, name, color in (("w_buy", "Buyer", BUY), ("w_rent", "Renter", RENT)):
        ax.plot(y["year"], y[col] / 1000, color=color, lw=2, label=name)
        ax.text(y["year"].iloc[-1] + 0.4, y[col].iloc[-1] / 1000, name, color=INK, fontsize=8, va="center")
    if be is not None:
        ax.axvline(be, color=MUTED, lw=1, ls=":")
        ax.text(be + 0.3, ax.get_ylim()[1] * 0.95, f"break-even: year {be}", fontsize=8, color="#52514e")
    base_opt = sorted(run.opportunity["options"], key=lambda o: o["risk_rank"])[0]
    ax.set_xlim(0, 33)
    ax.set_xlabel("Year")
    ax.set_ylabel("Net wealth (thousand S/)")
    ax.set_title(f"{district}: wealth from buying vs renting and investing\n"
                 f"Price S/ {s.price:,.0f} · rent S/ {s.monthly_rent:,.0f} · mortgage {s.mortgage_rate:.2%} · "
                 f"{OPTION_NAMES.get(base_opt['id'], base_opt['name'])} {s.opportunity_return:.2%}", fontsize=10, loc="left")
    ax.legend(frameon=False, fontsize=8, loc="lower left")
    _footer(fig, run)
    fig.tight_layout(rect=(0, 0.08, 1, 1))
    path = out / f"{slug(district)}_wealth.png"
    fig.savefig(path, dpi=200)
    plt.close(fig)
    return path


def heatmap_chart(run: RunData, district: str, out: Path, horizon: int = 20) -> Path:
    res = run.results
    sub = res[(res["district"] == district) & (res["horizon"] == horizon)]
    pivot = sub.pivot(index="option_id", columns="mortgage_rate", values="delta")
    order = [o["id"] for o in sorted(run.opportunity["options"], key=lambda o: o["risk_rank"]) if o["id"] in pivot.index]
    pivot = pivot.loc[order]
    vmax = max(abs(pivot.values.min()), abs(pivot.values.max()), 1.0)
    fig, ax = plt.subplots(figsize=(8, 3.6))
    ax.grid(False)
    im = ax.imshow(pivot.values / 1000, cmap=DIVERGING, norm=TwoSlopeNorm(0, -vmax / 1000, vmax / 1000), aspect="auto")
    for (i, j), v in np.ndenumerate(pivot.values):
        ax.text(j, i, f"{v / 1000:+,.0f}k", ha="center", va="center", fontsize=8,
                color="#ffffff" if abs(v) > 0.6 * vmax else INK)
    ax.set_xticks(range(pivot.shape[1]), [f"{r:.2%}" for r in pivot.columns])
    ax.set_yticks(range(pivot.shape[0]), [OPTION_NAMES.get(i, i) for i in pivot.index])
    ax.set_xlabel("Mortgage rate (annual effective)")
    cb = fig.colorbar(im, ax=ax, fraction=0.04)
    cb.set_label("Buy − rent (thousand S/)", fontsize=8)
    ax.set_title(f"{district}: buy minus rent after {horizon} years (blue: buying wins; red: renting wins)",
                 fontsize=10, loc="left")
    _footer(fig, run)
    fig.tight_layout(rect=(0, 0.1, 1, 1))
    path = out / f"{slug(district)}_heatmap_{horizon}y.png"
    fig.savefig(path, dpi=200)
    plt.close(fig)
    return path


SPENT, SHARED = "#c3c2b7", "#e1e0d9"


def _k(v: float) -> str:
    if abs(v) < 500:
        return "S/ 0"
    return ("−" if v < 0 else "") + f"S/ {abs(v) / 1000:,.0f}k"


def explained_chart(run: RunData, district: str, out: Path, defaults: dict, horizon: int = 20) -> Path:
    """One page that explains the result: monthly money in year 1, wealth after `horizon` years, flip points."""
    s = build_scenario(run, district, defaults)
    split = explain.first_year_monthly(s)
    bd = explain.wealth_breakdown(s, horizon)
    flips = explain.flip_points(s, horizon, ["mortgage_rate", "opportunity_return", "price_growth", "monthly_rent",
                                              "price"])
    fig = plt.figure(figsize=(10, 8.6))
    gs = fig.add_gridspec(3, 2, height_ratios=[0.8, 1.6, 0.75], hspace=0.62, wspace=0.12)

    # A. same money every month
    ax = fig.add_subplot(gs[0, :])
    ax.grid(False)
    for row, (side, label) in enumerate((("buyer", "Buyer"), ("renter", "Renter"))):
        left = 0.0
        for name, value in split[side].items():
            if abs(value) < 0.5:
                continue
            if value < 0:  # rent above the buyer's costs: the renter draws from savings, drawn left of zero
                ax.barh(row, value, left=0, color=SPENT, edgecolor="#fcfcfb", linewidth=2, height=0.62, hatch="//")
                continue
            kept = name.startswith("Mortgage principal") or name.startswith("Invested")
            color = SHARED if name.startswith("Building fee") else (BUY if side == "buyer" else RENT) if kept else SPENT
            ax.barh(row, value, left=left, color=color, edgecolor="#fcfcfb", linewidth=2, height=0.62)
            if value > 0.09 * split["total"]:
                short = name.split(" (")[0].replace("Invested each month", "Invested")
                ax.text(left + value / 2, row, f"{short}\nS/ {value:,.0f}", ha="center", va="center", fontsize=7.5,
                        color="#ffffff" if kept else INK)
            left += value
    ax.set_yticks([0, 1], ["Buyer", "Renter"])
    ax.invert_yaxis()
    ax.set_xlim(min(0.0, split["renter"]["Invested each month (difference)"]) * 1.05, split["total"] * 1.01)
    ax.set_xlabel("S/ per month, year-1 average", fontsize=8)
    ax.set_title(f"A. Both spend the same S/ {split['total']:,.0f} a month in year 1.\n"
                 "Colored = builds wealth; gray = gone (interest, tax, insurance, rent); "
                 "light gray = building fee, paid by both", fontsize=9, loc="left")

    # B. what each owns after the horizon
    for col, side, total, color, label in ((0, "buyer", bd["w_buy"], BUY, "Buyer"),
                                           (1, "renter", bd["w_rent"], RENT, "Renter")):
        axb = fig.add_subplot(gs[1, col], sharey=None)
        level, xs = 0.0, []
        for i, (name, value) in enumerate(bd[side]):
            bottom = level if value >= 0 else level + value
            axb.bar(i, abs(value), bottom=bottom, color=color if value >= 0 else SPENT, width=0.7, zorder=2)
            axb.text(i, max(level, level + value) + 0.01 * bd["w_buy"], _k(value), ha="center", va="bottom", fontsize=7.5)
            level += value
            xs.append(name.replace(" ", "\n", 1))
        n = len(bd[side])
        axb.bar(n, total, color=color, width=0.7, edgecolor=INK, linewidth=1.2, zorder=2)
        axb.text(n, total + 0.01 * bd["w_buy"], _k(total), ha="center", va="bottom", fontsize=8, fontweight="bold")
        axb.set_xticks(range(n + 1), xs + ["Wealth"], fontsize=7.5)
        axb.yaxis.set_major_formatter(lambda v, _: f"{v / 1000:,.0f}k")
        axb.set_title(f"{'B. ' if col == 0 else ''}{label} after {horizon} years: S/ {total:,.0f}", fontsize=9, loc="left")
        if col == 0:
            top = max(bd["w_buy"], bd["w_rent"], max(v for _, v in bd["buyer"])) * 1.12
        axb.set_ylim(0, top)

    # C. flip points
    axc = fig.add_subplot(gs[2, :])
    axc.axis("off")
    winner = "Buying" if bd["delta"] > 0 else "Renting"
    lines = [f"C. {winner} wins by S/ {abs(bd['delta']):,.0f} after {horizon} years. "
             "The answer flips if one input alone moves to:"]
    lines += ["     •  " + f.sentence() for f in flips]
    axc.text(0, 1, "\n".join(lines), fontsize=8.5, va="top", ha="left", color=INK, linespacing=1.7,
             transform=axc.transAxes)

    base_opt = sorted(run.opportunity["options"], key=lambda o: o["risk_rank"])[0]
    fig.suptitle(f"{district}: how the recommendation was made\nPrice S/ {s.price:,.0f} · rent S/ {s.monthly_rent:,.0f} · "
                 f"mortgage {s.mortgage_rate:.2%} · down payment {s.down_payment_pct:.0%} · "
                 f"{OPTION_NAMES.get(base_opt['id'], base_opt['name'])} {s.opportunity_return:.2%} · "
                 f"loan {s.loan_term_years} years", fontsize=10, x=0.01, ha="left")
    _footer(fig, run)
    fig.subplots_adjust(left=0.08, right=0.98, top=0.89, bottom=0.05)
    path = out / f"{slug(district)}_explained_{horizon}y.png"
    fig.savefig(path, dpi=200)
    plt.close(fig)
    return path


def make_figures(run: RunData, out: Path) -> list[Path]:
    if run.summary is None or run.results is None:
        raise ValueError("Run the analysis first: analysis_summary.json and analysis_results.csv are missing.")
    out.mkdir(parents=True, exist_ok=True)
    defaults = load_defaults()
    paths = [verdict_chart(run, out)]
    for d in run.summary["districts"]:
        if d["verdicts"]:
            paths.append(wealth_chart(run, d["district"], out, defaults))
            paths.append(heatmap_chart(run, d["district"], out))
            paths.append(explained_chart(run, d["district"], out, defaults))
    return paths
