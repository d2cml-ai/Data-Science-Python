"""Official district names of Lima Metropolitana and Callao, with common aliases."""

from __future__ import annotations

import difflib
import re
import unicodedata

LIMA_DISTRICTS = [
    "Ancón", "Ate", "Barranco", "Breña", "Carabayllo", "Chaclacayo", "Chorrillos",
    "Cieneguilla", "Comas", "El Agustino", "Independencia", "Jesús María", "La Molina",
    "La Victoria", "Lima", "Lince", "Los Olivos", "Lurigancho", "Lurín",
    "Magdalena del Mar", "Miraflores", "Pachacámac", "Pucusana", "Pueblo Libre",
    "Puente Piedra", "Punta Hermosa", "Punta Negra", "Rímac", "San Bartolo", "San Borja",
    "San Isidro", "San Juan de Lurigancho", "San Juan de Miraflores", "San Luis",
    "San Martín de Porres", "San Miguel", "Santa Anita", "Santa María del Mar",
    "Santa Rosa", "Santiago de Surco", "Surquillo", "Villa El Salvador",
    "Villa María del Triunfo",
]
CALLAO_DISTRICTS = [
    "Callao", "Bellavista", "Carmen de la Legua Reynoso", "La Perla", "La Punta",
    "Ventanilla", "Mi Perú",
]
OFFICIAL = LIMA_DISTRICTS + CALLAO_DISTRICTS

# The districts offered first in the intake question (frequent searches).
COMMON_CHOICES = [
    "Miraflores", "San Isidro", "Santiago de Surco", "San Borja", "Barranco", "Jesús María",
    "Pueblo Libre", "San Miguel", "Lince", "Magdalena del Mar", "La Molina", "Surquillo",
]


def _key(text: str) -> str:
    text = unicodedata.normalize("NFKD", text).encode("ascii", "ignore").decode()
    text = re.sub(r"[^a-z0-9 ]", " ", text.lower())
    return re.sub(r"\s+", " ", text).strip()


ALIASES = {
    "smp": "San Martín de Porres",
    "san martin": "San Martín de Porres",
    "san martin de porras": "San Martín de Porres",
    "sjl": "San Juan de Lurigancho",
    "sjm": "San Juan de Miraflores",
    "ves": "Villa El Salvador",
    "vmt": "Villa María del Triunfo",
    "surco": "Santiago de Surco",
    "magdalena": "Magdalena del Mar",
    "cercado": "Lima",
    "cercado de lima": "Lima",
    "lima cercado": "Lima",
    "chosica": "Lurigancho",
    "jesus maria": "Jesús María",
    "rimac": "Rímac",
    "pachacamac": "Pachacámac",
    "carmen de la legua": "Carmen de la Legua Reynoso",
}

_BY_KEY = {_key(d): d for d in OFFICIAL}
_BY_KEY.update({_key(a): d for a, d in ALIASES.items()})


class UnknownDistrict(ValueError):
    def __init__(self, name: str, suggestions: list[str]):
        super().__init__(f"Unknown district '{name}'. Did you mean: {', '.join(suggestions) or 'no match'}?")
        self.name = name
        self.suggestions = suggestions


def normalize_district(name: str) -> str:
    """Return the official name, e.g. 'SMP' -> 'San Martín de Porres'. Raises UnknownDistrict."""
    key = _key(name)
    if key in _BY_KEY:
        return _BY_KEY[key]
    close = difflib.get_close_matches(key, list(_BY_KEY), n=3, cutoff=0.8)
    if len(close) >= 1 and difflib.SequenceMatcher(None, key, close[0]).ratio() >= 0.9:
        return _BY_KEY[close[0]]
    suggestions = sorted({_BY_KEY[c] for c in difflib.get_close_matches(key, list(_BY_KEY), n=3, cutoff=0.6)})
    raise UnknownDistrict(name, suggestions)
