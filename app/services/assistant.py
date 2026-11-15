"""The FlameScope assistant: an Agno agent on Groq, with tools over our database.

Tools: report search, one investigation's card, the list of investigations, ranking for a habitat's air,
test rows filtered by conditions, and a chart of test rows (make_chart).

Charts: make_chart draws from the database, never from numbers the model writes. The full chart goes into
agent.charts (streamed to the UI by services/chat.py); the model only gets a short summary back.
"""

import json

from agno.agent import Agent
from agno.db.in_memory import InMemoryDb
from agno.models.groq import Groq

from core.config import GROQ_API_KEY, GROQ_MODEL
from services import charts, habitats, investigations, tests_query
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
    "When a picture helps (comparing conditions, a trend, counts per experiment), call make_chart once: "
    "the user sees the chart under your answer. Do not redraw it as text, ASCII or a markdown image. Describe it only with the numbers "
    "in make_chart's summary (you cannot see the points), say what the colours mean as the summary states, and cite its tables. "
    "For a process, sequence or relations (how a test runs, what affects what, which experiment informs which job), "
    "you may add one diagram as a ```mermaid code block: 'flowchart TD' or 'flowchart LR', at most 10 nodes, "
    "short plain labels (no quotes, brackets or parentheses inside labels), only facts from tool results, no numbers that are not in them. "
    "It is shown as an illustration, never as data.",
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
    card = investigations.get_card(psi_id)
    if not card:
        return json.dumps({"error": f"unknown id {psi_id}"})
    return json.dumps({k: card.get(k) for k in CARD_FIELDS})


def list_investigations(fuel_type: str | None = None) -> str:
    """List investigations: id, short name, fuel type and fire-safety jobs.

    Args:
        fuel_type: optional filter: 'solid', 'droplet', 'gas', 'smoke' or 'ground'. Leave empty for all 24.

    Returns:
        JSON list, one entry per investigation.
    """
    keep = ("id", "name", "fuel_type", "safety_jobs")  # short: the list is sent to the model
    return json.dumps([{k: r[k] for k in keep} for r in investigations.list_investigations(fuel_type)])


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
    result = habitats.rank(habitat)
    if not result:
        return json.dumps({"error": f"unknown habitat {habitat}", "habitats": ["iss", "moon_base_rover", "mars_base"]})
    return json.dumps(result)


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


def chart_tool(drawn: list, psi_id: str | None = None):
    """A make_chart tool whose charts go into `drawn`. psi_id: lock it to one investigation (card chat)."""

    def make_chart(
        kind: str = "scatter",
        x: str = "o2_pct",
        y: str = "pressure_kpa",
        group_by: str = "fuel_type",
        title: str = "",
        fuel: str | None = None,
        fuel_type: str | None = None,
        psi: str | None = None,
        o2_min: float | None = None,
        o2_max: float | None = None,
        pressure_min_kpa: float | None = None,
        pressure_max_kpa: float | None = None,
        lunar_air: bool | None = None,
        has_result: bool | None = None,
    ) -> str:
        """Draw a chart of NASA test rows for the user (data from the test tables, not from you).

        Args:
            kind: 'scatter' (x vs y, one dot per row) or 'bar' (fires per group).
            x: 'o2_pct', 'pressure_kpa', 'flow_cm_s' or a numeric result field from query_tests rows (e.g. 'burn_time_s').
            y: same choices as x.
            group_by: scatter: 'fuel_type' or 'fuel'; bar: 'psi_id', 'fuel' or 'fuel_type'.
            title: short title.
            fuel, fuel_type, psi, o2_min, o2_max, pressure_min_kpa, pressure_max_kpa, lunar_air, has_result: filters, as in query_tests.

        Returns:
            Summary of the chart: counts, ranges, source tables to cite.
        """
        filters = {"psi_id": psi_id or psi, "fuel": fuel, "fuel_type": fuel_type, "o2_min": o2_min, "o2_max": o2_max,
                   "pressure_min_kpa": pressure_min_kpa, "pressure_max_kpa": pressure_max_kpa,
                   "lunar_air": lunar_air, "has_result": has_result}
        spec, summary = charts.build_chart(kind, filters, x, y, group_by, title)
        if spec:
            drawn.append(spec)
        return summary

    return make_chart


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
    drawn = []
    agent = Agent(
        model=Groq(id=GROQ_MODEL, api_key=GROQ_API_KEY),
        tools=[search_reports, get_investigation, list_investigations, rank_for_habitat, query_tests, chart_tool(drawn)],
        instructions=INSTRUCTIONS + [PERSONAS[persona]],
        markdown=True,
        db=_db,
        add_history_to_context=True,  # the last 3 questions and answers of the same session_id
        num_history_runs=3,
        tool_call_limit=6,         # stops a model that loops on the same calls (and burns the token limit)
        debug_mode=debug,          # prints every message sent to and received from the model
    )
    agent.charts = drawn  # filled by make_chart; services/chat.py streams them
    return agent


