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
        hovertemplate="Tasa hipotecaria %{x}<br>Rentabilidad %{y}<br>Comprar − alquilar: S/ %{z:,.0f}<extra></extra>",
    ))
    fig.update_layout(**_LAYOUT, height=420,
                      xaxis_title="Tasa hipotecaria (TEA)", yaxis_title="Rentabilidad del costo de oportunidad",
                      title=dict(text=f"A {horizon} años · azul: comprar gana · rojo: alquilar gana", font=dict(size=13)))
    cx = min(range(len(pivot.columns)), key=lambda i: abs(pivot.columns[i] - current_rate))
    cy = min(range(len(pivot.index)), key=lambda i: abs(pivot.index[i] - current_return))
    fig.add_trace(go.Scatter(x=[x[cx]], y=[y[cy]], mode="markers", name="Escenario actual",
                             marker=dict(size=14, symbol="circle-open", color="#0b0b0b", line=dict(width=2)),
                             hoverinfo="skip"))
    return fig


def wealth(yearly: pd.DataFrame, real: bool, break_even: Optional[int]) -> go.Figure:
    b, r = ("w_buy_real", "w_rent_real") if real else ("w_buy", "w_rent")
    fig = go.Figure()
    for col, name, color in ((b, L.BUYER, BUY_COLOR), (r, L.RENTER, RENT_COLOR)):
        fig.add_trace(go.Scatter(x=yearly["year"], y=yearly[col], name=name, mode="lines",
                                 line=dict(color=color, width=2),
                                 hovertemplate=f"{name}<br>Año %{{x}}: S/ %{{y:,.0f}}<extra></extra>"))
        last = yearly.iloc[-1]
        fig.add_annotation(x=last["year"], y=last[col], text=name, showarrow=False, xanchor="left", xshift=6,
                           font=dict(size=12))
    if break_even is not None:
        fig.add_vline(x=break_even, line=dict(color=MUTED, width=1, dash="dot"))
        fig.add_annotation(x=break_even, y=1, yref="paper", text=f"{L.BREAK_EVEN}: año {break_even}",
                           showarrow=False, yanchor="bottom", font=dict(size=12))
    fig.update_layout(**{**_LAYOUT, "hovermode": "x unified"}, height=400, xaxis_title="Año",
                      yaxis_title="Patrimonio neto (S/" + (", reales" if real else "") + ")")
    fig.update_xaxes(range=[0, yearly["year"].max() + 3])
    return fig


def price_histogram(prices: pd.Series, chosen: float, p25: Optional[float], p75: Optional[float]) -> go.Figure:
    fig = go.Figure(go.Histogram(x=prices, nbinsx=12, marker=dict(color=BUY_COLOR, line=dict(color="#fcfcfb", width=2)),
                                 name="Avisos de venta",
                                 hovertemplate="Precio %{x}<br>%{y} avisos<extra></extra>"))
    if p25 is not None and p75 is not None:
        fig.add_vrect(x0=p25, x1=p75, fillcolor=BUY_COLOR, opacity=0.08, line_width=0,
                      annotation_text="P25–P75", annotation_position="top left")
    fig.add_vline(x=chosen, line=dict(color="#0b0b0b", width=2))
    fig.add_annotation(x=chosen, y=1, yref="paper", text=f"Precio elegido {soles(chosen)}", showarrow=False,
                       yanchor="bottom", xanchor="left", xshift=4, font=dict(size=12))
    fig.update_layout(**_LAYOUT, height=320, showlegend=False, xaxis_title="Precio pedido (S/)", yaxis_title="Avisos",
                      bargap=0.05)
    return fig
