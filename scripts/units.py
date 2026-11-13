"""Unit conversions shared with the front end. All factors live in content/units.json.

    from units import to_std, from_std
    to_std(760, "pressure", "mmHg")   -> 101.32 (kPa)
    from_std(101.325, "pressure", "psi") -> 14.70
"""

from __future__ import annotations

import json
from functools import lru_cache
from pathlib import Path

UNITS_FILE = Path(__file__).resolve().parent.parent / "content" / "units.json"


@lru_cache(maxsize=1)
def _table() -> dict:
    return json.loads(UNITS_FILE.read_text(encoding="utf-8"))["quantities"]


def _unit(quantity: str, unit: str) -> dict:
    units = _table()[quantity]["units"]
    if unit in units:
        return units[unit]
    for spec in units.values():
        if unit in spec.get("aliases", []):
            return spec
    raise KeyError(f"unknown unit {unit!r} for {quantity!r}; add it to {UNITS_FILE.name}")


def standard_unit(quantity: str) -> str:
    return _table()[quantity]["standard"]


def to_std(value: float | None, quantity: str, unit: str) -> float | None:
    if value is None:
        return None
    u = _unit(quantity, unit)
    return value * u["factor"] + u.get("offset", 0)


def from_std(value: float | None, quantity: str, unit: str) -> float | None:
    if value is None:
        return None
    u = _unit(quantity, unit)
    return (value - u.get("offset", 0)) / u["factor"]
