from pydantic import BaseModel, Field
from typing import List, Literal

class UserBase(BaseModel):
    user_uuid: str = Field(..., example="d128a4fc-dc6f-4b11-8c12-657e811e1ace")

class UserCreate(UserBase):
    audiolist: List[str] = Field(default_factory=list, example=["d128a4fc-...", "a7b9c1d2-..."])

class AudiolistPayload(BaseModel):
    audiolist: List[str] = Field(..., example=["d128a4fc-...", "a7b9c1d2-..."])

class User(UserBase):
    audiolist: List[str] = Field(default_factory=list)

    class Config:
        from_attributes = True


class RoomTrack(BaseModel):
    track_id: str = Field(..., example="5e24cfd1-7db6-4e2d-ba84-a5ab96550f7e")
    url: str = Field(..., example="https://audio.example.com/files/5e24cfd1-7db6-4e2d-ba84-a5ab96550f7e")


class RoomPlaybackState(BaseModel):
    current_track_index: int = Field(default=0, ge=0)
    position_sec: float = Field(default=0.0, ge=0.0)
    is_playing: bool = Field(default=False)
    playback_rate: float = Field(default=1.0, gt=0.0, le=4.0)
    version: int = Field(default=1, ge=1)
    updated_at_ms: int = Field(..., ge=0)


class RoomCreateRequest(BaseModel):
    creator_user_uuid: str = Field(..., example="d128a4fc-dc6f-4b11-8c12-657e811e1ace")
    creator_telegram_id: int = Field(..., example=123456789)
    track_ids: List[str] = Field(..., min_length=1, example=["5e24cfd1-7db6-4e2d-ba84-a5ab96550f7e"])


class RoomBaseResponse(BaseModel):
    room_id: str = Field(..., example="8b2bbd37-e3ed-4474-b8e4-6ba53f908a8a")
    playlist: List[RoomTrack] = Field(default_factory=list)
    state: RoomPlaybackState
    is_active: bool = Field(default=True)


class RoomCreateResponse(RoomBaseResponse):
    pin_code: str = Field(..., pattern=r"^\d{6}$", example="391028")


class RoomPinAuthRequest(BaseModel):
    pin_code: str = Field(..., pattern=r"^\d{6}$")
    init_data: str = Field(..., min_length=1)


class RoomPinAuthResponse(BaseModel):
    room_id: str
    control_token: str = Field(..., min_length=32)


class RoomSocketAuthRequest(BaseModel):
    control_token: str | None = None


class RoomSocketAuthResponse(RoomBaseResponse):
    role: Literal["creator", "listener"]


class RoomControlRequest(BaseModel):
    control_token: str = Field(..., min_length=32)
    action: Literal["play", "pause", "seek", "set_rate", "next", "prev", "set_track"]
    position_sec: float | None = Field(default=None, ge=0.0)
    playback_rate: float | None = Field(default=None, gt=0.0, le=4.0)
    track_index: int | None = Field(default=None, ge=0)
