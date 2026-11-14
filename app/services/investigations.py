"""Investigation cards from the database, shared by the API and the assistant."""

from database.connection import connect

LIST_SQL = """
select id, name, title, fuel_type, hardware_group, safety_jobs, in_space,
       card -> 'fire_safety' ->> 'psi_label'        as psi_label,
       card -> 'summary' ->> 'text'                  as summary,
       coalesce(card ->> 'origin', 'psi')            as origin,
       (card -> 'tests' ->> 'count')::int            as tests,
       (card -> 'tests' ->> 'with_results')::int     as tests_with_results,
       (card -> 'tests' ->> 'lunar_air')::int        as lunar_air_tests,
       jsonb_array_length(coalesce(card -> 'findings', '[]'))  as findings
from investigations
where (%(fuel_type)s::text is null or fuel_type = %(fuel_type)s)
  and (%(job)s::text is null or %(job)s = any(safety_jobs))
order by id
"""


def list_investigations(fuel_type: str | None = None, safety_job: str | None = None) -> list[dict]:
    with connect() as conn:
        return conn.execute(LIST_SQL, {"fuel_type": fuel_type, "job": safety_job}).fetchall()


def get_card(psi_id: str) -> dict | None:
    """The full card (data/psi/cards.json), or None if the id is unknown."""
    with connect() as conn:
        row = conn.execute("select card from investigations where id = %s", (psi_id,)).fetchone()
    return row["card"] if row else None
