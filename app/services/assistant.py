"""The FlameScope assistant: an Agno agent on Groq, with tools over our database.

Tools: report search, one investigation's card, the list of investigations, ranking for a habitat's air,
test rows filtered by conditions.
"""

import json

from agno.agent import Agent
from agno.db.in_memory import InMemoryDb
from agno.models.groq import Groq

from core.config import GROQ_API_KEY, GROQ_MODEL
from database.connection import connect
from services import tests_query
from services.search import search

INSTRUCTIONS = [
    "You answer questions about NASA's 24 PSI combustion investigations, for fire safety in spacecraft and Moon/Mars habitats.",
    "Use the tools for every fact. Never state a number, condition or temperature that is not in a tool result.",
    "Cite each claim as a markdown link [cite](url), copying the 'cite' line and url of the result it came from "
    "(for query_tests rows: [NASA PSI test table <table>, row <row>](url of that table in 'tables')).",
    "A finding holds only for the conditions it states: never move it to other conditions (e.g. a 2 bar result is not lunar air).",
    "If query_tests returns more_rows = true, you saw only a sample: before drawing conclusions, query again with "
    "narrower filters (e.g. one fuel) so every matching row is seen, or say the answer covers only the rows shown.",
    "Keep what NASA measured apart from what it suggests. If the tools return nothing, say it is not in the data.",
    "All data is microgravity. Never claim Moon or Mars gravity results.",
    "Lunar air = 30% O2 or more at 70.3 kPa or less. FLEX tests at 71-72 kPa are 'near-lunar': never call them lunar.",
    "Tool results stay in the conversation: never call the same tool with the same arguments twice.",
    "Call only the tools the question needs. Call list_investigations only to find an id you do not know.",
]


def search_reports(query: str, psi_id: str | None = None) -> str:
    """Search the NASA report pages for passages that answer a question.

    Args:
        query: the question or keywords, in English.
        psi_id: optional, only this investigation, e.g. 'PSI-25'.

    Returns:
        JSON with passages, each with its text, investigation, PDF page, url and 'cite' line.
    """
    hits = search(query, psi_id, k=6)["results"]
    keep = ("text", "investigation", "psi_id", "file", "page", "url", "cite")
    return json.dumps([{k: h[k] for k in keep} for h in hits])


# Card fields the assistant needs; the rest (publications, conditions, raw text) is too large for the model's token limit.
CARD_FIELDS = ("id", "name", "title", "fuel_type", "fire_safety", "summary", "findings", "limitations", "tests", "links")


def get_investigation(psi_id: str) -> str:
    """Get one investigation's card: summary, findings and limitations (each with its source), test counts.

    Args:
        psi_id: the investigation id, e.g. 'PSI-25'. Call list_investigations if unsure.

    Returns:
        The card as JSON, or an error if the id is unknown.
    """
    with connect() as conn:
        row = conn.execute("select card from investigations where id = %s", (psi_id,)).fetchone()
    if not row:
        return json.dumps({"error": f"unknown id {psi_id}"})
    return json.dumps({k: row["card"].get(k) for k in CARD_FIELDS})


def list_investigations(fuel_type: str | None = None) -> str:
    """List investigations: id, short name, fuel type and fire-safety jobs.

    Args:
        fuel_type: optional filter: 'solid', 'droplet', 'gas', 'smoke' or 'ground'. Leave empty for all 24.

    Returns:
        JSON list, one entry per investigation.
    """
    with connect() as conn:
        rows = conn.execute("select id, name, fuel_type, safety_jobs from investigations"
                            " where %(f)s::text is null or fuel_type = %(f)s order by id", {"f": fuel_type}).fetchall()
    return json.dumps(rows)


GROUPS = ("measured", "from_note", "o2_only", "mixed")
GROUPS_MEANING = {
    "measured": "chamber O2 and pressure both recorded inside the habitat's box: this group alone sets the ranking",
    "from_note": "inside the box, but O2 or pressure comes from a NASA document, not the test table",
    "o2_only": "O2 inside the box, pressure not recorded",
    "mixed": "a row lists several O2 values, so it cannot be counted exactly",
}


