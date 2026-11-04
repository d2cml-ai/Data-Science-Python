"""Buy vs rent dashboard for Lima.

Launch: python .claude/skills/buy-vs-rent/scripts/hl.py dashboard --run outputs/<run-id>
Reads one run folder and makes no network calls. All formulas come from housing_lima.model;
the step-by-step explanation comes from housing_lima.explain.
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
from housing_lima import DISCLAIMER, explain  # noqa: E402
from housing_lima.analysis import build_scenario  # noqa: E402
from housing_lima.model import Scenario, simulate  # noqa: E402
from housing_lima.returns import usd_to_pen  # noqa: E402

st.set_page_config(page_title="Buy vs rent in Lima", page_icon="🏠", layout="wide")


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


@st.cache_data(show_spinner=False)
def explain_breakdown(s: Scenario, horizon: int) -> dict:
    return explain.wealth_breakdown(s, horizon)


@st.cache_data(show_spinner=False)
def explain_split(s: Scenario) -> dict:
    return explain.first_year_monthly(s)


@st.cache_data(show_spinner=False)
def explain_vote(s: Scenario, horizon: int, rates: tuple, opts: tuple, thresholds: tuple) -> dict:
    options = [{"id": i, "name": n, "return": r} for i, n, r in opts]
    return explain.scenario_vote(s, horizon, list(rates), options, dict(thresholds))


@st.cache_data(show_spinner=False)
def explain_flips(s: Scenario, horizon: int) -> list:
    return explain.flip_points(s, horizon)


def pct(x: float) -> float:
    return round(100 * x, 2)


def fmt_value(v: float, is_rate: bool) -> str:
    return f"{v:.2%}" if is_rate else charts.soles(v)


# ---------------------------------------------------------------- run selection
runs = state.available_runs()
run_labels = [p.name for p in runs]
defaults = state.cached_defaults()

st.sidebar.header("Controls")
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
    st.error("No district has enough listings to analyse.")
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
                                  help=f"Defaults to the market average ({pct(market_rate):.2f}%).") / 100

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
                          help=f"Defaults to the median of the listings found. P25–P75: "
                               f"S/ {dd['price_p25']:,.0f} – S/ {dd['price_p75']:,.0f}.")
st.sidebar.caption(f"Listings P25–P75: S/ {dd['price_p25']:,.0f} – S/ {dd['price_p75']:,.0f}")

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
        st.sidebar.caption(f"⚠️ {L.PARAM_NAMES[name]}: no source found, an assumption is used. Adjust it.")
    return v / 100


price_growth = growth_slider("price_growth", L.PRICE_GROWTH)
rent_growth = growth_slider("rent_growth", L.RENT_GROWTH)
real = st.sidebar.toggle(L.REAL, value=False, key="real")

common = dict(mortgage_rate=mortgage_rate, down_payment_pct=down_payment, opportunity_return=opp_return,
              negotiation_discount=discount, loan_term_years=loan_term)
detail = build_scenario(run, district, defaults, **common, price=price, price_growth=price_growth,
                        rent_growth=rent_growth)
dcol = "delta_real" if real else "delta"
horizons = summary.get("horizons") or defaults["horizons"]

# ---------------------------------------------------------------- 1. verdict cards
st.subheader(L.SEC_VERDICTS)
st.markdown(L.VERDICT_INTRO)
st.caption("With the current controls. The chosen price and growth rates apply to the detail district; "
           "the other districts use their own realistic price and parameters.")
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
        all_rows.append({"district": name, "horizon": h, "price": s.price, "rent": s.monthly_rent,
                         "buyer_wealth": r["w_buy_real" if real else "w_buy"],
                         "renter_wealth": r["w_rent_real" if real else "w_rent"],
                         "buy_minus_rent": r[dcol], "break_even_year": be})

# ---------------------------------------------------------------- 2. how the recommendation was made
st.subheader(L.SEC_HOW.format(district=district))
horizon = st.select_slider(L.HORIZON, horizons, value=20 if 20 in horizons else horizons[-1], key="horizon")
md = run.district(district)
bd = explain_breakdown(detail, horizon)
split = explain_split(detail)
st.markdown(L.HOW_INTRO.format(h=horizon))

# Step 1: two comparable homes
st.markdown(f"#### {L.STEP1}")
paid = detail.price * (1 - detail.negotiation_discount)
rent_yield = 12 * detail.monthly_rent / paid
c1, c2, c3 = st.columns(3)
c1.markdown(f"**{L.BUYER}** buys at **{charts.soles(paid)}**  \n"
            f"median of {md['sale']['n']} sale listings in your range "
            f"(P25–P75: {charts.soles(md['sale']['price_p25'])} – {charts.soles(md['sale']['price_p75'])})"
            + (f", minus a {detail.negotiation_discount:.1%} discount" if detail.negotiation_discount else ""))
c2.markdown(f"**{L.RENTER}** rents a similar home for **{charts.soles(detail.monthly_rent)} / month**  \n"
            f"median of {md['rent']['n']} rent listings of similar size")
c3.markdown(f"**One year of rent = {rent_yield:.1%} of the price**  \n"
            f"it takes {1 / rent_yield:.0f} years of rent to pay the price of the home")

# Step 2: same money every month
st.markdown(f"#### {L.STEP2}")
st.markdown(L.STEP2_TEXT.format(upfront=charts.soles(bd["upfront"]), down=charts.soles(bd["down_payment"]),
                                costs=charts.soles(bd["buy_costs"]), total=charts.soles(split["total"]),
                                payment=charts.soles(split["payment"]),
                                invested=charts.soles(split["renter"]["Invested each month (difference)"])))
st.plotly_chart(charts.monthly_split(split), width="stretch", key="monthly_split")
st.caption(L.STEP2_CAPTION)

# Step 3: what each one owns
st.markdown(f"#### {L.STEP3.format(h=horizon)}")
st.plotly_chart(charts.wealth_waterfall(bd), width="stretch", key="waterfall")
st.markdown((L.STEP3_BUY if bd["delta"] > 0 else L.STEP3_RENT).format(
    h=horizon, gap=charts.soles(abs(bd["delta"])), interest=charts.soles(bd["interest_paid"]),
    rent=charts.soles(bd["rent_paid"])))

# Step 4: why
st.markdown(f"#### {L.STEP4}")
drv = explain.drivers(detail)
st.dataframe(pd.DataFrame([{
    "Comparison": d["name"],
    "A": f"{d['left'][0]}: {d['left'][1]:.2%}",
    "B": f"{d['right'][0]}: {d['right'][1]:.2%}",
    "Points to": "Buying" if d["favours"] == "buy" else "Renting",
    "Why it matters": d["why"]} for d in drv]), hide_index=True, width="stretch")
n_rent = sum(d["favours"] == "rent" for d in drv)
st.markdown(L.STEP4_SUMMARY.format(n=n_rent, total=len(drv), side="renting") if n_rent * 2 > len(drv)
            else L.STEP4_SUMMARY.format(n=len(drv) - n_rent, total=len(drv), side="buying"))

# Step 5: the scenario vote
st.markdown(f"#### {L.STEP5}")
thresholds = (summary.get("parameters") or {}).get("verdict_thresholds") or defaults["verdict_thresholds"]
vote_opts = tuple((o["id"], o["name"], float(o["return_base"])) for o in options)
vote = explain_vote(detail, horizon, tuple(grid), vote_opts, tuple(thresholds.items()))
st.plotly_chart(charts.vote_grid(vote["cells"], market_rate), width="stretch", key="vote")
st.markdown(L.STEP5_TEXT.format(n=vote["n"], rates=len(grid), opts=len(options),
                                wins=sum(c["buy_wins"] for c in vote["cells"]), share=vote["share"],
                                buy=thresholds["buy"], rent=thresholds["rent"], h=horizon,
                                label=L.GRID_VERDICT[vote["label"]]))
orig = {v["horizon"]: v for d in summary.get("districts", []) if d["district"] == district for v in d["verdicts"]}
if horizon in orig:
    st.caption(L.STEP5_ORIGINAL.format(label=L.GRID_VERDICT[orig[horizon]["label"]],
                                       share=orig[horizon]["share_buy_wins"]))

# Step 6: what would change the answer
st.markdown(f"#### {L.STEP6}")
flips = explain_flips(detail, horizon)
st.dataframe(pd.DataFrame([{
    "Input": f.label,
    "Now": fmt_value(f.current, f.is_rate),
    "Buy and rent tie at": "—" if f.flip is None else fmt_value(f.flip, f.is_rate),
    "Buying wins when it is": "not in a realistic range" if f.flip is None else f"{f.buy_wins_when} that value",
} for f in flips]), hide_index=True, width="stretch")
st.caption(L.STEP6_CAPTION.format(h=horizon))

# ---------------------------------------------------------------- 3. wealth over time
st.subheader(L.SEC_WEALTH)
yearly, (be, reverts), exhausted = run_sim(detail)
st.plotly_chart(charts.wealth(yearly, real, be), width="stretch", key="wealth")
msg = L.NO_BREAK_EVEN if be is None else L.BREAK_EVEN_AT.format(year=be) + (L.REVERTS if reverts else "")
st.markdown(f"**{district}:** {msg}")
sim = simulate(detail, years=1)
st.caption(f"Price paid {charts.soles(sim.price_paid)} · down payment {charts.soles(sim.down_payment)} · "
           f"loan {charts.soles(sim.loan)} · monthly payment {charts.soles(sim.monthly_payment)} · "
           f"starting rent {charts.soles(detail.monthly_rent)}")
if exhausted:
    st.warning("In this scenario the renter's portfolio goes negative: rent exceeds what it can fund "
               "(renter_budget_exhausted).", icon="⚠️")

# ---------------------------------------------------------------- 4. heat map
st.subheader(L.SEC_HEATMAP)
rates = tuple(sorted({round(max(mortgage_rate + o, 0.001), 6) for o in np.arange(-0.02, 0.0201, 0.005)}))
returns = tuple(sorted({round(x, 6) for x in np.linspace(0.0, 0.14, 8)} | {round(opp_return, 6)}))
hm = heat_grid(detail, horizon, rates, returns)
if real:
    hm = hm.assign(delta=hm["delta"] / (1 + detail.inflation) ** horizon)
st.plotly_chart(charts.heatmap(hm, horizon, mortgage_rate, opp_return), width="stretch", key="heatmap")
st.caption(f"{district}. Each cell: buyer's wealth minus renter's wealth (S/) after {horizon} years. "
           "The circle marks the current scenario; pale cells are close to a tie.")

# ---------------------------------------------------------------- 5. price check
st.subheader(L.SEC_PRICES)
lst = run.listings
sale = lst[(lst.district == district) & (lst.operation == "sale")]
clean = sale[sale.in_range.astype(bool) & ~sale.outlier_flag.astype(bool) & sale.duplicate_of.isna()]
st.plotly_chart(charts.price_histogram(clean.price_pen, price, dd["price_p25"], dd["price_p75"]),
                width="stretch", key="prices")
st.caption(f"{len(clean)} sale listings in your range, without duplicates or outliers "
           f"({len(sale)} found in total). These are asking prices, not closing prices.")
show = lst[lst.district == district][["operation", "price_pen", "area_m2", "bedrooms", "maintenance_fee_pen",
                                      "in_range", "outlier_flag", "duplicate_of", "source_portal", "listing_date",
                                      "collected_at", "source_url"]]
st.dataframe(show, hide_index=True, width="stretch", column_config={
    "operation": st.column_config.TextColumn("Operation"),
    "price_pen": st.column_config.NumberColumn("Price (S/)", format="%.0f"),
    "area_m2": st.column_config.NumberColumn("m²"),
    "bedrooms": st.column_config.NumberColumn("Bedrooms"),
    "maintenance_fee_pen": st.column_config.NumberColumn("Building fee (S/)"),
    "in_range": st.column_config.CheckboxColumn("In your range"),
    "outlier_flag": st.column_config.CheckboxColumn("Outlier"),
    "duplicate_of": st.column_config.TextColumn("Duplicate of"),
    "source_portal": st.column_config.TextColumn("Portal"),
    "listing_date": st.column_config.TextColumn("Listing date"),
    "collected_at": st.column_config.TextColumn("Collected"),
    "source_url": st.column_config.LinkColumn("Source"),
})

# ---------------------------------------------------------------- 6. assumptions and sources
st.subheader(L.SEC_SOURCES)
rows = []
for key, label in L.PARAM_NAMES.items():
    src = dd["sources"].get(key, {})
    rows.append({"Parameter": label, "Value": dd["values"].get(key),
                 "Origin": L.ORIGIN.get(src.get("origin"), src.get("origin")),
                 "Source": src.get("source_url"), "Date": src.get("as_of"), "Note": src.get("note", "")})
for o in options:
    rows.append({"Parameter": f"{o['name']} (base)", "Value": o["return_base"], "Origin": o["basis"],
                 "Source": ", ".join(o["source_urls"]), "Date": o["as_of"],
                 "Note": "; ".join(o.get("caveats", []))})
rows.append({"Parameter": "Listings (source mode)", "Value": None, "Origin": run.market["source_mode"],
             "Source": "listings.csv", "Date": run.market["collected_at"], "Note": ""})
st.dataframe(pd.DataFrame(rows), hide_index=True, width="stretch",
             column_config={"Value": st.column_config.NumberColumn(format="%.4f")})
with st.expander("Banks and the risk of each option"):
    banks = run.params["mortgage"].get("by_bank") or []
    if banks:
        st.dataframe(pd.DataFrame(banks), hide_index=True, width="stretch",
                     column_config={"source_url": st.column_config.LinkColumn("Source")})
    for o in options:
        st.markdown(f"**{o['risk_rank']}. {o['name']}** — {o.get('explanation', '')} "
                    f"Volatility: {o['volatility'] if o['volatility'] is not None else 'n/a'}; "
                    f"worst year: {o['worst_1y'] if o['worst_1y'] is not None else 'n/a'}; "
                    f"taxes and fees: {o['tax_and_fees'] or L.NEEDS_INPUT}.")
with st.expander(L.METHOD_TITLE):
    st.markdown(L.METHOD_TEXT)
warnings = list(summary.get("warnings", [])) + dd["warnings"] + run.district(district).get("warnings", [])
for w in dict.fromkeys(warnings):
    st.warning(w, icon="⚠️")
st.info(DISCLAIMER, icon="📘")

# ---------------------------------------------------------------- 7. downloads
st.subheader(L.SEC_DOWNLOAD)
c1, c2 = st.columns(2)
c1.download_button("Current scenario by district and horizon (CSV)", pd.DataFrame(all_rows).to_csv(index=False),
                   file_name=f"{run.run_id}_scenario.csv", mime="text/csv", key="dl_all")
c2.download_button(f"Yearly path for {district} (CSV)", yearly.to_csv(index=False),
                   file_name=f"{run.run_id}_{district}_yearly.csv", mime="text/csv", key="dl_detail")
