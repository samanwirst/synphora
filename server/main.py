from fastapi import FastAPI, Depends
from app.routes.users import router as users_router
from app.dependencies import verify_bot_key
from app.db import init_db

app = FastAPI(title="Users API")

@app.on_event("startup")
def on_startup():
    init_db()

app.include_router(
    users_router,
    prefix="/users",
    tags=["users"],
    dependencies=[Depends(verify_bot_key)],
)