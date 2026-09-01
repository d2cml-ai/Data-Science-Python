"""
ENAHO 2019 - Relacion entre horas trabajadas y salario por hora.

Lee el panel enaho.dta, filtra el ano 2019, construye la muestra analitica
(ocupados con horas > 0 y salario > 0) y exporta:
  - estadisticos descriptivos (consola + CSV)
  - figuras PNG
  - datos agregados en JSON para el dashboard HTML

Uso:  python analisis_horas_salario_2019.py
"""

import json
from pathlib import Path

import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

# ----------------------------------------------------------------------------
# Configuracion
# ----------------------------------------------------------------------------
RAIZ = Path(__file__).resolve().parents[3]
DATA = RAIZ / "_data" / "enaho.dta"
OUT = Path(__file__).resolve().parent
OUT.mkdir(parents=True, exist_ok=True)

ANIO = "2019"

COLS = ["year", "horas", "salario", "l_salario", "sexo", "edad", "educ",
        "area", "dpto", "informal", "ocu500", "exper", "tenure",
        "facpob07", "ingreso", "educa", "contrato", "sector"]

# Paleta (skill dataviz - modo claro)
C = {"blue": "#2a78d6", "orange": "#eb6834", "aqua": "#1baf7a",
     "yellow": "#eda100", "magenta": "#e87ba4", "green": "#008300",
     "violet": "#4a3aa7", "red": "#e34948",
     "surface": "#fcfcfb", "ink": "#0b0b0b", "ink2": "#52514e",
     "muted": "#898781", "grid": "#e1e0d9", "axis": "#c3c2b7"}

plt.rcParams.update({
    "figure.facecolor": C["surface"], "axes.facecolor": C["surface"],
    "font.family": "sans-serif", "font.size": 10,
    "axes.edgecolor": C["axis"], "axes.labelcolor": C["ink2"],
    "xtick.color": C["muted"], "ytick.color": C["muted"],
    "axes.spines.top": False, "axes.spines.right": False,
    "grid.color": C["grid"], "grid.linewidth": 0.8,
})


def sep(titulo):
    print("\n" + "=" * 78)
    print(titulo)
    print("=" * 78)


# ----------------------------------------------------------------------------
# 1. Carga y muestra analitica
# ----------------------------------------------------------------------------
df = pd.read_stata(DATA, columns=COLS, convert_categoricals=True)
d19 = df[df["year"] == ANIO].copy()

m = d19[(d19["ocu500"] == "ocupado") & (d19["horas"] > 0) & (d19["salario"] > 0)].copy()
m["lsal"] = np.log(m["salario"])
m["w"] = m["facpob07"]

sep(f"MUESTRA - ENAHO {ANIO}")
print(f"Registros del ano {ANIO}          : {len(d19):,}")
print(f"Ocupados                          : {(d19['ocu500'] == 'ocupado').sum():,}")
print(f"Muestra analitica (horas>0, sal>0): {len(m):,}")
print(f"Poblacion representada (fac. exp.): {m['w'].sum():,.0f}")
print(f"Rango de edad                     : {m.edad.min()}-{m.edad.max()} anos")


def desc_pond(s, w):
    """Estadisticos ponderados por factor de expansion."""
    s, w = np.asarray(s, float), np.asarray(w, float)
    ok = np.isfinite(s) & np.isfinite(w)
    s, w = s[ok], w[ok]
    o = np.argsort(s)
    s, w = s[o], w[o]
    cw = np.cumsum(w) / w.sum()
    q = lambda p: float(np.interp(p, cw, s))
    mu = float(np.average(s, weights=w))
    sd = float(np.sqrt(np.average((s - mu) ** 2, weights=w)))
    return {"n": int(len(s)), "media": mu, "sd": sd, "min": float(s.min()),
            "p10": q(.10), "p25": q(.25), "mediana": q(.50), "p75": q(.75),
            "p90": q(.90), "max": float(s.max())}


sep("ESTADISTICOS DESCRIPTIVOS (ponderados por factor de expansion)")
VARS = {"horas": "Horas trabajadas / semana", "salario": "Salario por hora (S/)",
        "lsal": "Log salario por hora", "edad": "Edad (anos)",
        "educa": "Anos de educacion", "exper": "Experiencia (anos)",
        "tenure": "Antiguedad en el empleo (anos)"}
