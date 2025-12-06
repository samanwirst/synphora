import sqlite3
from pathlib import Path
from typing import Optional
import uuid

from config import FILE_ID_STORAGE_PATH

CREATE_TABLE_SQL = """
CREATE TABLE IF NOT EXISTS file_map (
    file_uuid TEXT PRIMARY KEY,
    file_id TEXT NOT NULL UNIQUE
);
"""

class FileIDStorageUtils:
    def __init__(self, db_path: Optional[str | Path] = None):
        self.db_path = Path(db_path) if db_path else FILE_ID_STORAGE_PATH
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

    def generate_and_store(self, file_id: str) -> str:
        existing = self.get_uuid_by_file_id(file_id)
        if existing:
            return existing

        new_uuid = str(uuid.uuid4())
        with self._get_conn() as conn:
            conn.execute(
                "INSERT INTO file_map (file_uuid, file_id) VALUES (?, ?)",
                (new_uuid, file_id)
            )
            conn.commit()
        return new_uuid

    def get_file_id(self, file_uuid: str) -> Optional[str]:
        with self._get_conn() as conn:
            cur = conn.execute(
                "SELECT file_id FROM file_map WHERE file_uuid = ?",
                (file_uuid,)
            )
            row = cur.fetchone()
            return row["file_id"] if row else None

    def get_uuid_by_file_id(self, file_id: str) -> Optional[str]:
        with self._get_conn() as conn:
            cur = conn.execute(
                "SELECT file_uuid FROM file_map WHERE file_id = ?",
                (file_id,)
            )
            row = cur.fetchone()
            return row["file_uuid"] if row else None