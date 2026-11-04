"""Plotly charts. Colors follow the reference palette: buyer = slot 1 (blue), renter = slot 2 (orange);
the heat map is diverging blue (buying wins) <-> red (renting wins) with a gray midpoint at zero."""

from __future__ import annotations

from typing import Optional

import pandas as pd
import plotly.graph_objects as go

import labels as L

BUY_COLOR = "#2a78d6"
RENT_COLOR = "#eb6834"
MUTED = "#898781"
INK = "#0b0b0b"
DIVERGING = [[0.0, "#b8302f"], [0.25, "#e98584"], [0.5, "#f0efec"], [0.75, "#86b6ef"], [1.0, "#1c5cab"]]

_LAYOUT = dict(margin=dict(l=10, r=10, t=30, b=10), hovermode="closest",
               font=dict(family='system-ui, -apple-system, "Segoe UI", sans-serif'),
               legend=dict(orientation="h", yanchor="bottom", y=1.02, x=0))


def soles(x: float) -> str:
    return f"S/ {x:,.0f}"


def heatmap(df: pd.DataFrame, horizon: int, current_rate: float, current_return: float) -> go.Figure:
    """df: rows of mortgage_rate, opportunity_return, delta."""
    pivot = df.pivot(index="opportunity_return", columns="mortgage_rate", values="delta").sort_index()
    x = [f"{r:.2%}" for r in pivot.columns]
    y = [f"{r:.2%}" for r in pivot.index]
    zmax = float(max(abs(pivot.values.min()), abs(pivot.values.max()), 1.0))
    fig = go.Figure(go.Heatmap(
        z=pivot.values, x=x, y=y, colorscale=DIVERGING, zmid=0, zmin=-zmax, zmax=zmax, xgap=2, ygap=2,
        colorbar=dict(title="S/", thickness=12),
        hovertemplate="Mortgage rate %{x}<br>Return %{y}<br>Buy − rent: S/ %{z:,.0f}<extra></extra>",
    ))
    fig.update_layout(**_LAYOUT, height=420,
                      xaxis_title="Mortgage rate (annual effective)", yaxis_title="Opportunity-cost return",
                      title=dict(text=f"After {horizon} years · blue: buying wins · red: renting wins", font=dict(size=13)))
    cx = min(range(len(pivot.columns)), key=lambda i: abs(pivot.columns[i] - current_rate))
    cy = min(range(len(pivot.index)), key=lambda i: abs(pivot.index[i] - current_return))
    fig.add_trace(go.Scatter(x=[x[cx]], y=[y[cy]], mode="markers", name="Current scenario",
                             marker=dict(size=14, symbol="circle-open", color="#0b0b0b", line=dict(width=2)),
                             hoverinfo="skip"))
    return fig


def wealth(yearly: pd.DataFrame, real: bool, break_even: Optional[int]) -> go.Figure:
    b, r = ("w_buy_real", "w_rent_real") if real else ("w_buy", "w_rent")
    fig = go.Figure()
    for col, name, color in ((b, L.BUYER, BUY_COLOR), (r, L.RENTER, RENT_COLOR)):
        fig.add_trace(go.Scatter(x=yearly["year"], y=yearly[col], name=name, mode="lines",
                                 line=dict(color=color, width=2),
                                 hovertemplate=f"{name}<br>Year %{{x}}: S/ %{{y:,.0f}}<extra></extra>"))
        last = yearly.iloc[-1]
        fig.add_annotation(x=last["year"], y=last[col], text=name, showarrow=False, xanchor="left", xshift=6,
                           font=dict(size=12))
    if break_even is not None:
        fig.add_vline(x=break_even, line=dict(color=MUTED, width=1, dash="dot"))
        fig.add_annotation(x=break_even, y=1, yref="paper", text=f"{L.BREAK_EVEN}: year {break_even}",
                           showarrow=False, yanchor="bottom", font=dict(size=12))
    fig.update_layout(**{**_LAYOUT, "hovermode": "x unified"}, height=400, xaxis_title="Year",
                      yaxis_title="Net wealth (S/" + (", real" if real else "") + ")")
    fig.update_xaxes(range=[0, yearly["year"].max() + 3])
    return fig


def price_histogram(prices: pd.Series, chosen: float, p25: Optional[float], p75: Optional[float]) -> go.Figure:
    fig = go.Figure(go.Histogram(x=prices, nbinsx=12, marker=dict(color=BUY_COLOR, line=dict(color="#fcfcfb", width=2)),
                                 name="Sale listings",
                                 hovertemplate="Price %{x}<br>%{y} listings<extra></extra>"))
    if p25 is not None and p75 is not None:
        fig.add_vrect(x0=p25, x1=p75, fillcolor=BUY_COLOR, opacity=0.08, line_width=0,
                      annotation_text="P25–P75", annotation_position="top left")
    fig.add_vline(x=chosen, line=dict(color="#0b0b0b", width=2))
    fig.add_annotation(x=chosen, y=1, yref="paper", text=f"Chosen price {soles(chosen)}", showarrow=False,
                       yanchor="bottom", xanchor="left", xshift=4, font=dict(size=12))
    fig.update_layout(**_LAYOUT, height=320, showlegend=False, xaxis_title="Asking price (S/)", yaxis_title="Listings",
                      bargap=0.05)
    return fig


