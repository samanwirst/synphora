from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
import secrets
import threading
import uuid
from typing import Literal, TypedDict

from fastapi import HTTPException, status

from app.schemas import RoomControlRequest


PIN_TTL_SECONDS = 24 * 60 * 60
PIN_MAX_ATTEMPTS = 5
PIN_LOCK_SECONDS = 2 * 60
AUDIO_PROXY_PREFIX = "/api/audio/files"


def _utc_now() -> datetime:
    return datetime.now(timezone.utc)


def _to_unix_ms(dt: datetime) -> int:
    return int(dt.timestamp() * 1000)


def _clean_track_ids(track_ids: list[str]) -> list[str]:
    cleaned: list[str] = []
    seen: set[str] = set()
    for raw in track_ids:
        item = str(raw).strip()
        if item == "" or item in seen:
            continue
        seen.add(item)
        cleaned.append(item)
    return cleaned


class SerializedRoomTrack(TypedDict):
    track_id: str
    url: str


class SerializedRoomState(TypedDict):
    current_track_index: int
    position_sec: float
    is_playing: bool
    playback_rate: float
    version: int
    updated_at_ms: int


class SerializedRoomPublic(TypedDict):
    room_id: str
    playlist: list[SerializedRoomTrack]
    state: SerializedRoomState
    is_active: bool


class SerializedRoomCreate(SerializedRoomPublic):
    pin_code: str


class SerializedRoomSocketAuth(SerializedRoomPublic):
    role: Literal["creator", "listener"]


@dataclass
class RoomTrackData:
    track_id: str
    url: str


@dataclass
class RoomPlaybackStateData:
    current_track_index: int = 0
    position_sec: float = 0.0
    is_playing: bool = False
    playback_rate: float = 1.0
    version: int = 1
    updated_at: datetime = field(default_factory=_utc_now)


@dataclass
class RoomData:
    room_id: str
    creator_user_uuid: str
    creator_telegram_id: int
    pin_code: str
    pin_issued_at: datetime
    playlist: list[RoomTrackData]
    state: RoomPlaybackStateData = field(default_factory=RoomPlaybackStateData)
    control_token: str | None = None
    pin_used: bool = False
    pin_attempts: int = 0
    pin_lock_until: datetime | None = None
    is_active: bool = True


