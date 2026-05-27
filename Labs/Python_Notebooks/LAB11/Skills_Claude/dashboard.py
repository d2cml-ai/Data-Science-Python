"""
Panel Macroeconómico — Perú (2021-2026)
Datos en vivo del BCRP. Generado por /bcrp-dashboard.
"""
import json
import numpy as np
import plotly.graph_objects as go
import plotly.express as px
import streamlit as st
from datetime import datetime

st.set_page_config(
    page_title="Panel Macroeconómico — Perú",
    page_icon="🇵🇪",
    layout="wide",
)

BCRP_RED  = "#C8102E"
BCRP_NAVY = "#003087"
LIGHT_RED = "#FFCCCC"

# ── Load data ─────────────────────────────────────────────────────────────────
@st.cache_data
def load_data():
    with open("bcrp_data.json", encoding="utf-8") as f:
        return json.load(f)

def parse(series, scale=1.0):
    """Return (labels, values) skipping n.d. entries."""
    labels, values = [], []
    for p in series.get("periods", []):
        v = p["values"][0]
        if v != "n.d." and v is not None:
            labels.append(p["name"])
            values.append(float(v) * scale)
    return labels, values

data = load_data()

inf_labels,  inf_vals  = parse(data["inflation"])
gdp_labels,  gdp_vals  = parse(data["gdp"])
ir_labels,   ir_vals   = parse(data["interest_rate"])
exc_labels,  exc_vals  = parse(data["exchange_rate"])
tb_labels,   tb_vals   = parse(data["trade_balance"])

updated = datetime.now().strftime("%d %b %Y %H:%M")

# ── Header ────────────────────────────────────────────────────────────────────
st.title("🇵🇪 Panel Macroeconómico — Perú")
st.caption(f"Fuente: BCRP (Banco Central de Reserva del Perú) · Serie: 2021–2026 · Actualizado: {updated}")
st.divider()

# ── Metric cards ──────────────────────────────────────────────────────────────
c1, c2, c3, c4, c5 = st.columns(5)

def delta(vals):
    if len(vals) >= 2:
        return round(vals[-1] - vals[-2], 3)
    return None

c1.metric("Inflación mensual",  f"{inf_vals[-1]:.2f}%",  delta=delta(inf_vals),  delta_color="inverse")
c2.metric("PBI (índice)",       f"{gdp_vals[-1]:.1f}",   delta=delta(gdp_vals))
c3.metric("Tasa referencial",   f"{ir_vals[-1]:.2f}%",   delta=delta(ir_vals),   delta_color="inverse")
c4.metric("Tipo de cambio",     f"S/ {exc_vals[-1]:.3f}", delta=delta(exc_vals), delta_color="inverse")
c5.metric("Balanza comercial",  f"{tb_vals[-1]:.2f}",    delta=delta(tb_vals))

st.divider()

# ── Row 1: Inflation | Exchange rate ──────────────────────────────────────────
col1, col2 = st.columns(2)

with col1:
    st.subheader("Inflación Mensual (IPC)")
    colors = [BCRP_RED if v < 0 else BCRP_NAVY for v in inf_vals]
    fig = go.Figure()
    fig.add_trace(go.Bar(x=inf_labels, y=inf_vals, marker_color=colors, name="IPC MoM %"))
    fig.add_hline(y=1, line_dash="dot", line_color="gray", annotation_text="Mín. meta 1%",
                  annotation_position="bottom right")
    fig.add_hline(y=3, line_dash="dot", line_color=BCRP_RED, annotation_text="Máx. meta 3%",
                  annotation_position="top right")
    fig.update_layout(
        yaxis_title="Variación % mensual",
        xaxis_tickangle=-45,
        showlegend=False,
        plot_bgcolor="white",
        height=380,
    )
    st.plotly_chart(fig, use_container_width=True)
    above = sum(1 for v in inf_vals if v > 3)
    if above:
        st.warning(f"{above} meses por encima del rango meta BCRP (1%–3%)")