tabla = pd.DataFrame({et: desc_pond(m[v], m["w"]) for v, et in VARS.items()}).T
print(tabla.round(2).to_string())
tabla.round(4).to_csv(OUT / "tabla_descriptivos_2019.csv")

# ----------------------------------------------------------------------------
# 2. Correlaciones horas <-> salario
# ----------------------------------------------------------------------------
sep("CORRELACION HORAS <-> SALARIO")


def wcorr(x, y, w):
    x, y, w = np.asarray(x, float), np.asarray(y, float), np.asarray(w, float)
    ok = np.isfinite(x) & np.isfinite(y) & np.isfinite(w)
    x, y, w = x[ok], y[ok], w[ok]
    mx, my = np.average(x, weights=w), np.average(y, weights=w)
    cov = np.average((x - mx) * (y - my), weights=w)
    return float(cov / np.sqrt(np.average((x - mx) ** 2, weights=w) *
                               np.average((y - my) ** 2, weights=w)))


corrs = {
    "Pearson  horas vs salario":      wcorr(m.horas, m.salario, m.w),
    "Pearson  horas vs log(salario)": wcorr(m.horas, m.lsal, m.w),
    "Spearman horas vs salario":      float(m.horas.rank().corr(m.salario.rank())),
}
for k, v in corrs.items():
    print(f"  {k:32s}: {v:+.4f}")

# Regresion log(salario) = a + b*horas  (MCO ponderado, EE robustos HC1)
# Los pesos se normalizan a media 1 (suman n): los factores de expansion son
# pesos de muestreo, no frecuencias, y usarlos sin normalizar infla los EE.
def mco_pond(y, Xcols, w):
    X = np.column_stack([np.ones(len(y))] + Xcols)
    y = np.asarray(y, float)
    W = np.asarray(w, float)
    W = W / W.mean()                       # sum(W) = n
    n, k = X.shape
    XtWX_inv = np.linalg.inv(X.T @ (X * W[:, None]))
    beta = XtWX_inv @ (X.T @ (W * y))
    e = y - X @ beta
    meat = X.T @ (X * (W ** 2 * e ** 2)[:, None])          # HC1
    V = XtWX_inv @ meat @ XtWX_inv * (n / (n - k))
    ybar = np.average(y, weights=W)
    r2 = 1 - float((W * e ** 2).sum()) / float((W * (y - ybar) ** 2).sum())
    return beta, np.sqrt(np.diag(V)), r2, n


beta, se_r, r2, nreg = mco_pond(m.lsal.values, [m.horas.values], m.w.values)
print(f"\n  MCO ponderado:  log(salario) = {beta[0]:.4f} + ({beta[1]:.5f}) * horas     (n = {nreg:,})")
print(f"  EE robusto (HC1) de la pendiente: {se_r[1]:.5f}   t = {beta[1] / se_r[1]:.2f}")
print(f"  Interpretacion: +1 hora semanal se asocia a {100 * beta[1]:+.2f}% en el salario/hora")
print(f"  R2 = {r2:.4f}")

# Version con controles: sexo, edad, edad^2, anos de educacion, area, formalidad
mc = m.dropna(subset=["educa", "informal"]).copy()
ctrl = [mc.horas.values,
        (mc.sexo == "mujer").astype(float).values,
        mc.edad.astype(float).values,
        (mc.edad.astype(float) ** 2).values,
        mc.educa.astype(float).values,
        (mc.area == "Urbana").astype(float).values,
        (mc.informal == "Trabajor con seguro de pensiones").astype(float).values]
b2, se2, r2c, n2 = mco_pond(mc.lsal.values, ctrl, mc.w.values)
print(f"\n  Con controles (sexo, edad, edad2, educacion, area, pensiones), n = {n2:,}:")
print(f"  Pendiente de horas = {b2[1]:.5f}  (EE {se2[1]:.5f}, t = {b2[1] / se2[1]:.2f})"
      f"  ->  {100 * b2[1]:+.2f}% por hora adicional")
print(f"  R2 = {r2c:.4f}")

# ----------------------------------------------------------------------------
# 3. Binscatter: horas -> salario mediano
# ----------------------------------------------------------------------------
sep("SALARIO POR TRAMO DE HORAS SEMANALES")
tramos = [0, 20, 30, 40, 48, 56, 70, 200]
etiq = ["1-20", "21-30", "31-40", "41-48", "49-56", "57-70", "70+"]
m["tramo"] = pd.cut(m.horas, bins=tramos, labels=etiq)

