"""Count and map hospitals per district in Peru using the GEOPERU EESS shapefile."""

from pathlib import Path
import geopandas as gpd
import matplotlib.pyplot as plt

HERE = Path(__file__).parent
EESS_SHP = HERE / "data" / "geoperu" / "Establecimientos de Salud GEOPERU SuyoPomalia geogpsperu.shp"
DIST_SHP = HERE / ".." / ".." / ".." / "_data" / "Folium" / "DISTRITOS.shp"

eess = gpd.read_file(EESS_SHP)
districts = gpd.read_file(DIST_SHP)
print(f"EESS rows: {len(eess)} | CRS: {eess.crs}")
print(f"Districts rows: {len(districts)} | CRS: {districts.crs}")
print("\nLayer counts:")
print(eess["layer"].value_counts())

hospitals = eess[eess["layer"] == "Hospital"].copy().to_crs(districts.crs)
print(f"\nHospitals kept: {len(hospitals)}")

joined = gpd.sjoin(
    hospitals,
    districts[["IDDIST", "DISTRITO", "PROVINCIA", "DEPARTAMEN", "geometry"]],
    how="left",
    predicate="within",
)
counts = joined.groupby("IDDIST").size().rename("n_hospitals").reset_index()
districts_h = districts.merge(counts, on="IDDIST", how="left")
districts_h["n_hospitals"] = districts_h["n_hospitals"].fillna(0).astype(int)

print(f"\nDistricts with >=1 hospital: {(districts_h['n_hospitals'] > 0).sum()}")
print("\nTop 10 districts by hospital count:")
print(
    districts_h.sort_values("n_hospitals", ascending=False)
    .head(10)[["DEPARTAMEN", "PROVINCIA", "DISTRITO", "n_hospitals"]]
    .to_string(index=False)
)

# Choropleth: Peru-wide
fig, ax = plt.subplots(figsize=(10, 12))
districts_h.plot(
    column="n_hospitals", cmap="OrRd", linewidth=0.1, edgecolor="grey",
    legend=True, ax=ax,
    legend_kwds={"label": "Number of hospitals", "shrink": 0.5},
)
ax.set_title("Hospitals per District in Peru (GEOPERU EESS)")
ax.set_axis_off()
plt.tight_layout()
plt.savefig(HERE / "hospitals_per_district.png", dpi=150, bbox_inches="tight")
plt.close(fig)

# Zoom: Lima department with district name labels
lima = districts_h[districts_h["DEPARTAMEN"] == "LIMA"].copy()
fig, ax = plt.subplots(figsize=(12, 12))
lima.plot(
    column="n_hospitals", cmap="OrRd", linewidth=0.3, edgecolor="grey",
    legend=True, ax=ax,
    legend_kwds={"label": "Hospitals", "shrink": 0.6},
)

# Label each district at its representative point (guaranteed inside polygon)
lima["label_pt"] = lima.geometry.representative_point()
for _, row in lima.iterrows():
    ax.annotate(
        row["DISTRITO"],
        xy=(row["label_pt"].x, row["label_pt"].y),
        ha="center", va="center",
        fontsize=4, color="black",
    )

ax.set_title("Hospitals per District - Lima Department")
ax.set_axis_off()
plt.tight_layout()
plt.savefig(HERE / "hospitals_per_district_lima.png", dpi=200, bbox_inches="tight")
plt.close(fig)

# Zoom: Lima Metropolitan province only (denser, labels more readable)
lima_metro = districts_h[
    (districts_h["DEPARTAMEN"] == "LIMA") & (districts_h["PROVINCIA"] == "LIMA")
].copy()
fig, ax = plt.subplots(figsize=(12, 12))
lima_metro.plot(
    column="n_hospitals", cmap="OrRd", linewidth=0.4, edgecolor="grey",
    legend=True, ax=ax,
    legend_kwds={"label": "Hospitals", "shrink": 0.6},
)
lima_metro["label_pt"] = lima_metro.geometry.representative_point()
for _, row in lima_metro.iterrows():
    ax.annotate(
        f"{row['DISTRITO']}\n({row['n_hospitals']})",
        xy=(row["label_pt"].x, row["label_pt"].y),
        ha="center", va="center",
        fontsize=6, color="black",
    )
ax.set_title("Hospitals per District - Lima Metropolitan")
ax.set_axis_off()
plt.tight_layout()
plt.savefig(HERE / "hospitals_per_district_lima_metro.png", dpi=200, bbox_inches="tight")
plt.close(fig)

print("\nSaved: hospitals_per_district.png, hospitals_per_district_lima.png, hospitals_per_district_lima_metro.png")
