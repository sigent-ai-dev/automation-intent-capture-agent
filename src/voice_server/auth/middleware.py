"""JWT validation middleware for FastAPI REST and WebSocket endpoints."""

from dataclasses import dataclass

from fastapi import HTTPException, WebSocket
from jose import JWTError, jwt

from voice_server.auth.config import get_auth_config
from voice_server.auth.jwks import get_jwks
from voice_server.observability.logging import get_logger

logger = get_logger(__name__)


@dataclass(frozen=True)
class JWTClaims:
    sub: str
    email: str
    token_use: str
    exp: int
    iss: str


_LOCAL_CLAIMS = JWTClaims(sub="local", email="local@dev", token_use="access", exp=0, iss="local")


async def validate_token(token: str) -> JWTClaims:
    config = get_auth_config()
    jwks = await get_jwks()

    try:
        unverified_header = jwt.get_unverified_header(token)
    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid token")

    kid = unverified_header.get("kid")
    key = next((k for k in jwks.get("keys", []) if k["kid"] == kid), None)

    if not key:
        jwks = await get_jwks(force_refresh=True)
        key = next((k for k in jwks.get("keys", []) if k["kid"] == kid), None)
        if not key:
            raise HTTPException(status_code=401, detail="Invalid token")

    try:
        claims = jwt.decode(
            token,
            key,
            algorithms=["RS256"],
            audience=config.cognito_client_id,
            issuer=config.issuer,
        )
    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid token")

    return JWTClaims(
        sub=claims["sub"],
        email=claims.get("email", ""),
        token_use=claims.get("token_use", ""),
        exp=claims.get("exp", 0),
        iss=claims.get("iss", ""),
    )


async def get_current_user(authorization: str | None = None) -> JWTClaims:
    config = get_auth_config()
    if config.local_mode:
        return _LOCAL_CLAIMS

    if not authorization:
        raise HTTPException(status_code=401, detail="Not authenticated")

    parts = authorization.split(" ")
    if len(parts) != 2 or parts[0].lower() != "bearer":
        raise HTTPException(status_code=401, detail="Invalid authorization scheme")

    return await validate_token(parts[1])


async def validate_ws_token(websocket: WebSocket) -> JWTClaims | None:
    config = get_auth_config()
    if config.local_mode:
        return _LOCAL_CLAIMS

    token = websocket.query_params.get("token")
    if not token:
        await websocket.close(code=4001, reason="Missing auth token")
        return None

    try:
        claims = await validate_token(token)
        return claims
    except HTTPException:
        await websocket.close(code=4003, reason="Invalid token")
        return None
