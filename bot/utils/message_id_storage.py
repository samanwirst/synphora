import sqlite3
from pathlib import Path
from typing import Optional
import uuid

from config import MESSAGE_ID_STORAGE_PATH

CREATE_TABLE_SQL = """
CREATE TABLE IF NOT EXISTS message_map (
    telegram_message_id INTEGER PRIMARY KEY,
    message_uuid TEXT NOT NULL UNIQUE
);
"""

class MessageIDStorageUtils:
    def __init__(self, db_path: Optional[str | Path] = None):
        self.db_path = Path(db_path) if db_path else MESSAGE_ID_STORAGE_PATH
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._ensure_table()

    def _get_conn(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.db_path.as_posix(), timeout=30)
        conn.row_factory = sqlite3.Row
        return conn

    def _ensure_table(self) -> None:
        with self._get_conn() as conn:
            conn.execute(CREATE_TABLE_SQL)
            conn.commit()

    def get_uuid(self, telegram_message_id: int) -> Optional[str]:
        with self._get_conn() as conn:
            cur = conn.execute(
                "SELECT message_uuid FROM message_map WHERE telegram_message_id = ?",
                (int(telegram_message_id),)
            )
            row = cur.fetchone()
            return row["message_uuid"] if row else None

    def set_uuid(self, telegram_message_id: int, message_uuid: str) -> None:
        with self._get_conn() as conn:
            conn.execute(
                "INSERT OR REPLACE INTO message_map (telegram_message_id, message_uuid) VALUES (?, ?)",
                (int(telegram_message_id), str(message_uuid)),
            )
            conn.commit()

    def generate_and_store(self, telegram_message_id: int) -> str:
        existing = self.get_uuid(telegram_message_id)
        if existing:
            return existing
        new_uuid = str(uuid.uuid4())
        self.set_uuid(telegram_message_id, new_uuid)
        return new_uuid