import hashlib
import hmac
import json
from datetime import datetime, timezone
from urllib.parse import parse_qsl

from fastapi import Header, HTTPException, status
from config import API_SECRET_BOT_KEY, BOT_TOKEN

async def verify_bot_key(x_api_key: str | None = Header(None)) -> bool:
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


def verify_telegram_init_data(init_data: str) -> int:
    if not BOT_TOKEN:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Server configuration error: BOT_TOKEN not set",
        )

    if not init_data:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="init_data is required")

    pairs = dict(parse_qsl(init_data, keep_blank_values=True))
    incoming_hash = pairs.pop("hash", None)
    if not incoming_hash:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid Telegram init_data")

    data_check_string = "\n".join(f"{k}={v}" for k, v in sorted(pairs.items()))
    secret_key = hmac.new(b"WebAppData", BOT_TOKEN.encode("utf-8"), hashlib.sha256).digest()
    expected_hash = hmac.new(secret_key, data_check_string.encode("utf-8"), hashlib.sha256).hexdigest()

    if not hmac.compare_digest(expected_hash, incoming_hash):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid Telegram signature")

    auth_date_raw = pairs.get("auth_date")
    if auth_date_raw:
        try:
            auth_dt = datetime.fromtimestamp(int(auth_date_raw), tz=timezone.utc)
            age_seconds = (datetime.now(timezone.utc) - auth_dt).total_seconds()
            if age_seconds > 24 * 60 * 60:
                raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Telegram auth data is too old")
        except ValueError:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid auth_date")

    user_raw = pairs.get("user")
    if not user_raw:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Telegram user data is missing")

    try:
        user_data = json.loads(user_raw)
        user_id = int(user_data["id"])
    except (ValueError, TypeError, KeyError, json.JSONDecodeError):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid Telegram user payload")

    return user_id
