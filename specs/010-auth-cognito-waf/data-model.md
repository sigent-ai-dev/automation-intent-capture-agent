# Data Model: Cognito + WAF Authentication

## Entities

### CognitoUser (managed by AWS Cognito)

| Field | Type | Notes |
|-------|------|-------|
| sub | UUID | Cognito-assigned unique identifier |
| email | string | Unique, used as username |
| email_verified | boolean | Must be true before access granted |
| created_at | datetime | Auto-set by Cognito |
| updated_at | datetime | Auto-set by Cognito |

Not stored in application database — read from JWT claims.

### JWTClaims (extracted from access token)

```python
@dataclass(frozen=True)
class JWTClaims:
    sub: str           # User UUID
    email: str         # User email
    token_use: str     # "access" or "id"
    exp: int           # Expiration timestamp
    iss: str           # Issuer URL (Cognito pool)
    aud: str           # Client ID
    auth_time: int     # Time of authentication
```

### AuthConfig (application configuration)

```python
@dataclass(frozen=True)
class AuthConfig:
    cognito_user_pool_id: str   # e.g. "eu-west-1_AbCdEf123"
    cognito_client_id: str      # e.g. "1a2b3c4d5e6f7g8h9i0j"
    cognito_region: str         # e.g. "eu-west-1"
    local_mode: bool            # Skip auth when True
```

Derived values:
- `issuer = f"https://cognito-idp.{region}.amazonaws.com/{pool_id}"`
- `jwks_url = f"{issuer}/.well-known/jwks.json"`

## Token Lifecycle

```
User signs in → Cognito returns:
├── Access Token (JWT, 1hr TTL) — used for API auth
├── ID Token (JWT, 1hr TTL) — contains user claims
└── Refresh Token (opaque, 30-day TTL) — used to get new access/ID tokens

Frontend stores tokens in memory (Amplify manages this).
On expiry: Amplify auto-refreshes using refresh token.
On refresh token expiry: User must re-authenticate.
```

## WebSocket Auth Flow

```
1. Frontend: fetchAuthSession() → accessToken
2. Frontend: new WebSocket(`ws://host/ws/audio?token=${accessToken}`)
3. Backend: extract token from query param
4. Backend: fetch JWKS (cached), validate signature + claims
5. Backend: extract sub + email → associate with session
6. Backend: accept() or close(4001/4003)
```

## WAF Rules

| Rule | Priority | Action | Config |
|------|----------|--------|--------|
| RateLimit | 1 | Block | 100 requests/min per IP |
| BodySizeLimit | 2 | Block | Body > 8KB (REST only, excludes WS frames) |
| Default | — | Allow | All other traffic passes |

## Relationship to Existing Entities

- `CaptureSession.participants` → populated with `JWTClaims.email` on session create
- `CaptureSession` created only if JWT validation passes
- WebSocket `session_ready` message includes `user_id` from `JWTClaims.sub`
