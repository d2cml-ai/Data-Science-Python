"""Listings pipeline used by the market-data agent: normalize, de-duplicate, flag outliers, summarize.

Listings are never invented, interpolated or silently deleted. Records without a
source URL are dropped (and counted); duplicates and outliers stay in the file with flags.
"""

from __future__ import annotations

import hashlib
from datetime import date
from typing import Optional

import numpy as np
import pandas as pd

from .districts import UnknownDistrict, normalize_district
from .validate import LISTING_COLUMNS


def _stable_id(row: pd.Series) -> str:
    raw = f"{row['operation']}|{row['source_url']}"
    return row["operation"][0].upper() + "-" + hashlib.sha1(raw.encode()).hexdigest()[:10]


def normalize(raw: pd.DataFrame, fx_usd_pen: Optional[float], collected_at: Optional[str] = None) -> tuple[pd.DataFrame, dict]:
    """Bring raw rows to the listing schema. Returns (df, report).

    Raw rows need at least: operation, district, price_original, currency_original,
    area_m2, bedrooms, source_portal, source_url. Rent prices are monthly.
    """
    df = raw.copy()
    for col in LISTING_COLUMNS:
        if col not in df.columns:
            df[col] = np.nan
    report = {"rows_in": len(df), "dropped_without_url": 0, "dropped_unknown_district": [],
              "dropped_no_price": 0, "usd_converted": 0}

    url = df["source_url"].astype("string").str.strip()
    no_url = url.isna() | (url == "") | ~url.fillna("").str.startswith(("http://", "https://"))
    report["dropped_without_url"] = int(no_url.sum())
    df = df.loc[~no_url].copy()

    df["operation"] = df["operation"].astype(str).str.strip().str.lower().replace(
        {"venta": "sale", "alquiler": "rent", "compra": "sale"})
    df = df[df["operation"].isin(["sale", "rent"])].copy()

    canon = []
    for name in df["district"].astype(str):
        try:
            canon.append(normalize_district(name))
        except UnknownDistrict:
            canon.append(None)
            report["dropped_unknown_district"].append(name)
    df["district"] = canon
    df = df[df["district"].notna()].copy()

    df["currency_original"] = df["currency_original"].astype(str).str.upper().str.strip().replace(
        {"S/": "PEN", "S/.": "PEN", "SOLES": "PEN", "US$": "USD", "$": "USD", "DOLARES": "USD"})
    df["price_original"] = pd.to_numeric(df["price_original"], errors="coerce")
    is_usd = df["currency_original"] == "USD"
    if is_usd.any() and not fx_usd_pen:
        raise ValueError("USD listings found but no USD/PEN rate was given for the collection date")
    df["fx_used"] = np.where(is_usd, fx_usd_pen or np.nan, 1.0)
    df["price_pen"] = df["price_original"] * df["fx_used"]
    report["usd_converted"] = int(is_usd.sum())
    no_price = df["price_pen"].isna() | (df["price_pen"] <= 0)
    report["dropped_no_price"] = int(no_price.sum())
    df = df[~no_price].copy()

    for col in ("area_m2", "bathrooms", "parking", "age_years", "maintenance_fee_pen"):
        df[col] = pd.to_numeric(df[col], errors="coerce")
    df["bedrooms"] = pd.to_numeric(df["bedrooms"], errors="coerce")
    df["collected_at"] = df["collected_at"].fillna(collected_at or date.today().isoformat())
    df["id"] = [i if isinstance(i, str) and i.strip() else _stable_id(r) for i, (_, r) in zip(df["id"], df.iterrows())]
    df["outlier_flag"] = False
    df["duplicate_of"] = pd.Series([None] * len(df), index=df.index, dtype="object")
    df["in_range"] = False
    df["notes"] = df["notes"].fillna("")
    report["rows_out"] = len(df)
    return df[LISTING_COLUMNS].reset_index(drop=True), report


