from fastapi import WebSocket

from voice_server.config import get_settings


def extract_user_id(websocket: WebSocket) -> str | None:
    settings = get_settings()
    if settings.local_mode:
        return "local-dev-user"
    user_id = websocket.headers.get("x-amzn-oidc-identity")
    return user_id


def extract_user_email(websocket: WebSocket) -> str:
    settings = get_settings()
    if settings.local_mode:
        return "dev@localhost"
    protocols = websocket.headers.get("sec-websocket-protocol", "")
    parts = [p.strip() for p in protocols.split(",")]
    for part in parts:
        if "@" in part and "." in part:
            return part
    return ""
