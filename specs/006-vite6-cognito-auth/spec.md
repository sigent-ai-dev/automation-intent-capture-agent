# Feature Specification: Vite 6 Upgrade and Cognito Authentication

**Feature Branch**: `006-vite6-cognito-auth`

**Created**: 2026-05-28

**Status**: Draft

**Input**: Upgrade frontend build tooling from Vite 5 to Vite 6, and add AWS Cognito-based user authentication to the browser frontend so that only authenticated users can access the voice intent capture interface.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Authenticated User Accesses Voice Interface (Priority: P1)

A returning user opens the intent capture application in their browser. They are presented with a login screen where they enter their email and password. After successful authentication, they are taken to the voice interface where they can start a WebSocket session and interact with the intent capture agent. Their identity token is attached to the connection so the backend knows who they are.

**Why this priority**: Without authentication, the application is open to anyone. This is the core security gate that must exist before any other auth-related feature matters.

**Independent Test**: Can be fully tested by creating a Cognito user, logging in via the form, and verifying the voice interface becomes accessible with a valid token attached to the WebSocket.

**Acceptance Scenarios**:

1. **Given** an unauthenticated user visits the app, **When** the page loads, **Then** they see a login form (not the voice interface)
2. **Given** a user with valid credentials, **When** they submit the login form, **Then** they are authenticated and redirected to the voice interface
3. **Given** an authenticated user, **When** they initiate a WebSocket connection, **Then** their identity token is included in the Sec-WebSocket-Protocol header
4. **Given** an authenticated user, **When** their session expires, **Then** they are redirected back to the login screen

---

### User Story 2 - User Signs Out (Priority: P2)

An authenticated user wants to end their session. They click a sign-out button, which terminates their Cognito session, closes any active WebSocket connections, and returns them to the login screen.

**Why this priority**: Session termination is a fundamental security requirement that pairs with login functionality.

**Independent Test**: Can be tested by logging in, verifying the voice interface is visible, clicking sign out, and confirming the login form reappears and WebSocket is disconnected.

**Acceptance Scenarios**:

1. **Given** an authenticated user on the voice interface, **When** they click "Sign out", **Then** their session is terminated and the login screen is displayed
2. **Given** a user who has signed out, **When** they try to reconnect the WebSocket, **Then** the connection is rejected until they re-authenticate

---

### User Story 3 - Build Tooling Upgrade (Priority: P1)

A developer working on the frontend runs the dev server, builds for production, or executes tests. All existing functionality continues to work identically after the Vite 5-to-6 upgrade. No user-facing behavior changes.

**Why this priority**: The Vite upgrade is a prerequisite for modern tooling compatibility and must not break existing functionality. It is foundational work that unblocks other improvements.

**Independent Test**: Can be tested by running `npm run dev`, `npm run build`, and `npm test` and verifying all pass without errors and the application functions as before.

**Acceptance Scenarios**:

1. **Given** the upgraded frontend, **When** a developer runs the dev server, **Then** it starts without errors and serves the application
2. **Given** the upgraded frontend, **When** a developer runs the test suite, **Then** all existing tests pass
3. **Given** the upgraded frontend, **When** a production build is created, **Then** it completes without errors and produces valid output

---

### User Story 4 - New Password Challenge (Priority: P3)

A newly created user logs in for the first time and is required to set a new password (admin-created accounts in Cognito). They see a "Set New Password" form, enter their new password, and upon success are taken to the voice interface.

**Why this priority**: This is a standard Cognito flow for admin-provisioned users. Important for onboarding but not critical for the core authentication loop.

**Independent Test**: Can be tested by creating a user via admin API (which forces password change), logging in, and verifying the new-password form appears and works.

**Acceptance Scenarios**:

1. **Given** a user whose account requires a password change, **When** they log in with temporary credentials, **Then** they see a "Set New Password" form
2. **Given** the new-password form is displayed, **When** the user submits a valid new password, **Then** they are authenticated and taken to the voice interface

---

### User Story 5 - Federated Sign-In (Priority: P2)

A user whose organization uses an external identity provider (Microsoft, Okta, or Google) clicks the corresponding "Sign in with..." button on the login form. They are redirected to their provider's login page, authenticate there, and are redirected back to the application fully authenticated. The experience is seamless — they land on the voice interface with a valid session.

**Why this priority**: Enterprise users expect SSO-style login via their corporate identity provider. This is critical for adoption in organizations that mandate federated authentication.

**Independent Test**: Can be tested by configuring a federated provider in Cognito, clicking the provider button, completing external auth, and verifying the redirect back lands on the voice interface with a valid token.

**Acceptance Scenarios**:

1. **Given** a user on the login screen, **When** they click "Sign in with Microsoft" (or Okta/Google), **Then** they are redirected to that provider's authentication page
2. **Given** a user has authenticated with the external provider, **When** the provider redirects back to the app, **Then** the user is authenticated and sees the voice interface
3. **Given** federation is disabled via configuration, **When** the login screen loads, **Then** the federated provider buttons are not shown
4. **Given** a federated sign-in fails (provider error or misconfiguration), **When** the redirect returns, **Then** the user sees a clear error message on the login screen

---

### User Story 6 - Role-Based Access Control (Priority: P3)

An administrator assigns users to Cognito groups (e.g., "admin", "user") to control what they can access. The "admin" group guards a future admin panel — for now, only the route guard mechanism is implemented (no admin UI exists yet). Users without the required group membership are shown an appropriate message when attempting to access restricted areas.

**Why this priority**: Role-based access enables multi-tenant use and administrative separation. It builds on top of basic auth and federation.

