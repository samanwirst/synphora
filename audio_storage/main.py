from fastapi import FastAPI
from app.routes.audio import router as audio_router
from config import FILES_DIR

app = FastAPI(title="Audio Storage API")

@app.on_event("startup")
def on_startup():
    FILES_DIR.mkdir(parents=True, exist_ok=True)

app.include_router(
    audio_router,
    prefix="/files",
    tags=["files"],
)