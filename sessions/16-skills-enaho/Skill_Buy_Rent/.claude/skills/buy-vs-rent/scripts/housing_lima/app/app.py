"""Buy vs rent dashboard for Lima.

Launch: python .claude/skills/buy-vs-rent/scripts/hl.py dashboard --run salidas/<run-id>
Reads one run folder and makes no network calls. All formulas come from housing_lima.model.
"""

from __future__ import annotations

import sys
from pathlib import Path

APP_DIR = Path(__file__).resolve().parent
for p in (APP_DIR, APP_DIR.parents[1]):  # app/ and the scripts/ folder that holds housing_lima
    if str(p) not in sys.path:
        sys.path.insert(0, str(p))

import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402
import streamlit as st  # noqa: E402

import labels as L  # noqa: E402
import state  # noqa: E402
from components import cards, charts  # noqa: E402
from housing_lima import DISCLAIMER_ES  # noqa: E402
from housing_lima.analysis import build_scenario, resolve_params  # noqa: E402
from housing_lima.model import Scenario, simulate  # noqa: E402
from housing_lima.returns import usd_to_pen  # noqa: E402

st.set_page_config(page_title="Comprar vs alquilar en Lima", page_icon="🏠", layout="wide")


@st.cache_data(show_spinner=False)
def run_sim(s: Scenario, years: int = 30) -> tuple[pd.DataFrame, object, bool]:
    r = simulate(s, years=years)
    return r.yearly, r.break_even(), r.renter_budget_exhausted


@st.cache_data(show_spinner=False)
def heat_grid(s: Scenario, horizon: int, rates: tuple, returns: tuple) -> pd.DataFrame:
    rows = []
    for rate in rates:
        for ret in returns:
            r = simulate(s.with_(mortgage_rate=rate, opportunity_return=ret), years=horizon)
            rows.append({"mortgage_rate": rate, "opportunity_return": ret, "delta": float(r.at(horizon)["delta"])})
    return pd.DataFrame(rows)


def pct(x: float) -> float:
    return round(100 * x, 2)


# ---------------------------------------------------------------- run selection
runs = state.available_runs()
run_labels = [p.name for p in runs]
defaults = state.cached_defaults()

st.sidebar.header("Controles")
run_idx = st.sidebar.selectbox(L.RUN, range(len(runs)), format_func=lambda i: run_labels[i], key="run")
run = state.cached_run(str(runs[run_idx]))
summary = run.summary or {}

st.title(L.TITLE)
st.caption(L.SUBTITLE)
if run.synthetic:
    st.warning(L.SYNTHETIC, icon="⚠️")
if run.market["source_mode"] != "live":
    st.info(L.CSV_MODE, icon="ℹ️")

analysable = [d["district"] for d in run.market["districts"]
              if d["sale"]["realistic_price"] is not None and d["rent"]["realistic_rent"] is not None]
if not analysable:
    st.error("Ningún distrito tiene suficientes avisos para analizar.")
    st.stop()

# ---------------------------------------------------------------- sidebar controls
district = st.sidebar.selectbox(L.DISTRICT, analysable, key="district")
dd = state.district_defaults(run, district, defaults)
market_rate = dd["values"]["mortgage_rate"]
grid = summary.get("mortgage_rate_grid") or [market_rate]

rate_lo = max(0.5, pct(min(grid)) - 1.0)
rate_hi = pct(max(grid)) + 1.0
mortgage_rate = st.sidebar.slider(L.MORTGAGE_RATE, rate_lo, rate_hi, pct(market_rate), 0.05, format="%.2f%%",
                                  key="mortgage_rate",
                                  help=f"Por defecto, el promedio de mercado ({pct(market_rate):.2f}%).") / 100

down_payment = st.sidebar.slider(L.DOWN_PAYMENT, 5, 50, int(round(run.inputs["down_payment_pct"])), 1,
                                 format="%d%%", key="down_payment") / 100

