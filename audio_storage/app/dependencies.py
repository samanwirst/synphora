from typing import Optional
from fastapi import Header, HTTPException, status
from config import API_SECRET_BOT_KEY

async def verify_bot_key(x_api_key: Optional[str] = Header(None)):
    if API_SECRET_BOT_KEY is None:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Server configuration error: API_SECRET_BOT_KEY not set",
        )

    if not x_api_key or x_api_key != API_SECRET_BOT_KEY:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or missing API key",
            headers={"WWW-Authenticate": "API-Key"},
        )

    return True