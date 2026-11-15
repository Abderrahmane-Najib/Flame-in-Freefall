"""Knowledge graph of the PSI investigations, built from the cards (no extra data).

Nodes: investigation, family (fuel family), material, job (safety job), hardware, habitat.
Edges: investigation -> family | material | job | hardware | habitat (tests measured in that air).
Findings are not nodes (too many to read): each investigation node carries its findings with cite + url.

Materials: the raw fuel names in the test tables are messy ('1/4" clear rod', 'sibal 2 cm'), so they are
mapped to named materials by the patterns below. A raw name that does not say what it is made of
('2 cm sphere', '200 micron film') is left out rather than guessed.
"""

import re

from database.connection import connect

PSI_PAGE = "https://psi.nasa.gov/physci/repo/data/investigations/{}"

# (material id, label, phase, regex on the lowercased raw fuel name). A mixture matches several.
MATERIALS = [
    ("methane", "Methane", "gas", r"ch4|methane"),
    ("ethylene", "Ethylene", "gas", r"c2h4|ethylene"),
    ("ethane", "Ethane", "gas", r"c2h6|\bethane"),
    ("propane", "Propane", "gas", r"c3h8|\bpropane"),
    ("propylene", "Propylene", "gas", r"propylene"),
    ("butane", "n-Butane", "gas", r"butane"),
    ("hydrogen", "Hydrogen", "gas", r"\bh2\b"),
    ("dodecane", "n-Dodecane", "liquid", r"c12h26"),
    ("isododecane", "iso-Dodecane", "liquid", r"iso-dodecane"),
    ("farnesane", "Farnesane", "liquid", r"farnesane"),
    ("decane", "n-Decane", "liquid", r"\bdecane"),
    ("heptane", "n-Heptane", "liquid", r"heptane"),
    ("isooctane", "Isooctane", "liquid", r"isooctane"),
    ("octane", "n-Octane", "liquid", r"n-octane"),
    ("methanol", "Methanol", "liquid", r"methanol"),
    ("ethanol", "Ethanol", "liquid", r"\bethanol"),
    ("propanol", "Propanol", "liquid", r"propanol"),
    ("glycerol", "Glycerol", "liquid", r"glycerol"),
    ("dbp", "Dibutyl phthalate", "liquid", r"dibutyl phthalate"),
    # BASS-II "clear / black rods" are PMMA rods (BASS-II Summary Report; predictors/P10)
    ("pmma", "PMMA (acrylic)", "solid", r"pmma|acrylic|\brod\b"),
    ("sibal", "SIBAL cotton-fiberglass fabric", "solid", r"sibal"),
    ("nomex", "Nomex", "solid", r"nomex"),
    ("silicone", "Silicone", "solid", r"silicone"),
    ("kapton", "Kapton", "solid", r"kapton"),
    ("teflon", "Teflon", "solid", r"teflon"),
    ("lampwick", "Lamp wick", "solid", r"lampwick"),
    ("pyrell", "Pyrell foam", "solid", r"pyrell"),
    ("wax", "Candle wax (paraffin / Japan wax)", "solid", r"wax|candle"),
    ("ultem", "Ultem (PEI)", "solid", r"ultem"),
]

FAMILIES = {
    "solid": "Solid materials", "droplet": "Liquid droplets", "gas": "Gas flames",
    "smoke": "Smoke & detection", "ground": "Ground / lab studies",
}
JOBS = {"prevention": "Prevention", "detection": "Detection", "suppression": "Suppression"}
HARDWARE = {
    "CIR": "Combustion Integrated Rack (CIR)", "ACME": "ACME insert", "MDCA": "Droplet apparatus (MDCA)",
    "MSG": "Microgravity Science Glovebox (MSG)", "Cygnus": "Cygnus cargo vehicle (Saffire)",
    "ground": "Ground laboratory",
}
HABITATS = {"iss": "ISS air", "moon_base_rover": "Moon habitat & rover air", "mars_base": "Mars base air (assumed = Moon)"}
NEAR_LUNAR = ("near_lunar", "Near-lunar air (not lunar)")