por_tramo = []
for t in etiq:
    g = m[m.tramo == t]
    if len(g) == 0:
        continue
    st = desc_pond(g.salario, g.w)
    por_tramo.append({"tramo": t, "n": len(g), "share": 100 * g.w.sum() / m.w.sum(),
                      "mediana": st["mediana"], "media": st["media"],
                      "p25": st["p25"], "p75": st["p75"]})
pt = pd.DataFrame(por_tramo)
print(pt.round(2).to_string(index=False))

# Binscatter: 20 bins por percentil de horas. Se reporta la MEDIANA ponderada
# del salario en cada bin (la media esta dominada por la cola derecha).
def binscatter(dd, nbins=20):
    dd = dd.copy()
    dd["bin"] = pd.qcut(dd.horas, nbins, duplicates="drop")
    filas = []
    for _, g in dd.groupby("bin", observed=True):
        st = desc_pond(g.salario, g.w)
        filas.append({"horas": float(np.average(g.horas, weights=g.w)),
                      "salario": st["mediana"], "sal_media": st["media"],
                      "lsal": float(np.average(g.lsal, weights=g.w)),
                      "p25": st["p25"], "p75": st["p75"], "n": len(g)})
    return pd.DataFrame(filas)


bs = binscatter(m)
bs_sexo = {str(c): binscatter(g, 12) for c, g in m.groupby("sexo", observed=True)}
bs_form = {str(c): binscatter(g, 12)
           for c, g in m.dropna(subset=["informal"]).groupby("informal", observed=True)}

# Regresion log(salario) ~ horas dentro de cada subgrupo (para las lineas del dashboard)
reg_grupo = {}
for var in ["sexo", "informal"]:
    for cat, g in m.dropna(subset=[var]).groupby(var, observed=True):
        b, e, rr, nn = mco_pond(g.lsal.values, [g.horas.values], g.w.values)
        reg_grupo[str(cat)] = {"a": float(b[0]), "b": float(b[1]), "se": float(e[1]),
                               "t": float(b[1] / e[1]), "r2": float(rr), "n": int(nn)}
print("\n  Pendiente de horas por subgrupo (log-salario, MCO ponderado):")
for k, v in reg_grupo.items():
    print(f"    {k:35s} {100 * v['b']:+.2f}% por hora  (t = {v['t']:.1f}, n = {v['n']:,})")

# ----------------------------------------------------------------------------
# 4. Cortes por grupo
# ----------------------------------------------------------------------------
sep("HORAS Y SALARIO POR GRUPO")
grupos = {"sexo": "Sexo", "area": "Area", "informal": "Afiliacion a pensiones",
          "educ": "Nivel educativo"}
cortes = {}
for var, et in grupos.items():
    filas = []
    for cat, g in m.groupby(var, observed=True):
        if len(g) < 30:
            continue
        h, s = desc_pond(g.horas, g.w), desc_pond(g.salario, g.w)
        filas.append({"grupo": str(cat), "n": len(g),
                      "share": 100 * g.w.sum() / m.w.sum(),
                      "horas_med": h["mediana"], "horas_mean": h["media"],
                      "sal_med": s["mediana"], "sal_mean": s["media"],
                      "sal_p25": s["p25"], "sal_p75": s["p75"],
                      "corr": wcorr(g.horas, g.lsal, g.w)})
    t = pd.DataFrame(filas).sort_values("sal_med", ascending=False)
    cortes[var] = t
    print(f"\n--- {et} ---")
    print(t.round(2).to_string(index=False))

# ----------------------------------------------------------------------------
# 5. Histogramas
# ----------------------------------------------------------------------------
h_edges = np.arange(0, 101, 4)
h_cnt, _ = np.histogram(m.horas, bins=h_edges, weights=m.w)
h_cnt = 100 * h_cnt / h_cnt.sum()

s_edges = np.arange(0, 41, 1.5)
s_cnt, _ = np.histogram(m.salario.clip(upper=40), bins=s_edges, weights=m.w)
s_cnt = 100 * s_cnt / s_cnt.sum()

