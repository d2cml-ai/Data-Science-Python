"""Verdict cards: one row per district, one metric per horizon."""

from __future__ import annotations

import streamlit as st

import labels as L


def verdict_row(district: str, deltas: dict[int, float], low_confidence: bool, grid_labels: dict[int, str],
                real: bool) -> None:
    title = f"**{district}**" + (f" · _{L.LOW_CONFIDENCE}_" if low_confidence else "")
    st.markdown(title)
    cols = st.columns(len(deltas))
    for col, (h, d) in zip(cols, deltas.items()):
        winner = L.BUY_WINS if d > 0 else L.RENT_WINS
        icon = "▲" if d > 0 else "▼"
        col.metric(
            label=f"{h} {L.YEARS}",
            value=f"{icon} {winner}",
            delta=f"S/ {d:,.0f}" + (" reales" if real else ""),
            delta_color="normal",
            help=("Diferencia de patrimonio comprador − inquilino con los controles actuales. "
                  + (f"En la grilla original: {L.GRID_VERDICT[grid_labels[h]]}." if h in grid_labels else "")),
        )
