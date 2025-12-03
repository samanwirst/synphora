import sqlite3
from config import DB_PATH

CREATE_TABLE_SQL = """
CREATE TABLE IF NOT EXISTS users (
    user_uuid TEXT PRIMARY KEY,
    audiolist TEXT NOT NULL DEFAULT ''
);
"""

def get_conn() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_PATH.as_posix(), timeout=30)
    conn.row_factory = sqlite3.Row
    return conn

def init_db() -> None:
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    with get_conn() as conn:
        conn.execute(CREATE_TABLE_SQL)
        conn.commit()