def dedupe(df: pd.DataFrame, price_tol: float = 0.02, area_tol: float = 0.03) -> pd.DataFrame:
    """Mark listings that appear on several portals. The first occurrence stays the original."""
    df = df.copy()
    df["duplicate_of"] = df["duplicate_of"].astype("object")
    for _, grp in df.groupby(["operation", "district", "bedrooms"], dropna=False):
        idx = list(grp.index)
        for a_pos, a in enumerate(idx):
            if isinstance(df.at[a, "duplicate_of"], str):
                continue
            for b in idx[a_pos + 1:]:
                if isinstance(df.at[b, "duplicate_of"], str):
                    continue
                if df.at[a, "source_url"] == df.at[b, "source_url"]:
                    df.at[b, "duplicate_of"] = df.at[a, "id"]
                    continue
                # A cross-portal duplicate: the same home published on another portal.
                if df.at[a, "source_portal"] == df.at[b, "source_portal"]:
                    continue
                pa, pb = df.at[a, "price_pen"], df.at[b, "price_pen"]
                aa, ab = df.at[a, "area_m2"], df.at[b, "area_m2"]
                if pd.isna(aa) or pd.isna(ab):
                    continue
                if abs(pa - pb) / max(pa, pb) <= price_tol and abs(aa - ab) / max(aa, ab) <= area_tol:
                    df.at[b, "duplicate_of"] = df.at[a, "id"]
    return df


def flag_outliers(df: pd.DataFrame, k: float = 1.5) -> pd.DataFrame:
    """IQR rule per district and operation on price, among non-duplicates. Rows are kept, only flagged."""
    df = df.copy()
    df["outlier_flag"] = False
    base = df["duplicate_of"].isna()
    for _, grp in df[base].groupby(["district", "operation"]):
        if len(grp) < 4:
            continue
        q1, q3 = grp["price_pen"].quantile([0.25, 0.75])
        iqr = q3 - q1
        lo, hi = q1 - k * iqr, q3 + k * iqr
        mask = (grp["price_pen"] < lo) | (grp["price_pen"] > hi)
        df.loc[grp.index[mask], "outlier_flag"] = True
    return df


def mark_in_range(df: pd.DataFrame, inputs: dict, rent_area_tolerance: float = 0.15) -> pd.DataFrame:
    """Sale: inside the user's price range and filters. Rent: comparable homes to the sale sample."""
    df = df.copy()
    extras = inputs.get("extras", {})
    sale = df["operation"] == "sale"
    ok = (
        sale
        & df["price_pen"].between(inputs["price_min_pen"], inputs["price_max_pen"])
        & (df["area_m2"] >= inputs["min_area_m2"])
        & (df["bedrooms"] >= inputs["min_bedrooms"])
    )
    if extras.get("parking_min"):
        ok &= df["parking"].fillna(0) >= extras["parking_min"]
    if extras.get("max_age_years") is not None:
        ok &= df["age_years"].isna() | (df["age_years"] <= extras["max_age_years"])
    if extras.get("is_new") is True:
        ok &= (df["is_new"].astype(str).str.lower().isin(["true", "1"])) | (df["age_years"] == 0)
    df.loc[sale, "in_range"] = ok[sale]

    clean = df["duplicate_of"].isna() & ~df["outlier_flag"]
    for district in df["district"].unique():
        s = df[(df["district"] == district) & df["in_range"] & clean]
        r_idx = df.index[(df["district"] == district) & (df["operation"] == "rent")]
        if s.empty:
            df.loc[r_idx, "in_range"] = False
            continue
        med_area = s["area_m2"].median()
        r = df.loc[r_idx]
        df.loc[r_idx, "in_range"] = (
            (r["bedrooms"] >= inputs["min_bedrooms"])
            & (r["area_m2"].between(med_area * (1 - rent_area_tolerance), med_area * (1 + rent_area_tolerance)))
        )
    return df


def _q(series: pd.Series, q: float) -> Optional[float]:
    return None if series.empty else round(float(series.quantile(q)), 2)


