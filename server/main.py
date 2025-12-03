from fastapi import FastAPI
from app.routes.users import router as users_router
from app.db import init_db

app = FastAPI(title="Synphora API")

@app.on_event("startup")
def on_startup():
    init_db()

app.include_router(
    users_router,
    prefix="/users",
    tags=["users"],
)