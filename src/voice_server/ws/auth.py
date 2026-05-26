from fastapi import WebSocket

from voice_server.config import get_settings


def extract_user_id(websocket: WebSocket) -> str | None:
    settings = get_settings()
    if settings.local_mode:
        return "local-dev-user"
    user_id = websocket.headers.get("x-amzn-oidc-identity")
    return user_id
