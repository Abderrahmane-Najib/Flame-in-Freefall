"""PostgreSQL connection and schema (the tables are defined in database/schema.sql)."""

from pathlib import Path

import psycopg
from psycopg.rows import dict_row

from core.config import DATABASE_URL

SCHEMA_FILE = Path(__file__).with_name("schema.sql")


def connect() -> psycopg.Connection:
    if not DATABASE_URL:
        raise RuntimeError("DATABASE_URL is not set. Copy app/.env.example to app/.env and fill it in.")
    return psycopg.connect(DATABASE_URL, row_factory=dict_row)


def create_schema(conn: psycopg.Connection) -> None:
    conn.execute(SCHEMA_FILE.read_text(encoding="utf-8"))
