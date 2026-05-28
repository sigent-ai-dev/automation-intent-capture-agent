# Implementation Plan: Cognito + WAF Authentication

**Branch**: `10-auth-cognito-waf` | **Date**: 2026-05-27 | **Spec**: [spec.md](./spec.md)

**Input**: Feature specification from `specs/010-auth-cognito-waf/spec.md`

## Summary

Add authentication (Cognito) and edge protection (WAF) to the voice agent. Cognito user pool handles sign-up/sign-in/password-reset. Frontend uses AWS Amplify for auth flows. Backend validates JWT on WebSocket connections. WAF rate-limits and size-limits requests at the ALB layer. All infrastructure defined in Terraform.

## Technical Context

**Language/Version**: Python 3.11 (backend JWT validation), TypeScript 5.3 (frontend Amplify integration), HCL (Terraform)

**Primary Dependencies**: `python-jose[cryptography]` (JWT validation), `@aws-amplify/auth` v6 (frontend), Terraform AWS provider

**Storage**: Cognito user pool (managed by AWS — no application-level storage)

**Testing**: pytest (backend middleware tests), Vitest (frontend auth context tests), Playwright (E2E login flow)

**Target Platform**: ECS Fargate (backend), Browser (frontend), AWS (infrastructure)

**Project Type**: Full-stack feature (infra + backend + frontend)

**Performance Goals**: Sign-in < 3s, token refresh invisible to user, WAF evaluation < 5ms added latency

**Constraints**: No SSO/SAML (out of scope), LOCAL_MODE bypasses auth, WebSocket validates at connection time only

**Scale/Scope**: 500 concurrent authenticated users, single Cognito user pool

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principle | Status | Evidence |
|-----------|--------|----------|
| I. Meet Them Where They Are | ✓ PASS | Cognito hosted UI or Amplify components — users sign in via browser, no extra tools |
| II. Propose, Don't Interrogate | N/A | Auth doesn't affect elicitation flow |
| III. Structured Output | N/A | Auth doesn't affect output format |
| IV. Multi-Source Convergence | N/A | Auth is channel-agnostic identity |
| V. Channel-Agnostic Core | ✓ PASS | JWT validation in backend middleware — same for any channel that sends a token |
| VI. Graceful Degradation | ✓ PASS | LOCAL_MODE bypasses auth; token refresh is silent; expired session prompts re-auth gracefully |

| Quality Standard | Status | Evidence |
|-----------------|--------|----------|
| API responses <200ms | ✓ PASS | JWT validation is local (no network call after initial JWKS fetch) |
| Sessions survive reconnection | ✓ PASS | Token refresh handles this; session ID unchanged after reconnect |

**Gate result**: PASS — no violations.

## Project Structure

### Documentation (this feature)

```text
specs/010-auth-cognito-waf/
├── spec.md
├── plan.md              ← this file
├── research.md
├── data-model.md
├── checklists/
│   └── requirements.md
└── contracts/
    └── auth-middleware.md
```

### Implementation

```text
# Backend (JWT validation middleware)
src/voice_server/auth/
├── __init__.py
├── middleware.py        ← FastAPI dependency for JWT validation
├── jwks.py             ← JWKS key fetcher + cache
└── config.py           ← Auth-specific settings (pool ID, client ID, region)

# Frontend (Amplify auth integration)
frontend/src/
├── contexts/AuthContext.tsx     ← Auth state + methods
├── components/auth/
│   ├── LoginForm.tsx            ← Sign-in UI
│   ├── SignUpForm.tsx           ← Registration UI
│   └── ProtectedRoute.tsx      ← Wrapper that redirects to login
├── services/authService.ts     ← Amplify auth wrapper
└── config/amplify.ts           ← Amplify configuration

# Infrastructure (Terraform)
terraform/modules/auth/
├── cognito.tf          ← User pool, client, domain
├── waf.tf              ← WebACL, rate limit rule, size rule
├── outputs.tf
└── variables.tf
```

