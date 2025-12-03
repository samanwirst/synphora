from typing import List

from app.db import get_conn
from app.schemas import User, UserCreate

def _serialize_audiolist(a: List[int]) -> str:
    return ",".join(str(int(x)) for x in a) if a else ""

def _deserialize_audiolist(s: str) -> List[int]:
    if not s:
        return []
    return [int(x) for x in s.split(",") if x.strip() != ""]

def get_user(telegram_user_id: int) -> User:
    tid = int(telegram_user_id)
    with get_conn() as conn:
        cur = conn.execute("SELECT telegram_user_id, audiolist FROM users WHERE telegram_user_id = ?", (tid,))
        row = cur.fetchone()
        if not row:
            raise KeyError("User not found")
        audiolist = _deserialize_audiolist(row["audiolist"])
    return User(telegram_user_id=tid, audiolist=audiolist)

def create_user(user_in: UserCreate) -> User:
    tid = int(user_in.telegram_user_id)
    with get_conn() as conn:
        cur = conn.execute("SELECT 1 FROM users WHERE telegram_user_id = ?", (tid,))
        if cur.fetchone():
            raise ValueError("User already exists")
        conn.execute(
            "INSERT INTO users (telegram_user_id, audiolist) VALUES (?, ?)",
            (tid, _serialize_audiolist(user_in.audiolist))
        )
        conn.commit()   
    return User(telegram_user_id=tid, audiolist=list(user_in.audiolist))

def append_audios(telegram_user_id: int, audios: List[int]) -> User:
    tid = int(telegram_user_id)
    with get_conn() as conn:
        cur = conn.execute("SELECT audiolist FROM users WHERE telegram_user_id = ?", (tid,))
        row = cur.fetchone()
        if not row:
            raise KeyError("User not found")
        current = _deserialize_audiolist(row["audiolist"])
        new_set = set(current)
        for a in audios:
            new_set.add(int(a))
        new_list = list(new_set)
        conn.execute(
            "UPDATE users SET audiolist = ? WHERE telegram_user_id = ?",
            (_serialize_audiolist(new_list), tid)
        )
        conn.commit()
    return User(telegram_user_id=tid, audiolist=new_list)

def delete_audio(telegram_user_id: int, item_id: int) -> User:
    tid = int(telegram_user_id)
    iid = int(item_id)
    with get_conn() as conn:
        cur = conn.execute("SELECT audiolist FROM users WHERE telegram_user_id = ?", (tid,))
        row = cur.fetchone()
        if not row:
            raise KeyError("User not found")
        current = _deserialize_audiolist(row["audiolist"])
        try:
            current.remove(iid)
        except ValueError:
            raise KeyError("Audio item not found")
        conn.execute(
            "UPDATE users SET audiolist = ? WHERE telegram_user_id = ?",
            (_serialize_audiolist(current), tid)
        )
        conn.commit()
    return User(telegram_user_id=tid, audiolist=current)