# ---------------------------------------------------------------- explanation charts
SPENT = "#c3c2b7"   # money that is gone (interest, taxes, rent)
SHARED = "#e1e0d9"  # building fee: paid by both, cancels out
KEPT = {"buyer": BUY_COLOR, "renter": RENT_COLOR}


def _segment_color(side: str, name: str) -> str:
    if name.startswith("Building fee"):
        return SHARED
    if name.startswith("Mortgage principal") or name.startswith("Invested"):
        return KEPT[side]
    return SPENT


def monthly_split(split: dict) -> go.Figure:
    """Two stacked bars of equal length: where the same monthly amount goes for each household.
    Colored segments build wealth; gray segments are money that is gone."""
    fig = go.Figure()
    rows = [("renter", L.RENTER), ("buyer", L.BUYER)]
    for side, label in rows:
        for name, value in split[side].items():
            if abs(value) < 0.5:
                continue
            fig.add_trace(go.Bar(
                y=[label], x=[value], orientation="h", name=name, showlegend=False,
                marker=dict(color=_segment_color(side, name), line=dict(color="#fcfcfb", width=2)),
                text=f"{name}<br>{soles(value)}", textposition="inside", insidetextanchor="middle",
                textfont=dict(color="#0b0b0b", size=11),
                hovertemplate=f"{label} · {name}: {soles(value)} per month<extra></extra>"))
    fig.update_layout(**{**_LAYOUT, "hovermode": "closest"}, barmode="relative", height=230,
                      xaxis_title=f"S/ per month in year 1 (both spend {soles(split['total'])})",
                      uniformtext=dict(minsize=9, mode="hide"))
    return fig


def wealth_waterfall(bd: dict) -> go.Figure:
    """Buyer's and renter's wealth after H years, built up from their parts."""
    from plotly.subplots import make_subplots
    fig = make_subplots(rows=1, cols=2, shared_yaxes=True, horizontal_spacing=0.06,
                        subplot_titles=(f"{L.BUYER}: {soles(bd['w_buy'])}", f"{L.RENTER}: {soles(bd['w_rent'])}"))
    for col, side, total in ((1, "buyer", bd["w_buy"]), (2, "renter", bd["w_rent"])):
        parts = bd[side]
        color = KEPT[side]
        fig.add_trace(go.Waterfall(
            x=[p[0] for p in parts] + ["Wealth"], y=[p[1] for p in parts] + [total],
            measure=["relative"] * len(parts) + ["total"],
            text=[soles(p[1]) for p in parts] + [soles(total)], textposition="outside",
            increasing=dict(marker=dict(color=color)), decreasing=dict(marker=dict(color=SPENT)),
            totals=dict(marker=dict(color=color, line=dict(color=INK, width=1.5))),
            connector=dict(line=dict(color=MUTED, width=1, dash="dot")), showlegend=False,
            hovertemplate="%{x}: S/ %{y:,.0f}<extra></extra>"), row=1, col=col)
    fig.update_layout(**_LAYOUT, height=400)
    fig.update_layout(margin=dict(l=10, r=10, t=50, b=10))
    fig.update_yaxes(title_text="S/", row=1, col=1)
    return fig


def vote_grid(cells: list[dict], current_rate: float) -> go.Figure:
    """Every scenario of the verdict grid: mortgage rate x investment option, buy minus rent."""
    df = pd.DataFrame(cells)
    order = list(dict.fromkeys(df["option"]))
    pivot = df.pivot(index="option", columns="mortgage_rate", values="delta").reindex(order[::-1])
    x = [f"{r:.2%}" for r in pivot.columns]
    text = [[("Buy " if v > 0 else "Rent ") + f"{v / 1000:+,.0f}k" for v in row] for row in pivot.values]
    zmax = float(max(abs(pivot.values.min()), abs(pivot.values.max()), 1.0))
    fig = go.Figure(go.Heatmap(
        z=pivot.values, x=x, y=list(pivot.index), colorscale=DIVERGING, zmid=0, zmin=-zmax, zmax=zmax,
        xgap=3, ygap=3, text=text, texttemplate="%{text}", textfont=dict(size=12, color=INK), showscale=False,
        hovertemplate="Mortgage rate %{x}<br>%{y}<br>Buy − rent: S/ %{z:,.0f}<extra></extra>"))
    cx = min(range(len(pivot.columns)), key=lambda i: abs(pivot.columns[i] - current_rate))
    fig.add_vrect(x0=cx - 0.5, x1=cx + 0.5, line=dict(color=INK, width=1.5), fillcolor="rgba(0,0,0,0)")
    fig.update_layout(**_LAYOUT, height=90 + 55 * len(pivot.index), xaxis_title="Mortgage rate (annual effective)",
                      yaxis_title=None)
    return fig