options = sorted(run.opportunity["options"], key=lambda o: o["risk_rank"])
opt_ids = [o["id"] for o in options] + ["custom"]
opt_names = {o["id"]: o["name"] for o in options} | {"custom": L.CUSTOM_RATE}
opt_id = st.sidebar.radio(L.OPPORTUNITY, opt_ids, format_func=lambda i: opt_names[i], key="option")
if opt_id == "custom":
    base_ret = options[0]["return_base"]
    opp_return = st.sidebar.slider(L.RETURN, -5.0, 20.0, pct(base_ret), 0.05, format="%.2f%%", key="ret_custom") / 100
else:
    opt = run.option(opt_id)
    level = st.sidebar.radio(L.SCENARIO_LEVEL, ["low", "base", "high"], index=1, horizontal=True,
                             format_func=lambda k: L.LEVELS[k], key=f"level_{opt_id}")
    if opt.get("return_usd_base") is not None:
        fx_change = st.sidebar.slider(L.FX_CHANGE, -5.0, 5.0, pct(run.opportunity["fx_change_assumption"]), 0.1,
                                      format="%.1f%%", key="fx_change") / 100
        preset = usd_to_pen(opt[f"return_usd_{level}"], fx_change)
    else:
        preset = opt[f"return_{level}"]
    opp_return = st.sidebar.slider(L.RETURN, -5.0, 20.0, pct(preset), 0.05, format="%.2f%%",
                                   key=f"ret_{opt_id}_{level}_{pct(preset)}") / 100

pmin, pmax = float(run.inputs["price_min_pen"]), float(run.inputs["price_max_pen"])
price = st.sidebar.slider(L.PRICE, pmin, pmax, float(np.clip(dd["price"], pmin, pmax)), 1000.0, format="%.0f",
                          key=f"price_{district}",
                          help=f"Por defecto, la mediana de los avisos encontrados. P25–P75: "
                               f"S/ {dd['price_p25']:,.0f} – S/ {dd['price_p75']:,.0f}.")
st.sidebar.caption(f"Avisos reales P25–P75: S/ {dd['price_p25']:,.0f} – S/ {dd['price_p75']:,.0f}")

discount = st.sidebar.slider(L.DISCOUNT, 0.0, 20.0, pct(run.market.get("negotiation_discount", 0.0)), 0.5,
                             format="%.1f%%", key="discount") / 100
terms = [10, 15, 20, 25, 30]
loan_term = st.sidebar.selectbox(L.LOAN_TERM, terms, index=terms.index(defaults["loan_term_years"]), key="loan_term")


def growth_slider(name: str, label: str) -> float:
    src = dd["sources"][name]
    tag = f" ({L.NEEDS_INPUT})" if src.get("origin") == "fallback" else ""
    v = st.sidebar.slider(label + tag, -5.0, 10.0, pct(dd["values"][name]), 0.1, format="%.1f%%",
                          key=f"{name}_{district}")
    if tag:
        st.sidebar.caption(f"⚠️ {L.PARAM_NAMES[name]}: sin fuente; se usa un supuesto. Ajústalo con tu dato.")
    return v / 100


price_growth = growth_slider("price_growth", L.PRICE_GROWTH)
rent_growth = growth_slider("rent_growth", L.RENT_GROWTH)
real = st.sidebar.toggle(L.REAL, value=False, key="real")

common = dict(mortgage_rate=mortgage_rate, down_payment_pct=down_payment, opportunity_return=opp_return,
              negotiation_discount=discount, loan_term_years=loan_term)
detail = build_scenario(run, district, defaults, **common, price=price, price_growth=price_growth,
                        rent_growth=rent_growth)
dcol = "delta_real" if real else "delta"

# ---------------------------------------------------------------- 1. verdict cards
st.subheader(L.SEC_VERDICTS)
st.caption("Con los controles actuales. El precio y los crecimientos elegidos aplican al distrito del detalle; "
           "los demás distritos usan su precio realista y sus parámetros.")
