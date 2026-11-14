"""Habitat atmospheres and the ranking of investigations by tests run in each habitat's air.

A plain count of tests (no weights): which data is most relevant to that air,
not how dangerous a fire would be there, and nothing about Moon or Mars gravity.
"""

from database.connection import connect

PSI_PAGE = "https://psi.nasa.gov/physci/repo/data/investigations/{}"

GROUPS = ("measured", "from_note", "o2_only", "mixed")
GROUPS_MEANING = {
    "measured": "chamber O2 and pressure both recorded inside the habitat's box: this group alone sets the ranking",
    "from_note": "inside the box, but O2 or pressure comes from a NASA document, not the test table",
    "o2_only": "O2 inside the box, pressure not recorded",
    "mixed": "a row lists several O2 values, so it cannot be counted exactly",
}


def list_habitats() -> list[dict]:
    with connect() as conn:
        return [r["data"] for r in conn.execute("select data from habitats order by id")]


def rank(habitat: str) -> dict | None:
    """The habitat (with sources and assumptions) and the investigations ordered by measured tests.
    None if the habitat id is unknown."""
    with connect() as conn:
        hab = conn.execute("select data from habitats where id = %s", (habitat,)).fetchone()
        if not hab:
            return None
        cards = conn.execute("select id, name, card -> 'habitat_match' -> %s as m from investigations",
                             (habitat,)).fetchall()
    ranked = []
    for c in cards:
        m = c["m"] or {}
        counts = {g: (m.get(g) or {}).get("tests", 0) for g in GROUPS}
        if any(counts.values()):
            ranked.append({"psi_id": c["id"], "name": c["name"], **counts,
                           "measured_with_results": (m.get("measured") or {}).get("with_results", 0),
                           "url": PSI_PAGE.format(c["id"])})
    ranked.sort(key=lambda r: [r[g] for g in GROUPS], reverse=True)
    return {
        "cite": "FlameScope count of NASA PSI test rows in this habitat's air (cleaned PSI test tables)",
        "habitat": hab["data"],
        "groups": GROUPS_MEANING,
        "investigations": ranked,
    }