class RoomsStore:
    def __init__(self):
        self._rooms: dict[str, RoomData] = {}
        self._lock = threading.RLock()

    @staticmethod
    def _effective_position(room: RoomData, now: datetime) -> float:
        position = max(0.0, room.state.position_sec)
        if room.state.is_playing:
            elapsed = max(0.0, (now - room.state.updated_at).total_seconds())
            position += elapsed * room.state.playback_rate
        return max(0.0, position)

    def _sync_state(self, room: RoomData, now: datetime) -> None:
        room.state.position_sec = self._effective_position(room, now)
        room.state.updated_at = now

    def _room_or_404(self, room_id: str) -> RoomData:
        room = self._rooms.get(room_id)
        if room is None or not room.is_active:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Room not found")
        return room

    def _serialize_state(self, room: RoomData) -> SerializedRoomState:
        now = _utc_now()
        position = self._effective_position(room, now)
        return {
            "current_track_index": room.state.current_track_index,
            "position_sec": position,
            "is_playing": room.state.is_playing,
            "playback_rate": room.state.playback_rate,
            "version": room.state.version,
            "updated_at_ms": _to_unix_ms(now),
        }

    def _serialize_playlist(self, room: RoomData) -> list[SerializedRoomTrack]:
        return [{"track_id": track.track_id, "url": track.url} for track in room.playlist]

    def _serialize_public(self, room: RoomData) -> SerializedRoomPublic:
        return {
            "room_id": room.room_id,
            "playlist": self._serialize_playlist(room),
            "state": self._serialize_state(room),
            "is_active": room.is_active,
        }

    @staticmethod
    def _require_position(payload: RoomControlRequest) -> float:
        if payload.position_sec is None:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="position_sec is required")
        return payload.position_sec

    @staticmethod
    def _require_playback_rate(payload: RoomControlRequest) -> float:
        if payload.playback_rate is None:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="playback_rate is required")
        return payload.playback_rate

    @staticmethod
    def _require_track_index(payload: RoomControlRequest, playlist_size: int) -> int:
        if payload.track_index is None:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="track_index is required")
        if payload.track_index >= playlist_size:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="track_index is out of range")
        return payload.track_index

    @staticmethod
    def _apply_play(room: RoomData, payload: RoomControlRequest) -> None:
        if payload.position_sec is not None:
            room.state.position_sec = payload.position_sec
        room.state.is_playing = True

    @staticmethod
    def _apply_pause(room: RoomData, payload: RoomControlRequest) -> None:
        if payload.position_sec is not None:
            room.state.position_sec = payload.position_sec
        room.state.is_playing = False

    def _apply_seek(self, room: RoomData, payload: RoomControlRequest) -> None:
        room.state.position_sec = self._require_position(payload)

    def _apply_set_rate(self, room: RoomData, payload: RoomControlRequest) -> None:
        room.state.playback_rate = self._require_playback_rate(payload)

    @staticmethod
    def _apply_next(room: RoomData) -> None:
        room.state.current_track_index = (room.state.current_track_index + 1) % len(room.playlist)
        room.state.position_sec = 0.0

    @staticmethod
    def _apply_prev(room: RoomData) -> None:
        room.state.current_track_index = (room.state.current_track_index - 1 + len(room.playlist)) % len(room.playlist)
        room.state.position_sec = 0.0

    def _apply_set_track(self, room: RoomData, payload: RoomControlRequest) -> None:
        room.state.current_track_index = self._require_track_index(payload, len(room.playlist))
        room.state.position_sec = 0.0

    def create_room(self, creator_user_uuid: str, creator_telegram_id: int, track_ids: list[str]) -> SerializedRoomCreate:
        cleaned_ids = _clean_track_ids(track_ids)
        if not cleaned_ids:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="track_ids cannot be empty")

        room_id = str(uuid.uuid4())
        pin_code = f"{secrets.randbelow(1_000_000):06d}"
        playlist = [RoomTrackData(track_id=item, url=f"{AUDIO_PROXY_PREFIX}/{item}") for item in cleaned_ids]
        room = RoomData(
            room_id=room_id,
            creator_user_uuid=str(creator_user_uuid),
            creator_telegram_id=int(creator_telegram_id),
            pin_code=pin_code,
            pin_issued_at=_utc_now(),
            playlist=playlist,
        )
        with self._lock:
            self._rooms[room_id] = room
            return {
                **self._serialize_public(room),
                "pin_code": pin_code,
            }

    def get_public_room(self, room_id: str) -> SerializedRoomPublic:
        with self._lock:
            room = self._room_or_404(room_id)
            return self._serialize_public(room)

    def claim_control_token(self, room_id: str, pin_code: str, telegram_user_id: int) -> str:
        with self._lock:
            room = self._room_or_404(room_id)
            now = _utc_now()

            if room.creator_telegram_id != int(telegram_user_id):
                raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="PIN is only for room creator")

            if room.pin_used:
                raise HTTPException(status_code=status.HTTP_410_GONE, detail="PIN already used")

            if now > room.pin_issued_at + timedelta(seconds=PIN_TTL_SECONDS):
                raise HTTPException(status_code=status.HTTP_410_GONE, detail="PIN expired")

            if room.pin_lock_until and now < room.pin_lock_until:
                raise HTTPException(
                    status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                    detail="Too many failed attempts. Try again later",
                )

            if not secrets.compare_digest(room.pin_code, str(pin_code)):
                room.pin_attempts += 1
                if room.pin_attempts >= PIN_MAX_ATTEMPTS:
                    room.pin_attempts = 0
                    room.pin_lock_until = now + timedelta(seconds=PIN_LOCK_SECONDS)
                raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid PIN code")

            room.pin_used = True
            room.pin_attempts = 0
            room.pin_lock_until = None
            room.control_token = secrets.token_urlsafe(48)
            room.pin_code = ""
            return room.control_token

    def authorize_socket(self, room_id: str, control_token: str | None) -> SerializedRoomSocketAuth:
        with self._lock:
            room = self._room_or_404(room_id)
            role: Literal["creator", "listener"] = "listener"

            if control_token and room.control_token and secrets.compare_digest(control_token, room.control_token):
                role = "creator"

            return {
                **self._serialize_public(room),
                "role": role,
            }

    def apply_control(self, room_id: str, payload: RoomControlRequest) -> SerializedRoomPublic:
        with self._lock:
            room = self._room_or_404(room_id)

            if (
                room.control_token is None
                or not payload.control_token
                or not secrets.compare_digest(payload.control_token, room.control_token)
            ):
                raise HTTPException(
                    status_code=status.HTTP_405_METHOD_NOT_ALLOWED,
                    detail="Method Not Allowed for listeners",
                )

            if not room.playlist:
                raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Room playlist is empty")

            now = _utc_now()
            self._sync_state(room, now)

            if payload.action == "play":
                self._apply_play(room, payload)
            elif payload.action == "pause":
                self._apply_pause(room, payload)
            elif payload.action == "seek":
                self._apply_seek(room, payload)
            elif payload.action == "set_rate":
                self._apply_set_rate(room, payload)
            elif payload.action == "next":
                self._apply_next(room)
            elif payload.action == "prev":
                self._apply_prev(room)
            elif payload.action == "set_track":
                self._apply_set_track(room, payload)

            room.state.version += 1
            room.state.updated_at = _utc_now()
            return self._serialize_public(room)


rooms_store = RoomsStore()
