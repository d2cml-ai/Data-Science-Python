"""Static PNG figures of a run (200 dpi) for figuras/. Same model and colors as the dashboard."""

from __future__ import annotations

import re
import unicodedata
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402
from matplotlib.colors import LinearSegmentedColormap, TwoSlopeNorm  # noqa: E402

from .analysis import build_scenario  # noqa: E402
from .loaders import RunData, load_defaults  # noqa: E402
from .model import simulate  # noqa: E402

BUY, RENT, MUTED, INK = "#2a78d6", "#eb6834", "#898781", "#0b0b0b"
SERIES = ["#2a78d6", "#eb6834", "#1baf7a", "#eda100", "#e87ba4", "#008300"]
DIVERGING = LinearSegmentedColormap.from_list("buy_rent", ["#b8302f", "#e98584", "#f0efec", "#86b6ef", "#1c5cab"])
OPTION_ES = {"deposit": "Depósito a plazo", "sp500": "S&P 500", "bvl": "BVL Perú General"}

plt.rcParams.update({"font.family": "sans-serif", "axes.spines.top": False, "axes.spines.right": False,
                     "axes.edgecolor": "#c3c2b7", "axes.labelcolor": "#52514e", "xtick.color": "#52514e",
                     "ytick.color": "#52514e", "axes.grid": True, "grid.color": "#e1e0d9", "grid.linewidth": 0.6})


def slug(text: str) -> str:
    text = unicodedata.normalize("NFKD", text).encode("ascii", "ignore").decode().lower()
    return re.sub(r"[^a-z0-9]+", "_", text).strip("_")


def _footer(fig, run: RunData) -> None:
    note = (f"Fuente: avisos recolectados el {run.market['collected_at']} ({run.market['source_mode']}); "
            "supuestos en analysis_report.md. Uso educativo.")
    if run.synthetic:
        note = "DATOS SINTÉTICOS de prueba, no son información de mercado.\n" + note
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
                      label=d["district"] + (" (baja confianza)" if d["low_confidence"] else ""), zorder=2)
        ax.bar_label(bars, fmt="%.0f", fontsize=7, color="#52514e", padding=2)
    for y, txt in ((100 * thr["buy"], "comprar"), (100 * thr["rent"], "alquilar")):
        ax.axhline(y, color=MUTED, lw=0.8, ls=":", zorder=1)
        ax.text(1.01, y, f"umbral\n{txt}", fontsize=7, color=MUTED, ha="left", va="center",
                transform=ax.get_yaxis_transform())
    ax.set_xticks(x, [f"{h} años" for h in horizons])
    ax.set_ylim(0, 105)
    ax.set_ylabel("% de escenarios en que comprar gana")
    ax.set_title(f"¿Comprar o alquilar? Escenarios en que comprar gana, por distrito y horizonte ({run.run_id[:8]})",
                 fontsize=11, loc="left")
    ax.legend(frameon=False, fontsize=8, ncol=min(3, len(districts)), loc="upper left")
    _footer(fig, run)
    fig.tight_layout(rect=(0, 0.07, 1, 1))
    path = out / "veredictos.png"
    fig.savefig(path, dpi=200)
    plt.close(fig)
    return path


def wealth_chart(run: RunData, district: str, out: Path, defaults: dict) -> Path:
    s = build_scenario(run, district, defaults)
    r = simulate(s, years=30)
    y = r.yearly
    be, _ = r.break_even()
    fig, ax = plt.subplots(figsize=(8, 4.5))
    for col, name, color in (("w_buy", "Comprador", BUY), ("w_rent", "Inquilino", RENT)):
        ax.plot(y["year"], y[col] / 1000, color=color, lw=2, label=name)
        ax.text(y["year"].iloc[-1] + 0.4, y[col].iloc[-1] / 1000, name, color=INK, fontsize=8, va="center")
    if be is not None:
        ax.axvline(be, color=MUTED, lw=1, ls=":")
        ax.text(be + 0.3, ax.get_ylim()[1] * 0.95, f"punto de equilibrio: año {be}", fontsize=8, color="#52514e")
    base_opt = sorted(run.opportunity["options"], key=lambda o: o["risk_rank"])[0]
    ax.set_xlim(0, 33)
    ax.set_xlabel("Año")
    ax.set_ylabel("Patrimonio neto (miles de S/)")
    ax.set_title(f"{district}: patrimonio de comprar vs alquilar e invertir\n"
                 f"Precio S/ {s.price:,.0f} · alquiler S/ {s.monthly_rent:,.0f} · TEA {s.mortgage_rate:.2%} · "
                 f"{OPTION_ES.get(base_opt['id'], base_opt['name'])} {s.opportunity_return:.2%}", fontsize=10, loc="left")
    ax.legend(frameon=False, fontsize=8, loc="lower left")
    _footer(fig, run)
    fig.tight_layout(rect=(0, 0.08, 1, 1))
    path = out / f"{slug(district)}_patrimonio.png"
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
    ax.set_yticks(range(pivot.shape[0]), [OPTION_ES.get(i, i) for i in pivot.index])
    ax.set_xlabel("Tasa hipotecaria (TEA)")
    cb = fig.colorbar(im, ax=ax, fraction=0.04)
    cb.set_label("Comprar − alquilar (miles de S/)", fontsize=8)
    ax.set_title(f"{district}: comprar menos alquilar a {horizon} años (azul: comprar gana; rojo: alquilar gana)",
                 fontsize=10, loc="left")
    _footer(fig, run)
    fig.tight_layout(rect=(0, 0.1, 1, 1))
    path = out / f"{slug(district)}_mapa_calor_{horizon}a.png"
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
    return paths