def district_summary(df: pd.DataFrame, inputs: dict, defaults: dict, source_mode: str,
                     index_ppm2: Optional[dict] = None) -> list[dict]:
    """Per-district statistics and realistic price / rent (median of in-range, clean listings)."""
    min_n = defaults["min_listings_per_side"]
    tol = defaults["index_check_tolerance"]
    out = []
    clean = df["duplicate_of"].isna() & ~df["outlier_flag"].astype(bool) & df["in_range"].astype(bool)
    for district in inputs["districts"]:
        in_d = df["district"] == district
        d_all = df[in_d]
        sale = df[in_d & (df["operation"] == "sale") & clean]
        rent = df[in_d & (df["operation"] == "rent") & clean]
        ppm2 = sale["price_pen"] / sale["area_m2"]
        warnings = []
        if len(sale) < min_n:
            warnings.append(f"only {len(sale)} sale listings (minimum {min_n}): low confidence")
        if len(rent) < min_n:
            warnings.append(f"only {len(rent)} rent listings (minimum {min_n}): low confidence")
        d_mode = source_mode

        index_check = None
        ref = (index_ppm2 or {}).get(district)
        if ref and ref.get("value") and not ppm2.empty:
            diff = float(ppm2.median()) / ref["value"] - 1
            index_check = {"index_ppm2": ref["value"], "sample_ppm2": round(float(ppm2.median()), 2),
                           "difference": round(diff, 4), "flag": abs(diff) > tol,
                           "source_url": ref.get("source_url"), "as_of": ref.get("as_of")}
            if abs(diff) > tol:
                warnings.append(f"median price/m2 differs {diff:+.0%} from the published index")

        out.append({
            "district": district,
            "source_mode": d_mode,
            "low_confidence": len(sale) < min_n or len(rent) < min_n,
            "sale": {
                "n": int(len(sale)),
                "n_found": int((d_all["operation"] == "sale").sum()),
                "price_p25": _q(sale["price_pen"], 0.25),
                "price_median": _q(sale["price_pen"], 0.5),
                "price_p75": _q(sale["price_pen"], 0.75),
                "price_per_m2_median": _q(ppm2, 0.5),
                "area_median": _q(sale["area_m2"], 0.5),
                "realistic_price": _q(sale["price_pen"], 0.5),
                "maintenance_fee_median": _q(sale["maintenance_fee_pen"].dropna(), 0.5),
            },
            "rent": {
                "n": int(len(rent)),
                "n_found": int((d_all["operation"] == "rent").sum()),
                "rent_p25": _q(rent["price_pen"], 0.25),
                "rent_median": _q(rent["price_pen"], 0.5),
                "rent_p75": _q(rent["price_pen"], 0.75),
                "rent_per_m2_median": _q(rent["price_pen"] / rent["area_m2"], 0.5),
                "realistic_rent": _q(rent["price_pen"], 0.5),
                "maintenance_fee_median": _q(rent["maintenance_fee_pen"].dropna(), 0.5),
            },
            "index_check": index_check,
            "warnings": warnings,
        })
    return out


def build_market(raw: pd.DataFrame, inputs: dict, defaults: dict, source_mode: str,
                 fx: Optional[dict] = None, collected_at: Optional[str] = None,
                 index_ppm2: Optional[dict] = None) -> tuple[pd.DataFrame, dict, dict]:
    """Full pipeline. Returns (listings, market_summary, report)."""
    fx_rate = fx.get("usd_pen") if fx else None
    df, report = normalize(raw, fx_rate, collected_at)
    df = df[df["district"].isin(inputs["districts"])].reset_index(drop=True)
    df = dedupe(df, defaults["dedupe_price_tolerance"], defaults["dedupe_area_tolerance"])
    df = flag_outliers(df)
    df = mark_in_range(df, inputs, defaults["rent_area_tolerance"])
    summary = {
        "run_id": inputs["run_id"],
        "synthetic": bool(inputs.get("synthetic", False)),
        "source_mode": source_mode,
        "collected_at": collected_at or date.today().isoformat(),
        "fx_used": fx,
        "negotiation_discount": defaults["negotiation_discount"],
        "dropped_without_url": report["dropped_without_url"],
        "districts": district_summary(df, inputs, defaults, source_mode, index_ppm2),
    }
    report["duplicates_flagged"] = int(df["duplicate_of"].notna().sum())
    report["outliers_flagged"] = int(df["outlier_flag"].sum())
    return df, summary, report