def build_graph(cards: list[dict], near_lunar: dict[str, int]) -> dict:
    """cards: the investigation cards. near_lunar: psi_id -> tests in the near-lunar band (from the tests)."""
    nodes, edges, used = {}, [], set()

    def node(nid, ntype, label, **extra):
        nodes.setdefault(nid, {"id": nid, "type": ntype, "label": label, **extra})

    for c in cards:
        iid = c["id"]
        tests = c.get("tests") or {}
        node(iid, "investigation", c["name"], title=c.get("title"), fuel_type=c.get("fuel_type"),
             tests=tests.get("count"), origin=c.get("origin", "psi"),
             url=PSI_PAGE.format(iid) if c.get("origin", "psi") == "psi" else None,
             summary=(c.get("summary") or {}).get("text"),
             findings=[{"text": f["text"], "cite": f.get("cite"), "url": f.get("url")} for f in c.get("findings") or []])

        if c.get("fuel_type") in FAMILIES:
            node("family:" + c["fuel_type"], "family", FAMILIES[c["fuel_type"]])
            edges.append({"source": iid, "target": "family:" + c["fuel_type"], "rel": "fuel family"})

        for job in (c.get("fire_safety") or {}).get("jobs") or []:
            node("job:" + job, "job", JOBS.get(job, job))
            edges.append({"source": iid, "target": "job:" + job, "rel": "informs"})

        for hw in (c.get("hardware_group") or "").split(" + "):
            if hw in HARDWARE:
                node("hw:" + hw, "hardware", HARDWARE[hw])
                edges.append({"source": iid, "target": "hw:" + hw, "rel": "flew on" if hw != "ground" else "run in"})

        mats = {}
        for f in (c.get("conditions") or {}).get("fuels") or []:
            name = (f.get("name") or "").lower()
            for mid, label, phase, pattern in MATERIALS:
                if re.search(pattern, name):
                    mats[mid] = mats.get(mid, 0) + (f.get("tests") or 0)
                    node("mat:" + mid, "material", label, phase=phase)
        for mid, n in mats.items():
            edges.append({"source": iid, "target": "mat:" + mid, "rel": "burned", "tests": n})
            used.add(mid)

        for hid, hlabel in HABITATS.items():
            measured = (((c.get("habitat_match") or {}).get(hid) or {}).get("measured") or {}).get("tests", 0)
            if measured:
                node("hab:" + hid, "habitat", hlabel)
                edges.append({"source": iid, "target": "hab:" + hid, "rel": "tested in this air", "tests": measured})

        if near_lunar.get(iid):
            node("hab:" + NEAR_LUNAR[0], "habitat", NEAR_LUNAR[1])
            edges.append({"source": iid, "target": "hab:" + NEAR_LUNAR[0], "rel": "tested just outside lunar air",
                          "tests": near_lunar[iid]})

    # Habitats with no measured tests still appear, so the gap is visible (e.g. no solid material in Moon air).
    for hid, hlabel in HABITATS.items():
        node("hab:" + hid, "habitat", hlabel)

    return {
        "nodes": list(nodes.values()),
        "edges": edges,
        "notes": [
            "Built from the 24 investigation cards. 'tested in this air' = tests with chamber O2 and pressure both "
            "measured inside the habitat's box; Mars uses the Moon habitat air (team assumption).",
            "Near-lunar = O2 >= 30% at 70.3-72.5 kPa (17 FLEX tests): never lunar.",
            "Materials are grouped from the raw fuel names; names that do not say the material are left out.",
            "Microgravity only: no edge means anything about Moon or Mars gravity.",
        ],
    }


NEAR_LUNAR_SQL = """
select psi_id, count(*) as n from tests
where o2_location is distinct from 'burner_stream' and o2_pct >= 30 and pressure_kpa > 70.3 and pressure_kpa <= 72.5
group by psi_id
"""


def graph() -> dict:
    with connect() as conn:
        cards = [r["card"] for r in conn.execute("select card from investigations order by id")]
        near = {r["psi_id"]: r["n"] for r in conn.execute(NEAR_LUNAR_SQL)}
    return build_graph(cards, near)
