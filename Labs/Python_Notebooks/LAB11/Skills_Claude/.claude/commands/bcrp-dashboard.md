# /bcrp-dashboard — Peru Macro Dashboard

Fetch live BCRP data, write dashboard.py, and launch Streamlit automatically.

## Steps to execute

1. **Fetch data** — call `get_macro_snapshot(12)` via the `bcrp` MCP server.
   This returns inflation, GDP, interest rate, trade balance, and exchange rate
   for the last 12 months in a single call.

2. **Parse the response** — each series has a `"periods"` array like:
   ```json
   [{"name": "Ene.2024", "values": ["2.4"]}, ...]
   ```
   Build a list of `(period_label, float_value)` pairs for each indicator.
   Skip values that are `"n.d."` (not available).

3. **Write dashboard.py** — overwrite the file completely with a Streamlit app
   that embeds the parsed data as Python lists (no external data loading at
   runtime). Layout:

   ```
   Page title: "🇵🇪 Panel Macroeconómico — Perú"
   Subtitle: "Fuente: BCRP | Actualizado: <fetched_at from snapshot>"

   Row 1 (two columns):
     LEFT  — Inflación mensual (IPC) — bar chart, red bars when negative
             Horizontal reference lines at y=1 and y=3 (BCRP target band)
             Y-axis label: "Variación % mensual"

     RIGHT — Tipo de Cambio USD/PEN — line chart, soles per USD
             Y-axis label: "S/ por USD"

   Row 2 (two columns):
     LEFT  — PBI Desestacionalizado — line chart + linear trend line overlay
             Y-axis label: "Índice"

     RIGHT — Tasa de Interés Referencial BCRP — step chart (hv steps)
             Y-axis label: "% anual"

   Row 3 (full width):
     Balanza Comercial — bar chart, red when negative (trade deficit)
     Y-axis label: "Millones USD"
     Annotation: "Déficit comercial" when latest value < 0, else "Superávit"

   Footer metric cards (st.metric):
     Show latest value for each of the 5 indicators with delta vs prior period
   ```

4. **Launch Streamlit** — after writing dashboard.py, run:
   ```
   streamlit run dashboard.py
   ```
   Use the Bash tool so it opens the browser at http://localhost:8501.
   Run it in the background so Claude Code doesn't block.

5. **Report** — tell the user:
   "Dashboard updated and launched at http://localhost:8501"

## Error handling rules

- If a series in the snapshot has `"error"` key (API failure), skip its chart
  and render `st.warning("No disponible: <indicator name>")` in its panel.
- Always check `"periods"` key exists before iterating.
- If ALL series fail, write dashboard.py with a single `st.error()` explaining
  the API is unreachable, then still launch Streamlit.

## Economics annotations

- Inflation bar > 3%: add a note "Por encima del rango meta BCRP (1%-3%)"
- Trade balance bar < 0: color red and label "Déficit"
- Interest rate: show direction arrow in the metric card delta
- Exchange rate: annotate max/min of the period

## Chart style

- Use Plotly Express / Plotly Graph Objects via `import plotly.express as px`
- Color palette: BCRP brand colors — primary `#C8102E` (red), secondary `#003087` (navy)
- All chart titles in Spanish
- X-axis tick labels: rotate 45° for readability
- `st.set_page_config(layout="wide")`