# ----------------------------------------------------------------------------
# 6. Figuras PNG
# ----------------------------------------------------------------------------
fig, ax = plt.subplots(1, 2, figsize=(11, 3.8))
ax[0].bar(h_edges[:-1], h_cnt, width=3.6, align="edge", color=C["blue"])
ax[0].axvline(48, color=C["orange"], lw=2, ls="--")
ax[0].text(49, max(h_cnt) * .92, "48 h\n(jornada legal)", color=C["orange"], fontsize=8)
ax[0].set_title("Horas trabajadas por semana", loc="left", color=C["ink"], fontweight="bold")
ax[0].set_xlabel("Horas semanales"); ax[0].set_ylabel("% de ocupados")
ax[1].bar(s_edges[:-1], s_cnt, width=1.35, align="edge", color=C["aqua"])
ax[1].set_title("Salario por hora (S/), recortado en 40", loc="left",
                color=C["ink"], fontweight="bold")
ax[1].set_xlabel("Soles por hora"); ax[1].set_ylabel("% de ocupados")
for a in ax:
    a.grid(axis="y", lw=.8); a.set_axisbelow(True)
fig.tight_layout(); fig.savefig(OUT / "fig1_distribuciones.png", dpi=160)

fig, ax = plt.subplots(figsize=(6.5, 4.2))
ax.scatter(bs.horas, bs.salario, s=60, color=C["blue"], zorder=3,
           edgecolor=C["surface"], linewidth=2)
xx = np.linspace(bs.horas.min(), bs.horas.max(), 50)
ax.plot(xx, np.exp(beta[0] + beta[1] * xx), color=C["orange"], lw=2, zorder=2,
        label=f"MCO en logs: {100 * beta[1]:+.2f}% por hora")
ax.legend(frameon=False)
ax.set_title("Salario por hora vs. horas trabajadas (20 bins de percentil)", loc="left",
             color=C["ink"], fontweight="bold")
ax.set_xlabel("Horas semanales (media del bin)")
ax.set_ylabel("Salario por hora mediano (S/)")
ax.grid(axis="y", lw=.8); ax.set_axisbelow(True)
fig.tight_layout(); fig.savefig(OUT / "fig2_binscatter.png", dpi=160)

fig, ax = plt.subplots(figsize=(7, 4.2))
sx = cortes["sexo"]
y = np.arange(len(sx))
ax.barh(y - .2, sx.sal_med, .36, color=C["blue"], label="Salario/hora mediano (S/)")
ax.barh(y + .2, sx.horas_med, .36, color=C["orange"], label="Horas medianas")
ax.set_yticks(y); ax.set_yticklabels(sx.grupo)
ax.legend(frameon=False); ax.grid(axis="x", lw=.8); ax.set_axisbelow(True)
ax.set_title("Horas y salario por sexo", loc="left", color=C["ink"], fontweight="bold")
fig.tight_layout(); fig.savefig(OUT / "fig3_sexo.png", dpi=160)

# ----------------------------------------------------------------------------
# 7. JSON para el dashboard
# ----------------------------------------------------------------------------
payload = {
    "anio": ANIO,
    "n_total": int(len(d19)),
    "n_ocupados": int((d19["ocu500"] == "ocupado").sum()),
    "n": int(len(m)),
    "poblacion": float(m.w.sum()),
    "edad_min": int(m.edad.min()), "edad_max": int(m.edad.max()),
    "descriptivos": {et: desc_pond(m[v], m.w) for v, et in VARS.items()},
    "corr": corrs,
    "reg": {"a": float(beta[0]), "b": float(beta[1]), "se": float(se_r[1]),
            "t": float(beta[1] / se_r[1]), "r2": float(r2), "n": int(nreg)},
    "reg_ctrl": {"b": float(b2[1]), "se": float(se2[1]), "t": float(b2[1] / se2[1]),
                 "r2": float(r2c), "n": int(n2)},
    "hist_horas": {"edges": h_edges.tolist(), "pct": h_cnt.tolist()},
    "hist_salario": {"edges": s_edges.tolist(), "pct": s_cnt.tolist()},
    "binscatter": bs.to_dict("records"),
    "bs_sexo": {k: v.to_dict("records") for k, v in bs_sexo.items()},
    "bs_form": {k: v.to_dict("records") for k, v in bs_form.items()},
    "reg_grupo": reg_grupo,
    "tramos": pt.to_dict("records"),
    "cortes": {k: v.to_dict("records") for k, v in cortes.items()},
}
with open(OUT / "datos_dashboard.json", "w", encoding="utf-8") as f:
    json.dump(payload, f, ensure_ascii=False, indent=1)

sep("SALIDAS")
for p in sorted(OUT.glob("*")):
    print(" ", p.name)
