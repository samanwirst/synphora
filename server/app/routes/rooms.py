from fastapi import APIRouter, Depends, Path, status

from app.dependencies import verify_bot_key, verify_telegram_init_data
from app.rooms_store import rooms_store
from app.schemas import (
    RoomBaseResponse,
    RoomControlRequest,
    RoomCreateRequest,
    RoomCreateResponse,
    RoomPinAuthRequest,
    RoomPinAuthResponse,
    RoomSocketAuthRequest,
    RoomSocketAuthResponse,
)

router = APIRouter()


@router.post("/", response_model=RoomCreateResponse, status_code=status.HTTP_201_CREATED)
async def create_room(payload: RoomCreateRequest, _bot_ok: bool = Depends(verify_bot_key)):
    return rooms_store.create_room(
        creator_user_uuid=payload.creator_user_uuid,
        creator_telegram_id=payload.creator_telegram_id,
        track_ids=payload.track_ids,
    )


@router.get("/{room_id}", response_model=RoomBaseResponse)
async def get_room(room_id: str = Path(..., description="Room UUID")):
    return rooms_store.get_public_room(room_id)


@router.post("/{room_id}/auth-pin", response_model=RoomPinAuthResponse)
async def auth_pin(
    payload: RoomPinAuthRequest,
    room_id: str = Path(..., description="Room UUID"),
):
    telegram_user_id = verify_telegram_init_data(payload.init_data)
    control_token = rooms_store.claim_control_token(
        room_id=room_id,
        pin_code=payload.pin_code,
        telegram_user_id=telegram_user_id,
    )
    return {"room_id": room_id, "control_token": control_token}


@router.post("/{room_id}/socket-auth", response_model=RoomSocketAuthResponse)
async def socket_auth(
    payload: RoomSocketAuthRequest,
    room_id: str = Path(..., description="Room UUID"),
):
    return rooms_store.authorize_socket(room_id=room_id, control_token=payload.control_token)


@router.post("/{room_id}/control", response_model=RoomBaseResponse)
async def control_room(
    payload: RoomControlRequest,
    room_id: str = Path(..., description="Room UUID"),
):
    return rooms_store.apply_control(room_id=room_id, payload=payload)
