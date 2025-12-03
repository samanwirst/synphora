from fastapi import APIRouter, HTTPException, Path, status, Depends
from app.schemas import User, UserCreate, AudiolistPayload
from app import crud
from app.dependencies import verify_bot_key

router = APIRouter()

@router.get("/{user_uuid}", response_model=User)
async def get_user(user_uuid: str = Path(..., description="User UUID")):
    try:
        return crud.get_user(user_uuid)
    except KeyError:
        raise HTTPException(status_code=404, detail="User not found")

@router.post("/", response_model=User, status_code=status.HTTP_201_CREATED)
async def create_user(
    user: UserCreate, 
    _bot_ok: bool = Depends(verify_bot_key
)):
    try:
        return crud.create_user(user)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.post("/{user_uuid}/audiolist", response_model=User)
async def add_audiolist(
    user_uuid: str = Path(..., description="User UUID"),
    payload: AudiolistPayload | None = None,
    _bot_ok: bool = Depends(verify_bot_key),
):
    audios = payload.audiolist if payload is not None else []
    try:
        return crud.append_audios(user_uuid, audios)
    except KeyError:
        raise HTTPException(status_code=404, detail="User not found")

@router.delete("/{user_uuid}/audiolist/{item_id}", response_model=User)
async def delete_audiolist_item(
    user_uuid: str = Path(..., description="User UUID"),
    item_id: int = Path(..., description="Audio item id to delete"),
    _bot_ok: bool = Depends(verify_bot_key),
):
    try:
        return crud.delete_audio(user_uuid, item_id)
    except KeyError as e:
        raise HTTPException(status_code=404, detail=str(e))