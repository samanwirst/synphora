import re
from urllib.parse import urlparse

from config import CLIENT_APP_URL


LISTENER_PAYLOAD_PATTERN = re.compile(
    r"^room_(?P<room_id>[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12})_listener$"
)
LISTENER_QUERY_PATTERN = re.compile(
    r"^room_id=(?P<room_id>[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12})(?:[?&]listener=true)?$"
)
LOCAL_ONLY_HOSTS = {"localhost", "::1"}


def _client_base_url() -> str:
    if not CLIENT_APP_URL:
        raise RuntimeError("CLIENT_APP_URL is not configured")
    return CLIENT_APP_URL.rstrip("/")


def ensure_public_webapp_url() -> None:
    base_url = _client_base_url()
    parsed = urlparse(base_url)
    if parsed.scheme != "https":
        raise RuntimeError("CLIENT_APP_URL must start with https://")

    hostname = (parsed.hostname or "").strip().lower()
    if hostname == "" or hostname in LOCAL_ONLY_HOSTS:
        raise RuntimeError(
            "CLIENT_APP_URL points to localhost. Telegram WebApp requires a public HTTPS domain."
        )


def build_creator_auth_url(room_id: str) -> str:
    return f"{_client_base_url()}/room/{room_id}/auth"


def build_listener_room_url(room_id: str) -> str:
    return f"{_client_base_url()}/room/{room_id}?listener=true"


def build_listener_start_payload(room_id: str) -> str:
    return f"room_{room_id}_listener"


def parse_listener_start_payload(payload: str | None) -> str | None:
    raw = (payload or "").strip()
    if raw == "":
        return None
    match = LISTENER_PAYLOAD_PATTERN.match(raw)
    if match is not None:
        return match.group("room_id")
    query_match = LISTENER_QUERY_PATTERN.match(raw)
    if query_match is not None:
        return query_match.group("room_id")
    return None
