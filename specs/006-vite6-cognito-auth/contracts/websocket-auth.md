# Contract: WebSocket Authentication

**Type**: Protocol extension | **Scope**: Frontend ↔ Backend WebSocket handshake

## Token Delivery Mechanism

The Cognito ID token is passed via the `Sec-WebSocket-Protocol` header during the WebSocket upgrade request.

## Client Behavior

```
new WebSocket(wsUrl, ['v1.audio.intent', cognitoIdToken])
```

- First protocol value: application protocol identifier (`v1.audio.intent`)
- Second protocol value: Cognito ID token (JWT string)

## Server Behavior

1. Extract `Sec-WebSocket-Protocol` header from upgrade request
2. Parse protocol list: first = app protocol, second = token
3. Validate JWT against Cognito user pool (issuer, signature, expiry)
4. If valid: accept connection, echo `v1.audio.intent` as selected protocol
5. If invalid: reject with HTTP 401

## Failure Modes

| Scenario                   | Server Response | Client Behavior                |
| -------------------------- | --------------- | ------------------------------ |
| No token in protocols      | 401             | Redirect to login              |
| Expired token              | 401             | Attempt token refresh, retry   |
| Invalid signature          | 401             | Redirect to login              |
| Malformed JWT              | 401             | Redirect to login              |

## Backward Compatibility

The existing `codec_negotiate` → `codec_ack` → `session_ready` message flow remains unchanged after the handshake completes. Authentication is purely at the connection upgrade level.
