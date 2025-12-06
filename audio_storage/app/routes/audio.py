from fastapi import APIRouter, UploadFile, File, Form, HTTPException, status, Path, Depends
from fastapi.responses import FileResponse
from pathlib import Path as PathLib
from app.dependencies import verify_bot_key
from config import FILES_DIR

router = APIRouter()

def _safe_name(name: str) -> str:
    if not name or not isinstance(name, str):
        raise ValueError("Invalid file name")
    base = PathLib(name).name
    stem = PathLib(base).stem
    if stem.strip() == "":
        raise ValueError("Invalid file name")
    return stem

def _mp3_path(name_no_ext: str) -> PathLib:
    return PathLib(FILES_DIR) / f"{name_no_ext}.mp3"

@router.post("/", status_code=status.HTTP_201_CREATED, summary="Upload audio")
async def upload_audio(
    file: UploadFile = File(..., description="Audio file to upload (any filename, will be saved as .mp3)"),
    file_name: str = Form(..., description="Desired file name (without .mp3)"),
    _bot_ok: bool = Depends(verify_bot_key),
):
    try:
        safe = _safe_name(file_name)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid file_name")

    dest = _mp3_path(safe)

    try:
        with dest.open("wb") as f:
            while True:
                chunk = await file.read(1024 * 1024)
                if not chunk:
                    break
                f.write(chunk)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error saving file: {e}")
    finally:
        await file.close()

    return {"file_name": f"{safe}.mp3", "path": str(dest)}

@router.delete("/{file_name}", status_code=status.HTTP_204_NO_CONTENT, summary="Delete audio")
async def delete_audio(
    file_name: str = Path(..., description="File name to delete (without .mp3)"),
    _bot_ok: bool = Depends(verify_bot_key),
):
    try:
        safe = _safe_name(file_name)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid file_name")

    target = _mp3_path(safe)
    if not target.exists():
        raise HTTPException(status_code=404, detail="File not found")

    try:
        target.unlink()
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error deleting file: {e}")

    return

@router.get("/{file_name}", response_class=FileResponse, summary="Download audio")
async def get_audio(
    file_name: str = Path(..., description="File name to download (without .mp3)"),
):
    try:
        safe = _safe_name(file_name)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid file_name")

    target = _mp3_path(safe)
    if not target.exists():
        raise HTTPException(status_code=404, detail="File not found")

    return FileResponse(path=target.as_posix(), filename=target.name, media_type="audio/mpeg")