# Feature Specification: Cognito + WAF Authentication

**Feature Branch**: `10-auth-cognito-waf`

**Created**: 2026-05-27

**Status**: Draft

**Input**: User description: "Cognito + WAF authentication for the voice agent. Cognito user pool, browser frontend auth via Amplify, JWT-secured WebSocket, WAF rate limiting. Terraform module for all resources. See issue #10."

## User Scenarios & Testing

### User Story 1 — Authenticated Session Start (Priority: P1)

A user opens the browser frontend and is prompted to sign in before starting a capture session. After signing in with email and password, they can start sessions as normal. Their identity is attached to the session.

**Why this priority**: Without authentication, the service is open to the internet. This is the core gate that makes everything else secure.

**Independent Test**: Can be tested by opening the frontend in an unauthenticated browser — user sees login form, signs in, then the "Start Capture" button becomes available.

**Acceptance Scenarios**:

1. **Given** an unauthenticated user, **When** they open the frontend, **Then** they see a login form (not the Start Capture view)
2. **Given** a user with valid credentials, **When** they sign in, **Then** they are redirected to the main capture UI with their session token stored
3. **Given** a signed-in user, **When** they click Start Capture, **Then** the WebSocket connection includes their JWT and the session is created with their user ID
4. **Given** a user with an expired token, **When** they attempt any action, **Then** the token is silently refreshed via Cognito refresh token flow

---

### User Story 2 — WebSocket JWT Validation (Priority: P1)

The WebSocket endpoint rejects connections without a valid JWT. Only authenticated users can establish a voice session.

**Why this priority**: The WebSocket carries real-time audio data — it must be secured to prevent unauthorized access or resource abuse.

**Independent Test**: Attempt a WebSocket connection without a token → connection rejected with 401. Attempt with a valid JWT → connection accepted.

**Acceptance Scenarios**:

1. **Given** a WebSocket connection attempt without a token, **When** the server processes it, **Then** the connection is rejected with a 401/403 response
2. **Given** a valid JWT in the WebSocket connection, **When** the server validates it, **Then** the connection is accepted and the user ID is extracted from the token
3. **Given** a WebSocket connection with an expired JWT, **When** the server validates it, **Then** the connection is rejected and the frontend triggers a token refresh
4. **Given** a JWT signed by an unknown issuer, **When** the server validates it, **Then** the connection is rejected

---

### User Story 3 — WAF Rate Limiting & Protection (Priority: P2)

AWS WAF sits in front of the ALB to protect against abuse: rate limiting per IP, request size limits, and optional geo-blocking. Legitimate users are unaffected.

**Why this priority**: Defence-in-depth. Authentication alone doesn't prevent a compromised account from flooding the service. WAF adds the infrastructure-level protection layer.

**Independent Test**: Send 200 requests in 10 seconds from a single IP → WAF blocks further requests. Send normal traffic → unaffected.

**Acceptance Scenarios**:

1. **Given** a single IP sending more than 100 requests per minute, **When** WAF evaluates the traffic, **Then** subsequent requests are blocked for a cooldown period
2. **Given** a request larger than 8KB (excluding WebSocket audio frames), **When** WAF evaluates it, **Then** the request is rejected
3. **Given** normal user traffic (< 20 requests/min), **When** WAF evaluates it, **Then** all requests pass through without delay
4. **Given** WAF blocks a request, **When** the user sees the response, **Then** they receive a clear "Too many requests, please wait" message

---

### User Story 4 — User Registration & Password Management (Priority: P3)

New users can self-register with email verification. Existing users can reset their password. All flows use Amplify custom components (matching the existing design system).

**Why this priority**: Secondary to the core auth flow — initial deployment may use admin-created accounts. Self-service registration adds convenience.

**Independent Test**: Register with a new email → receive verification code → confirm → can sign in.

**Acceptance Scenarios**:

1. **Given** a new user, **When** they sign up with email and password, **Then** they receive a verification email and must confirm before accessing the service
2. **Given** a user who forgot their password, **When** they initiate a password reset, **Then** they receive a reset code and can set a new password
3. **Given** a password that doesn't meet complexity requirements, **When** submitted, **Then** the user sees a clear error explaining the requirements

---

### Edge Cases

- What happens when the Cognito service is temporarily unavailable? → Frontend shows "Authentication service unavailable, please try again" error banner
- What happens when a user's session token expires mid-voice-capture? → Token refresh happens in background; if refresh fails, session continues until next REST call fails, then user is prompted to re-authenticate
- What happens when WAF blocks a legitimate user (false positive)? → User sees a rate-limit error with retry guidance; logs capture the block for investigation
- What happens when the same user opens multiple tabs? → Each tab authenticates independently; multiple concurrent sessions are allowed

## Requirements

### Functional Requirements

- **FR-001**: System MUST require authentication before any capture session can be created
- **FR-002**: System MUST validate JWT tokens on every WebSocket connection attempt
- **FR-003**: System MUST reject WebSocket connections with missing, expired, or invalid tokens
- **FR-004**: System MUST extract user identity from the JWT and associate it with the session
- **FR-005**: Frontend MUST redirect unauthenticated users to a sign-in form
- **FR-006**: Frontend MUST store tokens securely and handle silent refresh
- **FR-007**: System MUST enforce rate limits (100 requests/minute per IP) via WAF
- **FR-008**: System MUST limit non-WebSocket request body size to 8KB via WAF
- **FR-009**: System MUST support user registration with email verification
- **FR-010**: System MUST support password reset via email
- **FR-011**: System MUST enforce password complexity (minimum 8 characters, mixed case, number)
- **FR-012**: Infrastructure MUST be defined as Terraform modules (Cognito user pool, WAF WebACL)

### Key Entities

- **User**: Email (unique identifier), password (hashed by Cognito), verification status, created_at
- **Token**: Access token (JWT, short-lived ~1hr), refresh token (long-lived ~30 days), ID token (user claims)
- **WAF Rule**: Rate limit rule, size restriction rule, optional geo-block rule
- **User Pool**: Container for all voice agent users, password policy, verification settings

## Success Criteria

### Measurable Outcomes

- **SC-001**: Unauthenticated users cannot access any capture functionality (0% bypass rate)
- **SC-002**: Valid users can sign in and start a session in under 10 seconds
- **SC-003**: Token refresh completes without user-visible interruption in 95% of cases
- **SC-004**: WAF blocks abusive traffic (>100 req/min) within 5 seconds of threshold breach
- **SC-005**: System handles 500 concurrent authenticated users without auth-related errors
- **SC-006**: New user registration and verification completes in under 3 minutes

## Assumptions

- Users have email addresses and can receive verification emails
- Initial deployment uses email/password auth only (no SSO/SAML — explicitly out of scope per issue #10)
- The ALB already exists (from issue #6 Terraform) — WAF attaches to it
- Amplify custom forms used (not Cognito hosted UI) to maintain design system consistency
- All authenticated users have equal permissions (no role-based access)
- WebSocket token validation happens at connection time only (not per-message)
- The `LOCAL_MODE=true` flag bypasses auth for local development