def make_card_agent(psi_id: str, name: str, persona: str = "researcher") -> Agent:
    """The chat inside one card's drawer: its tools are locked to that investigation (card, reports, tests)."""

    def get_card() -> str:
        """Get this investigation's card: summary, findings and limitations (each with its source), test counts.

        Returns:
            The card as JSON.
        """
        return get_investigation(psi_id)

    def search_card_reports(query: str) -> str:
        """Search this investigation's reports for passages that answer a question.

        Args:
            query: the question or keywords, in English.

        Returns:
            JSON with passages, each with its text, PDF page, url and 'cite' line.
        """
        return search_reports(query, psi_id)

    def query_card_tests(
        fuel: str | None = None,
        o2_min: float | None = None,
        o2_max: float | None = None,
        pressure_min_kpa: float | None = None,
        pressure_max_kpa: float | None = None,
        flow_min_cm_s: float | None = None,
        flow_max_cm_s: float | None = None,
        lunar_air: bool | None = None,
        has_result: bool | None = None,
    ) -> str:
        """Find this investigation's fire tests under given conditions (all filters optional).

        Args:
            fuel: part of the fuel name, e.g. 'heptane'.
            o2_min: lowest chamber oxygen, in %.
            o2_max: highest chamber oxygen, in %.
            pressure_min_kpa: lowest pressure, in kPa (101.3 = sea level).
            pressure_max_kpa: highest pressure, in kPa.
            flow_min_cm_s: lowest flow, in cm/s.
            flow_max_cm_s: highest flow, in cm/s.
            lunar_air: true = only tests in lunar air (30% O2 or more at 70.3 kPa or less).
            has_result: true = only tests with a recorded outcome.

        Returns:
            JSON: totals and ranges of all matches, up to 10 rows (each with cite + url), more_rows if there are more.
        """
        return query_tests(psi_id, fuel, None, o2_min, o2_max, pressure_min_kpa, pressure_max_kpa,
                           flow_min_cm_s, flow_max_cm_s, lunar_air, has_result)

    drawn = []
    agent = Agent(
        model=Groq(id=GROQ_MODEL, api_key=GROQ_API_KEY),
        tools=[get_card, search_card_reports, query_card_tests, chart_tool(drawn, psi_id)],
        instructions=[
            f"You answer questions about one investigation only: {name} ({psi_id}). "
            "If asked about anything else, say this chat covers only this card and suggest the main assistant.",
        ] + INSTRUCTIONS[1:-2] + INSTRUCTIONS[-1:] + [PERSONAS[persona]],  # same rules, minus the intro and list rule
        markdown=True,
        db=_db,
        add_history_to_context=True,
        num_history_runs=3,
        tool_call_limit=5,
    )
    agent.charts = drawn
    return agent


def make_report_agent(doc_id: int, file: str, persona: str = "researcher") -> Agent:
    """The chat that opens with one uploaded report: it searches only that report."""

    def search_report(query: str) -> str:
        """Search the uploaded report for passages that answer a question.

        Args:
            query: the question or keywords, in English.

        Returns:
            JSON with passages, each with its text, PDF page, url and 'cite' line.
        """
        hits = search(query, k=6, include_unreviewed=True, document_id=doc_id)["results"]
        return json.dumps([{k: h[k] for k in ("text", "page", "url", "cite")} for h in hits])

    return Agent(
        model=Groq(id=GROQ_MODEL, api_key=GROQ_API_KEY),
        tools=[search_report],
        instructions=[
            f"You answer questions about one report the user uploaded: '{file}'. Only this report, no other knowledge.",
            "Use search_report for every fact. Never state a number or condition that is not in a passage.",
            "Cite each claim as a markdown link [cite](url), copying the 'cite' line and url of the passage.",
            "If the report does not say it, answer that it is not in the report.",
            "This is a user upload, not reviewed by NASA or FlameScope: never present it as NASA PSI data.",
            "A finding holds only for the conditions the report states (gravity, oxygen, pressure): never move it.",
            "Never call the same tool with the same arguments twice.",
            PERSONAS[persona],
        ],
        markdown=True,
        db=_db,
        add_history_to_context=True,
        num_history_runs=3,
        tool_call_limit=4,
    )


def clean_citation(text: str) -> str:
    """gpt-oss wraps links in its own brackets: '【cite](url)】' -> '[cite](url)'. Works chunk by chunk."""
    return text.replace("【", "[").replace("】", "")