horizons = summary.get("horizons") or defaults["horizons"]
all_rows = []
for name in analysable:
    s = detail if name == district else build_scenario(run, name, defaults, **common)
    yearly, (be, reverts), _ = run_sim(s)
    deltas = {h: float(yearly.loc[yearly.year == h, dcol].iloc[0]) for h in horizons}
    grid_labels = {}
    for d in summary.get("districts", []):
        if d["district"] == name:
            grid_labels = {v["horizon"]: v["label"] for v in d["verdicts"]}
    cards.verdict_row(name, deltas, run.district(name)["low_confidence"], grid_labels, real)
    for h in horizons:
        r = yearly.loc[yearly.year == h].iloc[0]
        all_rows.append({"distrito": name, "horizonte": h, "precio": s.price, "alquiler": s.monthly_rent,
                         "patrimonio_comprador": r["w_buy_real" if real else "w_buy"],
                         "patrimonio_inquilino": r["w_rent_real" if real else "w_rent"],
                         "comprar_menos_alquilar": r[dcol], "punto_equilibrio": be})

# ---------------------------------------------------------------- 2. heat map
st.subheader(L.SEC_HEATMAP)
horizon = st.select_slider(L.HORIZON, horizons, value=horizons[min(1, len(horizons) - 1)], key="horizon")
rates = tuple(sorted({round(max(mortgage_rate + o, 0.001), 6) for o in np.arange(-0.02, 0.0201, 0.005)}))
returns = tuple(sorted({round(x, 6) for x in np.linspace(0.0, 0.14, 8)} | {round(opp_return, 6)}))
hm = heat_grid(detail, horizon, rates, returns)
if real:
    hm = hm.assign(delta=hm["delta"] / (1 + detail.inflation) ** horizon)
st.plotly_chart(charts.heatmap(hm, horizon, mortgage_rate, opp_return), width="stretch", key="heatmap")
st.caption(f"{district}. Cada celda: patrimonio del comprador menos el del inquilino (S/) a {horizon} años. "
           "El círculo marca el escenario actual.")

# ---------------------------------------------------------------- 3. wealth over time
st.subheader(L.SEC_WEALTH)
yearly, (be, reverts), exhausted = run_sim(detail)
st.plotly_chart(charts.wealth(yearly, real, be), width="stretch", key="wealth")
msg = L.NO_BREAK_EVEN if be is None else L.BREAK_EVEN_AT.format(year=be) + (L.REVERTS if reverts else "")
st.markdown(f"**{district}:** {msg}")
sim = simulate(detail, years=1)
st.caption(f"Precio pagado {charts.soles(sim.price_paid)} · cuota inicial {charts.soles(sim.down_payment)} · "
           f"préstamo {charts.soles(sim.loan)} · cuota mensual {charts.soles(sim.monthly_payment)} · "
           f"alquiler inicial {charts.soles(detail.monthly_rent)}")
if exhausted:
    st.warning("En este escenario la cartera del inquilino se vuelve negativa: el alquiler supera lo que puede "
               "financiar (renter_budget_exhausted).", icon="⚠️")

# ---------------------------------------------------------------- 4. price check
st.subheader(L.SEC_PRICES)
lst = run.listings
sale = lst[(lst.district == district) & (lst.operation == "sale")]
clean = sale[sale.in_range.astype(bool) & ~sale.outlier_flag.astype(bool) & sale.duplicate_of.isna()]
st.plotly_chart(charts.price_histogram(clean.price_pen, price, dd["price_p25"], dd["price_p75"]),
                width="stretch", key="prices")
st.caption(f"{len(clean)} avisos de venta en tu rango, sin duplicados ni atípicos "
           f"({len(sale)} encontrados en total). Son precios pedidos, no precios de cierre.")
