import pandas as pd
import pytest

from housing_lima.listings import build_market, dedupe, flag_outliers, normalize
from housing_lima.loaders import load_defaults


def raw(rows):
    base = dict(operation="sale", district="Pueblo Libre", price_original=300000, currency_original="PEN",
                area_m2=70, bedrooms=2, source_portal="a", source_url="https://x.test/1")
    return pd.DataFrame([{**base, **r} for r in rows])


def test_rows_without_url_are_dropped():
    df, report = normalize(raw([{}, {"source_url": ""}, {"source_url": None}, {"source_url": "not-a-url"}]), None)
    assert len(df) == 1
    assert report["dropped_without_url"] == 3
    assert df["source_url"].str.startswith("http").all()


def test_usd_converted_to_soles_with_rate_recorded():
    df, report = normalize(raw([{"currency_original": "USD", "price_original": 100000}]), 3.75)
    assert df.loc[0, "price_pen"] == pytest.approx(375000)
    assert df.loc[0, "fx_used"] == 3.75
    assert report["usd_converted"] == 1


def test_usd_without_rate_is_an_error():
    with pytest.raises(ValueError):
        normalize(raw([{"currency_original": "US$"}]), None)


def test_district_aliases_and_spanish_operations():
    df, _ = normalize(raw([{"district": "SMP", "operation": "Venta"}, {"district": "surco", "operation": "alquiler",
                                                                       "source_url": "https://x.test/2"}]), None)
    assert list(df["district"]) == ["San Martín de Porres", "Santiago de Surco"]
    assert list(df["operation"]) == ["sale", "rent"]


def test_cross_portal_duplicate_flagged_but_kept():
    df, _ = normalize(raw([{}, {"source_portal": "b", "source_url": "https://y.test/9", "price_original": 301000}]), None)
    out = dedupe(df)
    assert len(out) == 2
    assert out["duplicate_of"].notna().sum() == 1
    assert out.loc[1, "duplicate_of"] == out.loc[0, "id"]


def test_same_portal_similar_homes_are_not_duplicates():
    df, _ = normalize(raw([{}, {"source_url": "https://x.test/2", "price_original": 301000}]), None)
    assert dedupe(df)["duplicate_of"].isna().all()


def test_iqr_outlier_flagged_not_deleted():
    rows = [{"source_url": f"https://x.test/{i}", "price_original": p}
            for i, p in enumerate([300000, 305000, 310000, 298000, 302000, 307000, 900000])]
    df, _ = normalize(raw(rows), None)
    out = flag_outliers(dedupe(df))
    assert len(out) == 7
    assert out["outlier_flag"].tolist() == [False] * 6 + [True]


def test_fixture_market_summary_uses_median_of_clean_in_range(sample_run):
    from housing_lima.loaders import read_json
    inputs = read_json(sample_run / "inputs.json")
    fx = read_json(sample_run / "fx.json")
    df, summary, report = build_market(pd.read_csv(sample_run / "raw_listings.csv"), inputs, load_defaults(), "csv", fx)
    assert report["dropped_without_url"] == 3
    assert report["duplicates_flagged"] == 3
    assert report["outliers_flagged"] == 3
    for d in summary["districts"]:
        sel = df[(df.district == d["district"]) & (df.operation == "sale") & df.in_range & ~df.outlier_flag & df.duplicate_of.isna()]
        assert d["sale"]["realistic_price"] == pytest.approx(sel.price_pen.median())
        assert inputs["price_min_pen"] <= d["sale"]["realistic_price"] <= inputs["price_max_pen"]
        assert d["sale"]["price_p25"] <= d["sale"]["price_median"] <= d["sale"]["price_p75"]
        assert d["sale"]["n"] >= 8 and d["rent"]["n"] >= 8


def test_low_sample_district_is_flagged_not_filled():
    rows = [{"source_url": f"https://x.test/{i}", "price_original": 300000 + i * 1000} for i in range(3)]
    rows += [{"operation": "rent", "source_url": f"https://x.test/r{i}", "price_original": 1800} for i in range(3)]
    inputs = {"run_id": "20261103-0000-t", "price_min_pen": 250000, "price_max_pen": 400000, "min_area_m2": 60,
              "min_bedrooms": 2, "districts": ["Pueblo Libre"], "down_payment_pct": 20, "extras": {"notes": ""}}
    _, summary, _ = build_market(raw(rows), inputs, load_defaults(), "live")
    d = summary["districts"][0]
    assert d["low_confidence"] is True
    assert d["sale"]["n"] == 3
    assert any("low confidence" in w for w in d["warnings"])
