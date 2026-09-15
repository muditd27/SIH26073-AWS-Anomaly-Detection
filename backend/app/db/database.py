import os
import sqlite3
from pathlib import Path

DATABASE_NAME = os.getenv("DB_NAME", "sih26073")
DATABASE_URL = os.getenv("DATABASE_URL")
SQLITE_PATH = Path(__file__).resolve().parent.parent.parent.parent / "db" / "sih26073.db"


def get_connection():
    if DATABASE_URL and (DATABASE_URL.startswith("postgresql://") or DATABASE_URL.startswith("postgres://")):
        import psycopg2
        return psycopg2.connect(DATABASE_URL)
    try:
        import psycopg2
        return psycopg2.connect(dbname=DATABASE_NAME)
    except Exception:
        conn = sqlite3.connect(str(SQLITE_PATH))
        conn.row_factory = sqlite3.Row
        return conn

