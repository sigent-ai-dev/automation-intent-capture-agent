# Auth Middleware Contract

## Overview

FastAPI dependency that validates Cognito JWT tokens on incoming requests. Used by both REST endpoints and WebSocket upgrade handlers.

---

## REST Endpoints

### Usage

```python
from voice_server.auth.middleware import get_current_user, JWTClaims

@router.post("/sessions")
async def create_session(body: CreateSessionRequest, user: JWTClaims = Depends(get_current_user)):
    # user.sub, user.email available
    ...
```

### Behavior

| Scenario | Input | Response |
|----------|-------|----------|
| Valid token | `Authorization: Bearer <jwt>` | Returns `JWTClaims` |
| Missing header | No Authorization header | `401 {"detail": "Not authenticated"}` |
| Malformed header | `Authorization: NotBearer xxx` | `401 {"detail": "Invalid authorization scheme"}` |
| Expired token | Valid JWT past `exp` | `401 {"detail": "Token expired"}` |
| Invalid signature | Tampered JWT | `401 {"detail": "Invalid token"}` |
| Wrong audience | JWT for different client | `401 {"detail": "Invalid token"}` |
| LOCAL_MODE=true | Any/no header | Returns mock `JWTClaims(sub="local", email="local@dev")` |

---

## WebSocket Endpoint

### Usage

```python
@app.websocket("/ws/audio")
async def ws_audio(websocket: WebSocket):
    token = websocket.query_params.get("token")
    user = await validate_ws_token(token)  # closes with 4001/4003 on failure
    await websocket.accept()
    ...
```

### Behavior

| Scenario | Input | Response |
|----------|-------|----------|
| Valid token | `?token=<jwt>` in URL | Connection accepted, `JWTClaims` returned |
| Missing token | No `token` query param | WebSocket close code 4001, reason "Missing auth token" |
| Invalid token | Bad/expired JWT | WebSocket close code 4003, reason "Invalid token" |
| LOCAL_MODE=true | Any/no token | Connection accepted, mock claims |

### WebSocket Close Codes

| Code | Meaning |
|------|---------|
| 4001 | Authentication required (no token provided) |
| 4003 | Authentication failed (invalid/expired token) |

---

## JWKS Caching

- Keys fetched from `https://cognito-idp.{region}.amazonaws.com/{pool_id}/.well-known/jwks.json`
- Cached in memory for 1 hour (3600s)
- If validation fails with "kid not found", force-refresh cache once (handles key rotation)
- If JWKS endpoint is unreachable, use stale cache (log warning)

---

## Configuration

| Environment Variable | Required | Default | Description |
|---------------------|----------|---------|-------------|
| COGNITO_USER_POOL_ID | Yes (prod) | — | Cognito user pool ID |
| COGNITO_CLIENT_ID | Yes (prod) | — | Cognito app client ID |
| COGNITO_REGION | No | eu-west-1 | AWS region for Cognito |
| LOCAL_MODE | No | false | Skip auth validation entirely |