**Independent Test**: Can be tested by creating users in different Cognito groups, logging in as each, and verifying that group-restricted UI elements appear/disappear based on membership.

**Acceptance Scenarios**:

1. **Given** a user belongs to the "admin" group, **When** they log in, **Then** they can see and access admin-restricted features
2. **Given** a user does not belong to a required group, **When** they navigate to a restricted area, **Then** they see an "Access Denied" message
3. **Given** a user's group membership changes, **When** they next refresh their session, **Then** the updated permissions take effect

---

### Edge Cases

- What happens when a user enters invalid credentials? They see a clear error message and can retry. After repeated failures, Cognito's built-in throttling locks the account and the frontend displays a lockout message.
- What happens when the Cognito service is unreachable? The login form shows a connectivity error without exposing internal details.
- What happens if the token expires mid-session? The WebSocket connection is closed and the user is redirected to re-authenticate.
- What happens if environment variables for Cognito are not configured? The app starts in a degraded state with a clear developer-facing error in the console.
- What happens if a federated provider is misconfigured? The redirect fails gracefully and the user is returned to the login form with an error.
- What happens if a user is removed from a Cognito group while actively using the app? On next token refresh, their access is downgraded.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: System MUST present a login form to unauthenticated users before granting access to the voice interface
- **FR-002**: System MUST authenticate users via email/password using the SRP auth flow against a Cognito user pool
- **FR-003**: System MUST handle the "new password required" challenge for admin-created user accounts
- **FR-004**: System MUST attach the authenticated user's identity token to WebSocket connections via the Sec-WebSocket-Protocol header
- **FR-005**: System MUST provide a sign-out mechanism that terminates the Cognito session and redirects to login
- **FR-006**: System MUST persist authentication state across page refreshes (using Cognito session tokens)
- **FR-007**: System MUST redirect users to the login screen when their session expires or token becomes invalid
- **FR-008**: System MUST display user-friendly error messages for authentication failures (invalid credentials, network errors, service unavailable, account lockout)
- **FR-009**: Frontend build tooling MUST be upgraded from Vite 5 to Vite 6 without breaking existing functionality
- **FR-010**: All existing unit tests and E2E tests MUST continue to pass after the tooling upgrade
- **FR-011**: CI pipeline MUST build, type-check, and test the frontend with the upgraded tooling
- **FR-012**: Infrastructure MUST provision a Cognito user pool and SPA client for the application
- **FR-013**: System MUST support federated sign-in via external identity providers (Microsoft, Okta, Google) using OAuth2/OIDC redirect flow
- **FR-014**: Federated sign-in buttons MUST be togglable via a configuration flag so they can be shown or hidden per environment
- **FR-015**: System MUST extract user group memberships from the Cognito ID token on authentication
- **FR-016**: System MUST provide a route guard mechanism that restricts access to UI areas based on Cognito group membership
- **FR-017**: Infrastructure MUST provision Cognito user groups for role-based access control
- **FR-018**: System MUST fall back to Cognito hosted UI redirect when the primary federated sign-in mechanism is unavailable

### Key Entities

- **User**: An authenticated person using the intent capture interface. Key attributes: email (username), authentication state, session tokens, group memberships.
- **Session**: A Cognito authentication session consisting of ID token, access token, and refresh token. Used to maintain authenticated state and authorize WebSocket connections.
- **User Pool**: The Cognito identity store containing user accounts, password policies, and client configurations for this application.
- **User Group**: A Cognito group (e.g., "admin", "user") that defines a user's role. Group memberships are embedded in the ID token and used for frontend access control.
- **Identity Provider**: An external OIDC-compatible authentication provider (Microsoft, Okta, Google) configured as a federated identity source in the Cognito user pool.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Users can complete login and reach the voice interface in under 5 seconds
- **SC-002**: Unauthenticated access to the voice interface is blocked 100% of the time
- **SC-003**: All existing frontend tests pass after the Vite upgrade with zero modifications to test logic
- **SC-004**: Frontend production build completes in under 30 seconds
- **SC-005**: Authentication-related unit tests cover happy path and error path for all auth flows (login, logout, getToken, isAuthenticated, completeNewPassword, federatedSignIn)
- **SC-006**: Session refresh works transparently — users are not forced to re-login during active use within the token validity period
- **SC-007**: Federated sign-in completes the full redirect cycle (app → provider → app) in under 10 seconds
- **SC-008**: Role-restricted areas correctly deny access within 1 second of navigation attempt by unauthorized users

## Clarifications

### Session 2026-05-28

- Q: What does the "admin" role unlock in the current application? → A: Admin guards a future admin panel; for now only the guard mechanism is implemented (no admin UI yet).
- Q: How should the auth token be passed to the WebSocket connection? → A: Token in Sec-WebSocket-Protocol header (browser-supported, no URL exposure).
- Q: How should failed login attempts be handled for security observability? → A: Rely on Cognito's built-in throttling and account lockout; frontend surfaces lockout message to user.

## Assumptions

- Users have modern browsers that support the Web Crypto API (required for SRP auth)
- The backend will validate tokens independently — this spec covers only the frontend auth flow and token attachment to WebSocket
- Email is used as the primary username attribute in Cognito
- The Cognito user pool will be provisioned via Terraform in the existing infrastructure directory
- The existing WebSocket protocol remains unchanged; the token is passed via the Sec-WebSocket-Protocol header to avoid URL leakage
- Federated providers are configured at the infrastructure level (Terraform) and toggled in the frontend via environment variable
- The initial group structure mirrors specter: admin and user roles, with the ability to add more granular groups later
- Cognito hosted UI domain is used as the fallback for federated redirect when the Amplify SDK redirect is unavailable
