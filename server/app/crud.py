from typing import List

from app.db import get_conn
from app.schemas import User, UserCreate

def _serialize_audiolist(a: List[int]) -> str:
    return ",".join(str(int(x)) for x in a) if a else ""

def _deserialize_audiolist(s: str) -> List[int]:
    if not s:
        return []
    return [int(x) for x in s.split(",") if x.strip() != ""]

def get_user(user_uuid: str) -> User:
    uid = str(user_uuid)
    with get_conn() as conn:
        cur = conn.execute("SELECT user_uuid, audiolist FROM users WHERE user_uuid = ?", (uid,))
        row = cur.fetchone()
        if not row:
            raise KeyError("User not found")
        audiolist = _deserialize_audiolist(row["audiolist"])
    return User(user_uuid=uid, audiolist=audiolist)

def create_user(user_in: UserCreate) -> User:
    uid = str(user_in.user_uuid)
    with get_conn() as conn:
        cur = conn.execute("SELECT 1 FROM users WHERE user_uuid = ?", (uid,))
        if cur.fetchone():
            raise ValueError("User already exists")
        conn.execute(
            "INSERT INTO users (user_uuid, audiolist) VALUES (?, ?)",
            (uid, _serialize_audiolist(user_in.audiolist))
        )
        conn.commit()
    return User(user_uuid=uid, audiolist=list(user_in.audiolist))

def append_audios(user_uuid: str, audios: List[int]) -> User:
    uid = str(user_uuid)
    with get_conn() as conn:
        cur = conn.execute("SELECT audiolist FROM users WHERE user_uuid = ?", (uid,))
        row = cur.fetchone()
        if not row:
            raise KeyError("User not found")
        current = _deserialize_audiolist(row["audiolist"])
        new_set = set(current)
        for a in audios:
            new_set.add(int(a))
        new_list = list(new_set)
        conn.execute(
            "UPDATE users SET audiolist = ? WHERE user_uuid = ?",
            (_serialize_audiolist(new_list), uid)
        )
        conn.commit()
    return User(user_uuid=uid, audiolist=new_list)

def delete_audio(user_uuid: str, item_id: int) -> User:
    uid = str(user_uuid)
    iid = int(item_id)
    with get_conn() as conn:
        cur = conn.execute("SELECT audiolist FROM users WHERE user_uuid = ?", (uid,))
        row = cur.fetchone()
        if not row:
            raise KeyError("User not found")
        current = _deserialize_audiolist(row["audiolist"])
        try:
            current.remove(iid)
        except ValueError:
            raise KeyError("Audio item not found")
        conn.execute(
            "UPDATE users SET audiolist = ? WHERE user_uuid = ?",
            (_serialize_audiolist(current), uid)
        )
        conn.commit()
    return User(user_uuid=uid, audiolist=current)