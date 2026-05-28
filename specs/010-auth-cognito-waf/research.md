# Research: Cognito + WAF Authentication

## 1. Cognito JWT Validation in FastAPI

**Decision**: Use `python-jose[cryptography]` with cached JWKS keys fetched from Cognito's `.well-known/jwks.json` endpoint.

**Rationale**: `python-jose` is the standard Python JWT library with RS256 support. Caching JWKS avoids a network call on every request — keys rotate infrequently (hours/days).

**Implementation pattern**:
```python
import httpx
from jose import jwt, JWTError
from functools import lru_cache
import time

JWKS_URL = f"https://cognito-idp.{region}.amazonaws.com/{pool_id}/.well-known/jwks.json"

_jwks_cache: dict = {}
_jwks_fetched_at: float = 0
JWKS_CACHE_TTL = 3600  # 1 hour

async def get_jwks() -> dict:
    global _jwks_cache, _jwks_fetched_at
    if time.time() - _jwks_fetched_at < JWKS_CACHE_TTL and _jwks_cache:
        return _jwks_cache
    async with httpx.AsyncClient() as client:
        resp = await client.get(JWKS_URL)
        _jwks_cache = resp.json()
        _jwks_fetched_at = time.time()
    return _jwks_cache

def validate_token(token: str, jwks: dict) -> dict:
    unverified_header = jwt.get_unverified_header(token)
    key = next(k for k in jwks["keys"] if k["kid"] == unverified_header["kid"])
    claims = jwt.decode(token, key, algorithms=["RS256"], audience=client_id, issuer=issuer)
    return claims
```

**Alternatives considered**:
- `PyJWT`: Also viable but `python-jose` has better Cognito documentation
- `cognitojwt`: Specific to Cognito but unmaintained
- AWS SDK `verify_user_token`: Requires network call per validation

---

## 2. WebSocket Auth Pattern in FastAPI

**Decision**: Extract JWT from WebSocket URL query parameter (`?token=<jwt>`). Validate during the WebSocket upgrade handler before accepting the connection.

**Rationale**: WebSocket doesn't support custom headers in the browser `WebSocket` API. Query params are the standard approach for browser-initiated WebSocket auth.

**Implementation pattern**:
```python
from fastapi import WebSocket, WebSocketDisconnect

async def websocket_audio_endpoint(websocket: WebSocket):
    token = websocket.query_params.get("token")
    if not token:
        await websocket.close(code=4001, reason="Missing auth token")
        return
    try:
        claims = await validate_jwt(token)
    except AuthError:
        await websocket.close(code=4003, reason="Invalid token")
        return
    await websocket.accept()
    # ... proceed with authenticated session
```

**Alternatives considered**:
- Subprotocol header: Non-standard, poor browser support
- First message auth: Adds complexity, connection already established before auth check
- Cookie-based: Requires additional session management

---

## 3. WAF + ALB Integration via Terraform

**Decision**: Create `aws_wafv2_web_acl` with rate-limit and size-restriction rules, then associate with the ALB using `aws_wafv2_web_acl_association`.

**Rationale**: WAFv2 is the current AWS WAF standard. Associating at the ALB level means all traffic (REST + WebSocket upgrade) is evaluated.

**Implementation pattern**:
```hcl
resource "aws_wafv2_web_acl" "main" {
  name  = "${local.name}-waf"
  scope = "REGIONAL"
  default_action { allow {} }

  rule {
    name     = "rate-limit"
    priority = 1
    action { block {} }
    statement {
      rate_based_statement {
        limit              = 100
        aggregate_key_type = "IP"
      }
    }
    visibility_config { ... }
  }

  rule {
    name     = "size-limit"
    priority = 2
    action { block {} }
    statement {
      size_constraint_statement {
        field_to_match { body {} }
        comparison_operator = "GT"
        size                = 8192
      }
    }
    visibility_config { ... }
  }
}

resource "aws_wafv2_web_acl_association" "alb" {
  resource_arn = aws_lb.main.arn
  web_acl_arn  = aws_wafv2_web_acl.main.arn
}
```

**Alternatives considered**:
- CloudFront WAF (scope=CLOUDFRONT): Adds CDN layer — overkill for MVP
- API Gateway with usage plans: Not applicable — we use ALB directly
- No WAF (auth-only): Insufficient — authenticated users could still flood

---

## 4. Amplify v6 Auth Configuration

**Decision**: Use `@aws-amplify/auth` v6 with `Amplify.configure()` pointing to the Cognito user pool. Use Amplify's `signIn`, `signUp`, `confirmSignUp`, `resetPassword` APIs directly (no hosted UI).

**Rationale**: Amplify v6 is modular (tree-shakeable), so we only import auth. Custom forms give us full UI control matching the existing design system. Cognito hosted UI would require redirects and break the SPA flow.

**Implementation pattern**:
```typescript
import { Amplify } from 'aws-amplify';
import { signIn, signUp, confirmSignUp, fetchAuthSession } from '@aws-amplify/auth';

Amplify.configure({
  Auth: {
    Cognito: {
      userPoolId: config.COGNITO_USER_POOL_ID,
      userPoolClientId: config.COGNITO_CLIENT_ID,
    },
  },
});

// Get token for API calls
const session = await fetchAuthSession();
const token = session.tokens?.accessToken?.toString();
```

**Alternatives considered**:
- Cognito hosted UI: Requires redirect, loses SPA state, hard to style
- `amazon-cognito-identity-js`: Lower-level, more code, same result
- Custom SRP implementation: Way too complex for no benefit