---

## Phase 0: Research

### Research Tasks

1. **Cognito JWT validation in FastAPI** — How to validate Cognito JWTs in Python without calling Cognito on every request (JWKS caching pattern)
2. **WebSocket auth pattern** — How to validate JWT during WebSocket upgrade (FastAPI WebSocket dependencies)
3. **WAF + ALB integration** — How to attach WAF WebACL to existing ALB via Terraform
4. **Amplify v6 auth** — Correct configuration pattern for Amplify Auth v6 with Cognito user pools

---

## Phase 1: Design & Contracts

### Data Model

| Entity | Fields | Notes |
|--------|--------|-------|
| CognitoUser | email, sub (UUID), email_verified, created_at | Managed by Cognito, not in our DB |
| JWTClaims | sub, email, token_use, exp, iss, aud | Extracted from validated access token |
| WAFRuleGroup | rate_limit (100/min), size_limit (8KB) | Configured in Terraform |

### Interface Contracts

**Auth Middleware Contract** (see `contracts/auth-middleware.md`):
- FastAPI dependency that extracts + validates JWT from WebSocket query param or Authorization header
- Returns `JWTClaims` dataclass on success, raises `HTTPException(401)` on failure
- JWKS keys cached for 1 hour

---

## Phase 2: Implementation Phases

### Phase 2A — Terraform: Cognito + WAF
- Cognito user pool with email verification + password policy
- Cognito app client (with secret = false for SPA)
- Cognito domain for hosted UI
- WAF WebACL with rate-limit rule (100/min/IP) + size rule (8KB)
- WAF association with existing ALB
- Outputs: user_pool_id, client_id, cognito_domain, waf_acl_arn

### Phase 2B — Backend: JWT Validation Middleware
- `jwks.py`: Fetch and cache JWKS from Cognito well-known endpoint
- `middleware.py`: FastAPI dependency `get_current_user()` — validates Bearer token or `?token=` query param
- `config.py`: Auth settings (COGNITO_USER_POOL_ID, COGNITO_CLIENT_ID, COGNITO_REGION)
- Wire middleware into WebSocket handler (validate on upgrade)
- Wire middleware into REST endpoints (session create/get/delete)
- LOCAL_MODE bypass: skip validation when `LOCAL_MODE=true`

### Phase 2C — Frontend: Amplify Auth Integration
- `config/amplify.ts`: Amplify.configure() with Cognito pool settings
- `contexts/AuthContext.tsx`: isAuthenticated, user, signIn, signUp, signOut, resetPassword
- `components/auth/LoginForm.tsx`: Email/password form with error handling
- `components/auth/SignUpForm.tsx`: Registration + verification code flow
- `components/auth/ProtectedRoute.tsx`: Wraps App content, redirects to login if not authed
- Update `websocketService.ts`: Include JWT in WebSocket URL query param
- Update `sessionService.ts`: Include Authorization header in REST calls

### Phase 2D — Testing & Integration
- Backend unit tests: JWT validation (valid/expired/malformed/missing)
- Frontend tests: AuthContext state transitions, LoginForm interaction
- E2E: Full login → start session → verify token in WebSocket
- Verify WAF blocks excessive requests (integration test against deployed infra)

---

## Risk Register

| Risk | Impact | Mitigation |
|------|--------|------------|
| JWKS fetch fails on cold start | Medium | Cache with fallback; retry with exponential backoff |
| Token refresh race condition (multiple tabs) | Low | Amplify handles this internally with locking |
| WAF false positives on legitimate users | Medium | Set rate limit high enough (100/min); monitor and adjust |
| Cognito hosted UI styling doesn't match brand | Low | Acceptable for MVP; can customize CSS or switch to Amplify components |
| LOCAL_MODE bypass accidentally enabled in prod | High | Environment variable not set in ECS task definition; add startup log warning |