def rank_for_habitat(habitat: str) -> str:
    """Rank investigations by how many of their fire tests were run in a habitat's air (O2 and pressure).

    A plain count of tests, no weights. It says which data is most relevant to that air,
    not how dangerous a fire would be there, and nothing about Moon or Mars gravity.

    Args:
        habitat: 'iss', 'moon_base_rover' or 'mars_base'.

    Returns:
        JSON: the habitat's air (with sources and assumptions) and the investigations,
        ordered by tests measured in that air; the other groups are listed but do not set the order.
    """
    with connect() as conn:
        hab = conn.execute("select data from habitats where id = %s", (habitat,)).fetchone()
        if not hab:
            ids = [r["id"] for r in conn.execute("select id from habitats order by id")]
            return json.dumps({"error": f"unknown habitat {habitat}", "habitats": ids})
        cards = conn.execute("select id, name, card -> 'habitat_match' -> %s as m from investigations",
                             (habitat,)).fetchall()
    ranked = []
    for c in cards:
        m = c["m"] or {}
        counts = {g: (m.get(g) or {}).get("tests", 0) for g in GROUPS}
        if any(counts.values()):
            ranked.append({"psi_id": c["id"], "name": c["name"], **counts,
                           "url": f"https://psi.nasa.gov/physci/repo/data/investigations/{c['id']}",
                           "measured_with_results": (m.get("measured") or {}).get("with_results", 0)})
    ranked.sort(key=lambda r: [r[g] for g in GROUPS], reverse=True)
    return json.dumps({
        "cite": "FlameScope count of NASA PSI test rows in this habitat's air (cleaned PSI test tables); "
                "link each investigation to its url",
        "habitat": hab["data"], "groups": GROUPS_MEANING, "investigations": ranked,
    })


def query_tests(
    psi_id: str | None = None,
    fuel: str | None = None,
    fuel_type: str | None = None,
    o2_min: float | None = None,
    o2_max: float | None = None,
    pressure_min_kpa: float | None = None,
    pressure_max_kpa: float | None = None,
    flow_min_cm_s: float | None = None,
    flow_max_cm_s: float | None = None,
    lunar_air: bool | None = None,
    has_result: bool | None = None,
) -> str:
    """Find the fire tests NASA ran under given conditions (at least one filter). Use it for numbers:
    how many tests, at which O2 / pressure / flow, with which fuels and results.

    Args:
        psi_id: only this investigation, e.g. 'PSI-159'.
        fuel: part of the fuel name, e.g. 'butane', 'PMMA', 'heptane'.
        fuel_type: 'solid', 'droplet', 'gas', 'smoke' or 'ground'.
        o2_min: lowest chamber oxygen, in %.
        o2_max: highest chamber oxygen, in %.
        pressure_min_kpa: lowest pressure, in kPa (101.3 = sea level).
        pressure_max_kpa: highest pressure, in kPa.
        flow_min_cm_s: lowest flow, in cm/s.
        flow_max_cm_s: highest flow, in cm/s.
        lunar_air: true = only tests in lunar air (30% O2 or more at 70.3 kPa or less).
        has_result: true = only tests with a recorded outcome.

    Returns:
        JSON: totals and ranges of all matches, up to 10 matching rows (each with cite + url),
        and more_rows = true if there are more (add a filter to narrow it down).
    """
    filters = {"psi_id": psi_id, "fuel": fuel, "fuel_type": fuel_type, "o2_min": o2_min, "o2_max": o2_max,
               "pressure_min_kpa": pressure_min_kpa, "pressure_max_kpa": pressure_max_kpa,
               "flow_min_cm_s": flow_min_cm_s, "flow_max_cm_s": flow_max_cm_s,
               "lunar_air": lunar_air, "has_result": has_result}
    return json.dumps(tests_query.query_tests(filters), default=str)


# Same facts and rules for everyone; only the language and depth change.
PERSONAS = {
    "student": "The user is a student. Use plain words, explain any technical term in a few words, keep it short.",
    "researcher": "The user is a researcher. Be precise: give conditions, test counts and ranges, and note data limitations.",
    "engineer": "The user is a spacecraft or habitat engineer. Focus on what the results mean for fire prevention, "
                "detection and suppression design, and state clearly what was not tested.",
}

# Chat history per session_id. In memory: lost when the server restarts (fine for the demo).
_db = InMemoryDb()


def make_agent(persona: str = "researcher", debug: bool = False) -> Agent:
    return Agent(
        model=Groq(id=GROQ_MODEL, api_key=GROQ_API_KEY),
        tools=[search_reports, get_investigation, list_investigations, rank_for_habitat, query_tests],
        instructions=INSTRUCTIONS + [PERSONAS[persona]],
        markdown=True,
        db=_db,
        add_history_to_context=True,  # the last 3 questions and answers of the same session_id
        num_history_runs=3,
        tool_call_limit=6,         # stops a model that loops on the same calls (and burns the token limit)
        debug_mode=debug,          # prints every message sent to and received from the model
    )


def clean_citation(text: str) -> str:
    """gpt-oss wraps links in its own brackets: '【cite](url)】' -> '[cite](url)'. Works chunk by chunk."""
    return text.replace("【", "[").replace("】", "")