with col2:
    st.subheader("Tipo de Cambio USD/PEN")
    fig2 = go.Figure()
    fig2.add_trace(go.Scatter(
        x=exc_labels, y=exc_vals,
        mode="lines+markers",
        line=dict(color=BCRP_NAVY, width=2),
        marker=dict(size=4),
        name="S/ por USD",
    ))
    fig2.add_annotation(
        x=exc_labels[exc_vals.index(max(exc_vals))],
        y=max(exc_vals),
        text=f"Máx: S/ {max(exc_vals):.3f}",
        showarrow=True, arrowhead=2, arrowcolor=BCRP_RED,
        font=dict(color=BCRP_RED),
    )
    fig2.add_annotation(
        x=exc_labels[exc_vals.index(min(exc_vals))],
        y=min(exc_vals),
        text=f"Mín: S/ {min(exc_vals):.3f}",
        showarrow=True, arrowhead=2, ax=20, ay=30,
    )
    fig2.update_layout(
        yaxis_title="S/ por USD",
        xaxis_tickangle=-45,
        showlegend=False,
        plot_bgcolor="white",
        height=380,
    )
    st.plotly_chart(fig2, use_container_width=True)

# ── Row 2: GDP | Interest rate ────────────────────────────────────────────────
col3, col4 = st.columns(2)

with col3:
    st.subheader("PBI Desestacionalizado")
    # Add linear trend
    x_num = list(range(len(gdp_vals)))
    z = np.polyfit(x_num, gdp_vals, 1)
    trend = [z[0]*i + z[1] for i in x_num]

    fig3 = go.Figure()
    fig3.add_trace(go.Scatter(
        x=gdp_labels, y=gdp_vals,
        mode="lines+markers",
        line=dict(color=BCRP_NAVY, width=2),
        marker=dict(size=4),
        name="PBI índice",
    ))
    fig3.add_trace(go.Scatter(
        x=gdp_labels, y=trend,
        mode="lines",
        line=dict(color=BCRP_RED, width=1, dash="dash"),
        name="Tendencia lineal",
    ))
    fig3.update_layout(
        yaxis_title="Índice (base 2007)",
        xaxis_tickangle=-45,
        plot_bgcolor="white",
        height=380,
        legend=dict(orientation="h", yanchor="bottom", y=1.02),
    )
    st.plotly_chart(fig3, use_container_width=True)

with col4:
    st.subheader("Tasa de Interés Referencial BCRP")
    fig4 = go.Figure()
    fig4.add_trace(go.Scatter(
        x=ir_labels, y=ir_vals,
        mode="lines",
        line=dict(shape="hv", color=BCRP_RED, width=2.5),
        fill="tozeroy",
        fillcolor="rgba(200,16,46,0.08)",
        name="Tasa %",
    ))
    peak_idx = ir_vals.index(max(ir_vals))
    fig4.add_annotation(
        x=ir_labels[peak_idx], y=max(ir_vals),
        text=f"Pico: {max(ir_vals):.2f}%",
        showarrow=True, arrowhead=2, arrowcolor=BCRP_NAVY,
        font=dict(color=BCRP_NAVY),
    )
    fig4.update_layout(
        yaxis_title="% anual",
        xaxis_tickangle=-45,
        showlegend=False,
        plot_bgcolor="white",
        height=380,
    )
    st.plotly_chart(fig4, use_container_width=True)
    direction = "subiendo" if ir_vals[-1] > ir_vals[-2] else "bajando" if ir_vals[-1] < ir_vals[-2] else "sin cambio"
    st.caption(f"Política monetaria: tasa {direction} (último dato {ir_labels[-1]})")

# ── Row 3: Trade balance (full width) ─────────────────────────────────────────
st.subheader("Balanza Comercial (Exportaciones acumuladas, millones USD)")
tb_colors = [BCRP_RED if v < 0 else BCRP_NAVY for v in tb_vals]
fig5 = go.Figure()
fig5.add_trace(go.Bar(x=tb_labels, y=tb_vals, marker_color=tb_colors, name="Millones USD"))
fig5.update_layout(
    yaxis_title="Millones USD",
    xaxis_tickangle=-45,
    showlegend=False,
    plot_bgcolor="white",
    height=320,
)
st.plotly_chart(fig5, use_container_width=True)

deficits = sum(1 for v in tb_vals if v < 0)
if deficits:
    st.error(f"Déficit comercial detectado en {deficits} meses del período analizado.")
else:
    st.success("Superávit comercial sostenido durante el período 2021–2026.")

# ── Footer ────────────────────────────────────────────────────────────────────
st.divider()
st.caption(
    "Series BCRP: Inflación PN01271PM · PBI PN01773AM · Tasa PN07819NM · "
    "Tipo de cambio PN01234PM · Balanza PN01781AM"
)
