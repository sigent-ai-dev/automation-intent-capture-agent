from fastapi import WebSocket

from voice_server.config import get_settings
from voice_server.observability.logging import get_logger

logger = get_logger(__name__)

EXPECTED_PROTOCOL = "v1.audio.intent"


def validate_token_sync(token: str) -> str | None:
    try:
        from jose import jwt

        unverified_claims = jwt.get_unverified_claims(token)
        return unverified_claims.get("sub")
    except Exception:
        return None


def extract_user_id(websocket: WebSocket) -> str | None:
    settings = get_settings()
    if settings.local_mode:
        return "local-dev-user"

    protocol_header = websocket.headers.get("sec-websocket-protocol", "")
    if not protocol_header:
        logger.warning("ws_auth_missing_protocol_header")
        return None

    parts = [p.strip() for p in protocol_header.split(",")]
    if len(parts) < 2:
        logger.warning("ws_auth_insufficient_protocols", count=len(parts))
        return None

    if parts[0] != EXPECTED_PROTOCOL:
        logger.warning("ws_auth_unexpected_protocol", protocol=parts[0])
        return None

    token = parts[1]
    user_id = validate_token_sync(token)
    if not user_id:
        logger.warning("ws_auth_token_validation_failed")
        return None

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
