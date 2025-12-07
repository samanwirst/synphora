from contextlib import asynccontextmanager
from fastapi import FastAPI

from app.routes.users import router as users_router
from app.db import init_db

@asynccontextmanager
async def lifespan(app: FastAPI):
    print("App starting")
    init_db()
    try:
        yield
    finally:
        print("App shutting down")

app = FastAPI(lifespan=lifespan, title="Synphora API")

app.include_router(
    users_router,
    prefix="/users",
    tags=["users"],
)