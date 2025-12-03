from fastapi import APIRouter, HTTPException, Path, status
from app.schemas import User, UserCreate, AudiolistPayload
from app import crud

router = APIRouter()

@router.get("/{telegram_user_id}", response_model=User)
async def get_user(telegram_user_id: int = Path(..., description="Telegram user id")):
    try:
        return crud.get_user(telegram_user_id)
    except KeyError:
        raise HTTPException(status_code=404, detail="User not found")

@router.post("/", response_model=User, status_code=status.HTTP_201_CREATED)
async def create_user(user: UserCreate):
    try:
        return crud.create_user(user)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.post("/{telegram_user_id}/audiolist", response_model=User)
async def add_audiolist(
    telegram_user_id: int = Path(..., description="Telegram user id"),
    payload: AudiolistPayload | None = None,
):
    audios = payload.audiolist if payload is not None else []
    try:
        return crud.append_audios(telegram_user_id, audios)
    except KeyError:
        raise HTTPException(status_code=404, detail="User not found")

@router.delete("/{telegram_user_id}/audiolist/{item_id}", response_model=User)
async def delete_audiolist_item(
    telegram_user_id: int = Path(..., description="Telegram user id"),
    item_id: int = Path(..., description="Audio item id to delete"),
):
    try:
        return crud.delete_audio(telegram_user_id, item_id)
    except KeyError as e:
        raise HTTPException(status_code=404, detail=str(e))