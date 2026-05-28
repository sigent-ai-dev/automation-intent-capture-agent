# Research: Vite 6 Upgrade and Cognito Authentication

**Date**: 2026-05-28 | **Feature**: 006-vite6-cognito-auth

## R1: Vite 5 → 6 Migration

**Decision**: Upgrade to Vite 6.x with vitest 2.x and @vitejs/plugin-react 4.3.x

**Rationale**: Vite 6 is the current stable release. The specter project already uses this stack successfully. Key breaking changes in Vite 6:
- Default dev server now uses `localhost` instead of `127.0.0.1`
- `resolve.conditions` default changed
- JSON stringify now uses `namedExports` by default
- `css.preprocessorOptions` API changed for some preprocessors
- None of these affect our current vite.config.ts (simple React + proxy setup)

**Alternatives considered**:
- Stay on Vite 5: Rejected — falling behind specter, missing security patches
- Jump to Vite 7 (if available): Not stable; 6.x is the proven target

**Migration steps**:
1. Bump `vite`, `vitest`, `@vitejs/plugin-react`, `@testing-library/react` in package.json
2. Run `npm install` and verify `npm run dev` starts
3. Run `npm test` and fix any vitest 2.x breaking changes (minimal — mostly config)
4. Run `npm run build` and verify output

## R2: AWS Amplify v6 Authentication Pattern

**Decision**: Use `aws-amplify` v6 with modular imports (`aws-amplify/auth`) for Cognito SRP authentication

**Rationale**: Amplify v6 is tree-shakeable, supports modular auth imports, and is the pattern proven in specter. It handles:
- SRP auth flow (no password leaves the browser)
- Token management (automatic refresh)
- Session persistence (localStorage by default)
- Federated sign-in via `signInWithRedirect`

**Alternatives considered**:
- amazon-cognito-identity-js: Lower-level, more boilerplate, no federation support built-in
- Custom OAuth2 implementation: Too much code for well-solved problem
- AWS SDK CognitoIdentityProvider: Server-side SDK, not appropriate for browser

## R3: Token Delivery to WebSocket

**Decision**: Pass Cognito ID token via `Sec-WebSocket-Protocol` header

**Rationale**: Clarified during spec session. The browser WebSocket API supports passing subprotocols via the second argument to `new WebSocket(url, protocols)`. The token is passed as a protocol value. The server echoes it back in the response header to complete the handshake. This avoids:
- URL query parameter leakage (logs, referrer, browser history)
- Cookie-based auth complexity (CORS, SameSite issues)

**Implementation pattern**:
```
// Client
const ws = new WebSocket(url, ['v1.audio.intent', token]);

// Server (FastAPI/Uvicorn)
// Extract token from Sec-WebSocket-Protocol, validate, echo accepted protocol
```

**Alternatives considered**:
- Query parameter (`?token=...`): Rejected — URL leakage risk
- First message auth: Rejected — adds protocol complexity, delays codec negotiation
- Cookie-based: Rejected — CORS complications with WebSocket

## R4: Federated Identity Provider Integration

**Decision**: Use Amplify `signInWithRedirect` with Cognito hosted UI fallback

**Rationale**: Specter's pattern handles the primary flow (Amplify redirect) with a fallback to direct Cognito hosted UI URL construction. This covers edge cases where Amplify's redirect mechanism fails silently.

**Provider configuration**:
- Providers configured in Terraform as Cognito identity providers
- Frontend only needs provider key names (e.g., "Microsoft", "Okta", "Google")
- Toggle via `VITE_ENABLE_FEDERATION` env var
- Hosted UI domain constructed from `VITE_COGNITO_DOMAIN`

**Alternatives considered**:
- Direct OIDC implementation per provider: Too much code, Cognito handles this
- Auth0/Okta SDK: External dependency, Cognito already provides federation layer

## R5: Role-Based Access Control (Cognito Groups)

**Decision**: Extract `cognito:groups` claim from ID token, implement RoleGuard component

**Rationale**: Cognito embeds group membership in the ID token payload. No additional API call needed. The frontend reads groups from the token and conditionally renders/guards routes.

**Initial group structure**:
- `admin` — guards future admin panel (no admin UI yet, just the mechanism)
- `user` — default group for all authenticated users (implicit if no group)

**Implementation**:
- `RoleGuard` component wraps protected routes
- Checks if user's groups intersect with required groups
- Shows "Access Denied" if no match
- Groups refreshed on session refresh (token includes latest groups)

**Alternatives considered**:
- Backend-enforced RBAC only: Insufficient — frontend needs to know what to render
- Custom attributes instead of groups: Groups are the Cognito-native RBAC mechanism

## R6: Cognito Terraform Module

**Decision**: New `terraform/modules/cognito/` module alongside existing `voice-service`

**Rationale**: Keeps infrastructure modular. The cognito module provisions:
- User pool (email username, password policy)
- User pool domain (for hosted UI / federation)
- SPA client (no secret, SRP + refresh flows)
- User groups (admin, user)
- Optional: identity provider configurations for federation

**Reference**: `specter/terraform/modules/mcp-proxy/cognito.tf` provides the proven pattern.

**Alternatives considered**:
- Inline in main.tf: Rejected — module keeps cognito concerns isolated
- Add to voice-service module: Rejected — cognito is cross-cutting, not voice-specific
