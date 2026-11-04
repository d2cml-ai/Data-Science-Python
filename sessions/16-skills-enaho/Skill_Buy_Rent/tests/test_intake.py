from datetime import datetime

import pytest

from housing_lima.districts import UnknownDistrict, normalize_district
from housing_lima.intake import IntakeError, build_inputs, create_run, parse_extras
from housing_lima.validate import validate_run

NOW = datetime(2026, 11, 4, 15, 30)


def answers(**kw):
    a = dict(price_min=250000, price_max=400000, currency="PEN", min_area_m2=60, min_bedrooms=2,
             districts=["Jesús María", "pueblo libre", "SMP"], down_payment_pct=20,
             extras_text="Quiero 1 estacionamiento, máximo 10 años de antigüedad y acepten mascotas")
    a.update(kw)
    return a


def test_build_inputs_normalizes_and_validates():
    inp = build_inputs(answers(), NOW)
    assert inp["run_id"] == "20261104-1530-jesus-maria-pueblo-libre"
    assert inp["districts"] == ["Jesús María", "Pueblo Libre", "San Martín de Porres"]
    assert inp["extras"]["parking_min"] == 1
    assert inp["extras"]["max_age_years"] == 10
    assert inp["extras"]["pets_allowed"] is True
    assert "mascotas" in inp["extras"]["notes"]


def test_usd_answers_converted_and_rate_recorded():
    inp = build_inputs(answers(currency="USD", price_min=70000, price_max=100000, fx_usd_pen=3.75,
                               fx_as_of="2026-11-04"), NOW)
    assert inp["price_min_pen"] == 262500
    assert inp["fx_conversion"]["usd_pen"] == 3.75


def test_usd_without_rate_asks_for_it():
    with pytest.raises(IntakeError) as e:
        build_inputs(answers(currency="USD"), NOW)
    assert e.value.code == "fx_needed"


@pytest.mark.parametrize("dp", [3, 60])
def test_down_payment_out_of_range_is_reasked(dp):
    with pytest.raises(IntakeError) as e:
        build_inputs(answers(down_payment_pct=dp), NOW)
    assert e.value.code == "down_payment_out_of_range"


def test_decimal_down_payment_accepted():
    assert build_inputs(answers(down_payment_pct=0.3), NOW)["down_payment_pct"] == 30


def test_price_range_must_be_ordered():
    with pytest.raises(IntakeError) as e:
        build_inputs(answers(price_min=500000), NOW)
    assert e.value.code == "price_range"


def test_unknown_district_gives_suggestions():
    with pytest.raises(IntakeError) as e:
        build_inputs(answers(districts=["Miraflorez", "Xyzzy"]), NOW)
    assert e.value.code == "district"


@pytest.mark.parametrize("alias,official", [("SMP", "San Martín de Porres"), ("San Martin", "San Martín de Porres"),
                                            ("surco", "Santiago de Surco"), ("Miraflorez", "Miraflores"),
                                            ("JESUS MARIA", "Jesús María"), ("Magdalena", "Magdalena del Mar")])
def test_district_aliases(alias, official):
    assert normalize_district(alias) == official


def test_unknown_district_raises():
    with pytest.raises(UnknownDistrict):
        normalize_district("Narnia")


def test_parse_extras_payment_and_new():
    ex = parse_extras("departamento a estrenar, cuota máxima S/ 2,500, piso 3", None)
    assert ex["is_new"] is True
    assert ex["max_monthly_payment"] == 2500
    assert ex["min_floor"] == 3


def test_create_run_writes_valid_inputs(tmp_path):
    run_dir = create_run(answers(), tmp_path, NOW)
    assert (run_dir / "inputs.json").exists()
    assert validate_run(run_dir, "inputs") == []
