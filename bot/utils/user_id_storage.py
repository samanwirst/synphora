import sqlite3
from pathlib import Path
from typing import Optional
import uuid

from config import USER_ID_STORAGE_PATH

CREATE_TABLE_SQL = """
CREATE TABLE IF NOT EXISTS id_map (
    telegram_user_id INTEGER PRIMARY KEY,
    user_uuid TEXT NOT NULL UNIQUE
);
"""

class UserIDStorageUtils:
    def __init__(self, db_path: Optional[str | Path] = None):
        self.db_path = Path(db_path) if db_path is not None else USER_ID_STORAGE_PATH
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

    def get_user_uuid(self, telegram_user_id: int) -> Optional[str]:
        tid = int(telegram_user_id)
        with self._get_conn() as conn:
            cur = conn.execute(
                "SELECT user_uuid FROM id_map WHERE telegram_user_id = ?",
                (tid,)
            )
            row = cur.fetchone()
            if not row:
                return None
            return row["user_uuid"]

    def set_user_uuid(self, telegram_user_id: int, user_uuid: str) -> None:
        tid = int(telegram_user_id)
        uid = str(user_uuid)
        with self._get_conn() as conn:
            conn.execute(
                "INSERT OR REPLACE INTO id_map (telegram_user_id, user_uuid) VALUES (?, ?)",
                (tid, uid),
            )
            conn.commit()

    def generate_and_store(self, telegram_user_id: int) -> str:
        existing = self.get_user_uuid(telegram_user_id)
        if existing is not None:
            return existing
        new_uuid = str(uuid.uuid4())
        self.set_user_uuid(telegram_user_id, new_uuid)
        return new_uuid