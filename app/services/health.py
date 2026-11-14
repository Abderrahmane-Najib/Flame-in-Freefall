from database.connection import connect

COUNTS_SQL = """
select (select count(*) from investigations)                       as investigations,
       (select count(*) from tests)                                as test_rows,
       (select count(*) from habitats)                             as habitats,
       (select count(*) from documents)                            as documents,
       (select count(*) from pages)                                as pages,
       (select count(*) from chunks)                               as chunks,
       (select count(*) from chunks where embedding is not null)   as chunks_embedded
"""


def database_counts() -> dict:
    with connect() as conn:
        return conn.execute(COUNTS_SQL).fetchone()
