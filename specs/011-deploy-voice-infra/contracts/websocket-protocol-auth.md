# Contract: WebSocket Sec-WebSocket-Protocol Authentication

**Type**: Server-side protocol handler | **Scope**: WebSocket upgrade in `ws/auth.py`

## Protocol

The client sends a WebSocket upgrade with two subprotocol values:

```
Sec-WebSocket-Protocol: v1.audio.intent, <cognito-id-token-jwt>
```

## Server Behavior

1. Parse `Sec-WebSocket-Protocol` header → split by `, ` (comma-space)
2. Expect exactly 2 values: `['v1.audio.intent', '<jwt>']`
3. Extract JWT (second value)
4. Validate JWT against Cognito JWKS:
   - Verify signature (RS256)
   - Check issuer matches `https://cognito-idp.{region}.amazonaws.com/{pool_id}`
   - Check expiry (`exp` claim)
   - Extract `sub`, `email`, `cognito:groups`
5. On success: `websocket.accept(subprotocol='v1.audio.intent')`
6. On failure: `websocket.close(code=4001, reason='Unauthorized')`

## Failure Modes

| Scenario                           | Action                        |
| ---------------------------------- | ----------------------------- |
| No Sec-WebSocket-Protocol header   | Close 4001                    |
| Only one protocol value            | Close 4001                    |
| First value != `v1.audio.intent`   | Close 4001                    |
| JWT signature invalid              | Close 4001                    |
| JWT expired                        | Close 4001                    |
| JWT issuer mismatch                | Close 4001                    |
| JWKS endpoint unreachable + no cache | Close 4001 (log warning)    |

## Local Mode Bypass

When `LOCAL_MODE=true`, skip JWT validation and return a synthetic user identity (`local-dev-user`). Accept with `subprotocol='v1.audio.intent'`.

## Response Header

On successful auth, the server MUST include:
```
Sec-WebSocket-Protocol: v1.audio.intent
```

This confirms to the client which subprotocol was selected (omitting the token).