show = lst[lst.district == district][["operation", "price_pen", "area_m2", "bedrooms", "maintenance_fee_pen",
                                      "in_range", "outlier_flag", "duplicate_of", "source_portal", "listing_date",
                                      "collected_at", "source_url"]]
st.dataframe(show, hide_index=True, width="stretch", column_config={
    "operation": st.column_config.TextColumn("Operación"),
    "price_pen": st.column_config.NumberColumn("Precio (S/)", format="%.0f"),
    "area_m2": st.column_config.NumberColumn("m²"),
    "bedrooms": st.column_config.NumberColumn("Dorm."),
    "maintenance_fee_pen": st.column_config.NumberColumn("Mantenimiento (S/)"),
    "in_range": st.column_config.CheckboxColumn("En tu rango"),
    "outlier_flag": st.column_config.CheckboxColumn("Atípico"),
    "duplicate_of": st.column_config.TextColumn("Duplicado de"),
    "source_portal": st.column_config.TextColumn("Portal"),
    "listing_date": st.column_config.TextColumn("Fecha del aviso"),
    "collected_at": st.column_config.TextColumn("Recolectado"),
    "source_url": st.column_config.LinkColumn("Fuente"),
})

# ---------------------------------------------------------------- 5. assumptions and sources
st.subheader(L.SEC_SOURCES)
rows = []
for key, label in L.PARAM_NAMES.items():
    src = dd["sources"].get(key, {})
    rows.append({"Parámetro": label, "Valor": dd["values"].get(key),
                 "Origen": L.ORIGIN.get(src.get("origin"), src.get("origin")),
                 "Fuente": src.get("source_url"), "Fecha": src.get("as_of"), "Nota": src.get("note", "")})
for o in options:
    rows.append({"Parámetro": f"{o['name']} (base)", "Valor": o["return_base"], "Origen": o["basis"],
                 "Fuente": ", ".join(o["source_urls"]), "Fecha": o["as_of"],
                 "Nota": "; ".join(o.get("caveats", []))})
rows.append({"Parámetro": "Avisos (modo de fuente)", "Valor": None, "Origen": run.market["source_mode"],
             "Fuente": "listings.csv", "Fecha": run.market["collected_at"], "Nota": ""})
st.dataframe(pd.DataFrame(rows), hide_index=True, width="stretch",
             column_config={"Valor": st.column_config.NumberColumn(format="%.4f")})
with st.expander("Bancos y riesgos de cada opción"):
    banks = run.params["mortgage"].get("by_bank") or []
    if banks:
        st.dataframe(pd.DataFrame(banks), hide_index=True, width="stretch",
                     column_config={"source_url": st.column_config.LinkColumn("Fuente")})
    for o in options:
        st.markdown(f"**{o['risk_rank']}. {o['name']}** — {o.get('explanation', '')} "
                    f"Volatilidad: {o['volatility'] if o['volatility'] is not None else 's/d'}; "
                    f"peor año: {o['worst_1y'] if o['worst_1y'] is not None else 's/d'}; "
                    f"impuestos y comisiones: {o['tax_and_fees'] or L.NEEDS_INPUT}.")
warnings = list(summary.get("warnings", [])) + dd["warnings"] + run.district(district).get("warnings", [])
for w in dict.fromkeys(warnings):
    st.warning(w, icon="⚠️")
st.info(DISCLAIMER_ES, icon="📘")

# ---------------------------------------------------------------- 6. downloads
st.subheader(L.SEC_DOWNLOAD)
c1, c2 = st.columns(2)
c1.download_button("Escenario actual por distrito y horizonte (CSV)", pd.DataFrame(all_rows).to_csv(index=False),
                   file_name=f"{run.run_id}_escenario.csv", mime="text/csv", key="dl_all")
c2.download_button(f"Trayectoria anual de {district} (CSV)", yearly.to_csv(index=False),
                   file_name=f"{run.run_id}_{district}_anual.csv", mime="text/csv", key="dl_detail")
