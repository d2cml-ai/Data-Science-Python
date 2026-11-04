"""Orchestrator intake: validate and normalize the user's answers into inputs.json."""

from __future__ import annotations

import re
import unicodedata
from datetime import datetime
from pathlib import Path
from typing import Optional

from .districts import UnknownDistrict, normalize_district
from .loaders import write_json
from .paths import runs_root
from .validate import validate_json


class IntakeError(ValueError):
    """Raised with a code so the orchestrator knows which question to ask again."""

    def __init__(self, code: str, message: str, suggestions: Optional[list[str]] = None):
        super().__init__(message)
        self.code = code
        self.suggestions = suggestions or []


def _ascii(text: str) -> str:
    return unicodedata.normalize("NFKD", text).encode("ascii", "ignore").decode().lower()


def _number(text: str) -> float:
    text = text.replace(" ", "").strip(".,")
    if re.fullmatch(r"\d{1,3}([.,]\d{3})+", text):  # thousands separators: 2.500 or 2,500
        return float(re.sub(r"[.,]", "", text))
    return float(text.replace(",", "."))


def parse_extras(text: str, fx_usd_pen: Optional[float] = None) -> dict:
    """Turn free-text wishes into structured filters; the full text stays in notes as a soft preference."""
    extras = {"parking_min": None, "max_age_years": None, "max_monthly_payment": None,
              "is_new": None, "pets_allowed": None, "min_floor": None, "notes": (text or "").strip()}
    t = _ascii(text or "")
    if not t:
        return extras

    m = re.search(r"(\d+)\s*(estacionamientos?|cocheras?|parkings?|parqueos?|garajes?)", t)
    if m:
        extras["parking_min"] = int(m.group(1))
    elif re.search(r"estacionamiento|cochera|parking|parqueo|garaje|garage", t) and not re.search(r"sin (estacionamiento|cochera)", t):
        extras["parking_min"] = 1

    m = re.search(r"(?:antiguedad|maximo|max\.?|menos de|hasta|no mas de)\D{0,25}?(\d{1,3})\s*anos", t)
    if m:
        extras["max_age_years"] = float(m.group(1))

    if re.search(r"\b(estreno|a estrenar|nuevo|nueva|en planos|new)\b", t):
        extras["is_new"] = True
    elif re.search(r"\b(usado|usada|segunda mano|de segunda)\b", t):
        extras["is_new"] = False

    if re.search(r"mascota|pet|perro|gato", t):
        extras["pets_allowed"] = True

    m = re.search(r"(?:cuota|pago mensual|mensualidad|monthly payment)\D{0,25}?(s/\.?|us\$|\$|usd)?\s*(\d[\d.,]*)", t)
    if m:
        amount = _number(m.group(2))
        if m.group(1) in ("us$", "$", "usd"):
            if not fx_usd_pen:
                raise IntakeError("fx_needed", "The maximum monthly payment is in dollars; a dated USD/PEN rate is needed.")
            amount *= fx_usd_pen
        extras["max_monthly_payment"] = round(amount, 2)

    m = re.search(r"piso\s*(\d{1,2})|(\d{1,2})\s*(?:er|ro|do|to|vo|no|mo|o)?\s*piso", t)
    if m:
        extras["min_floor"] = int(m.group(1) or m.group(2))
    return extras


def slugify(text: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", _ascii(text)).strip("-")[:40] or "lima"


def build_inputs(answers: dict, now: Optional[datetime] = None) -> dict:
    """answers: price_min, price_max, currency (PEN|USD), fx_usd_pen, fx_as_of, fx_source_url,
    min_area_m2, min_bedrooms, districts, down_payment_pct, extras_text, slug (optional)."""
    now = now or datetime.now()
    currency = str(answers.get("currency", "PEN")).upper()
    pmin, pmax = float(answers["price_min"]), float(answers["price_max"])
    if pmin <= 0 or pmax <= 0:
        raise IntakeError("price_range", "Both prices must be positive.")
    if pmin >= pmax:
        raise IntakeError("price_range", "The minimum price must be below the maximum price.")

    fx = None
    if currency == "USD":
        rate = answers.get("fx_usd_pen")
        if not rate or not answers.get("fx_as_of"):
            raise IntakeError("fx_needed", "Prices are in dollars: a USD/PEN rate with its date is needed to convert to soles.")
        fx = {"usd_pen": float(rate), "as_of": answers["fx_as_of"], "source_url": answers.get("fx_source_url")}
        pmin, pmax = pmin * fx["usd_pen"], pmax * fx["usd_pen"]
    elif currency != "PEN":
        raise IntakeError("currency", "Currency must be PEN or USD.")

    area, beds = float(answers["min_area_m2"]), int(answers["min_bedrooms"])
    if area <= 0:
        raise IntakeError("size", "The minimum area must be positive.")
    if beds < 0:
        raise IntakeError("size", "The number of bedrooms cannot be negative.")

    raw_districts = answers["districts"]
    if isinstance(raw_districts, str):
        raw_districts = [d for d in re.split(r"[,;/]| y ", raw_districts) if d.strip()]
    districts = []
    for name in raw_districts:
        try:
            canon = normalize_district(name.strip())
        except UnknownDistrict as exc:
            raise IntakeError("district", str(exc), exc.suggestions) from exc
        if canon not in districts:
            districts.append(canon)
    if not 1 <= len(districts) <= 6:
        raise IntakeError("district", "Choose between one and six districts.")

    dp = float(answers["down_payment_pct"])
    if 0 < dp < 1:  # answered as a decimal, e.g. 0.2
        dp *= 100
    if not 5 <= dp <= 50:
        raise IntakeError("down_payment_out_of_range",
                          f"A down payment of {dp:g}% is outside the 5%-50% range the model supports.")

    extras = parse_extras(answers.get("extras_text", ""), fx["usd_pen"] if fx else answers.get("fx_usd_pen"))
    slug = slugify(answers.get("slug") or "-".join(districts[:2]))
    inputs = {
        "run_id": f"{now:%Y%m%d-%H%M}-{slug}",
        "created_at": now.isoformat(timespec="seconds"),
        "price_min_pen": round(pmin, 2), "price_max_pen": round(pmax, 2),
        "min_area_m2": area, "min_bedrooms": beds,
        "districts": districts, "down_payment_pct": round(dp, 2),
        "currency_answered": currency, "fx_conversion": fx,
        "extras": extras,
    }
    if answers.get("synthetic"):
        inputs["synthetic"] = True
    validate_json(inputs, "inputs.schema.json")
    return inputs


def create_run(answers: dict, root: Optional[Path] = None, now: Optional[datetime] = None) -> Path:
    inputs = build_inputs(answers, now)
    run_dir = Path(root or runs_root()) / inputs["run_id"]
    run_dir.mkdir(parents=True, exist_ok=False)
    write_json(run_dir / "inputs.json", inputs)
    return run_dir
