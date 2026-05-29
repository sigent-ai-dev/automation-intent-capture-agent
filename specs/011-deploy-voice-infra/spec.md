# Feature Specification: Deploy Voice Service Infrastructure

**Feature Branch**: `011-deploy-voice-infra`

**Created**: 2026-05-29

**Status**: Draft

**Input**: Deploy the voice server backend to the builder-admin AWS account so the authenticated frontend can connect to a live backend. Provision networking, container hosting, session storage, and CI/CD deployment pipeline. Fix the backend authentication to accept tokens from the frontend via the Sec-WebSocket-Protocol header. Add smoke tests to verify the deployed service is reachable and functional.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Frontend Connects to Deployed Backend (Priority: P1)

A user opens the intent capture frontend, logs in via Cognito, and starts a voice session. The frontend connects to the deployed backend (not localhost). The WebSocket connection upgrades successfully with the user's auth token, codec negotiation completes, and the voice interface becomes active.

**Why this priority**: Without a deployed backend, the frontend auth work is unusable beyond local development. This is the critical path to a working end-to-end system.

**Independent Test**: Navigate to the frontend, log in, click Start Capture, and verify the WebSocket connects to the deployed service with a valid session.

**Acceptance Scenarios**:

1. **Given** a deployed backend, **When** the frontend initiates a WebSocket connection with a valid Cognito token, **Then** the connection is accepted and codec negotiation completes
2. **Given** a deployed backend, **When** a user without a valid token attempts to connect, **Then** the connection is rejected with an appropriate error code
3. **Given** the backend is running, **When** a health check is performed, **Then** it returns a healthy status

---

### User Story 2 - Developer Deploys New Version (Priority: P2)

A developer merges code to main or triggers the deploy workflow. The CI/CD pipeline builds a container image, pushes it to the registry, and updates the running service. The new version becomes healthy within minutes without manual intervention.

**Why this priority**: Continuous deployment enables rapid iteration. Without it, every change requires manual steps.

**Independent Test**: Trigger the deploy workflow, wait for completion, and verify the health endpoint returns the new version.

**Acceptance Scenarios**:

1. **Given** a code change is merged, **When** the deploy workflow runs, **Then** the new container image is built and deployed
2. **Given** a deployment is in progress, **When** the new version fails health checks, **Then** the service rolls back to the previous version
3. **Given** a successful deployment, **When** the service is checked, **Then** it is serving traffic within 5 minutes of trigger

---

### User Story 3 - Backend Validates WebSocket Auth Token (Priority: P1)

The backend receives a WebSocket upgrade request containing the Cognito ID token in the Sec-WebSocket-Protocol header. It extracts the token (second value after `v1.audio.intent`), validates it against the Cognito user pool's JWKS endpoint, and accepts or rejects the connection accordingly.

**Why this priority**: The frontend already sends the token via Sec-WebSocket-Protocol. The backend must match this contract for end-to-end auth to work.

**Independent Test**: Send a WebSocket upgrade with a valid token in Sec-WebSocket-Protocol — verify acceptance. Send one with an invalid/missing token — verify rejection.

**Acceptance Scenarios**:

1. **Given** a WebSocket upgrade with a valid Cognito ID token in Sec-WebSocket-Protocol, **When** the backend processes it, **Then** it validates the JWT, accepts the connection, and echoes `v1.audio.intent` as the selected protocol
2. **Given** a WebSocket upgrade with an expired or invalid token, **When** the backend processes it, **Then** it rejects the connection with code 4001
3. **Given** a WebSocket upgrade with no token, **When** the backend processes it, **Then** it rejects the connection with code 4001

---

### User Story 4 - Smoke Tests Verify Deployment (Priority: P2)

After each deployment, automated smoke tests run to verify the service is reachable and functional. These tests confirm health endpoints respond, WebSocket connections can be established with valid auth, and codec negotiation works end-to-end.

**Why this priority**: Automated verification catches deployment failures before users are affected.

**Independent Test**: Run the smoke test suite against the deployed URL and verify all checks pass.

**Acceptance Scenarios**:

1. **Given** a deployed service, **When** smoke tests run, **Then** health endpoints return expected responses
2. **Given** a deployed service, **When** smoke tests attempt WebSocket connection with a test token, **Then** codec negotiation completes successfully
3. **Given** a deployed service, **When** smoke tests attempt connection without auth, **Then** the connection is properly rejected

---

### Edge Cases

- What happens if the container crashes? The orchestration service restarts it automatically and health checks gate traffic.
- What happens if the JWKS endpoint is unreachable? The backend caches JWKS keys and retries; connections are rejected only if no cached keys exist.
- What happens if the deploy workflow fails mid-rollout? The service remains on the previous version (rolling deployment pattern).
- What happens if the networking has no egress? The backend cannot reach Cognito JWKS or Bedrock — health checks should report degraded state.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: Infrastructure MUST provision a network environment with public and private subnets across at least 2 availability zones
- **FR-002**: Infrastructure MUST provision a container registry for storing backend images
- **FR-003**: Infrastructure MUST provision a container orchestration service running the voice server on port 8080
- **FR-004**: Infrastructure MUST provision a load balancer with health checks on `GET /health/live`
- **FR-005**: Infrastructure MUST provision a session storage table for persisting voice session state
- **FR-006**: The CI/CD pipeline MUST build, push, and deploy container images on workflow trigger
- **FR-007**: The backend MUST extract the Cognito ID token from the Sec-WebSocket-Protocol header (second protocol value after `v1.audio.intent`)
- **FR-008**: The backend MUST validate the JWT against the Cognito user pool's signing keys
- **FR-009**: The backend MUST echo `v1.audio.intent` as the accepted protocol on successful auth
- **FR-010**: The backend MUST reject WebSocket connections with invalid or missing tokens (close code 4001)
- **FR-011**: Smoke tests MUST verify health endpoint availability after deployment
- **FR-012**: Smoke tests MUST verify WebSocket auth acceptance and rejection
- **FR-013**: Smoke tests MUST verify codec negotiation completes successfully
- **FR-014**: The container MUST have permission to access the session storage table and the AI model service
- **FR-015**: The load balancer MUST support WebSocket connections with sticky sessions

### Key Entities

- **Container Image**: A versioned build artifact containing the voice server application, stored in a registry.
- **Service**: A running instance (or set of instances) of the container, fronted by a load balancer and monitored by health checks.
- **Deployment**: The process of building a new image, pushing it, and updating the running service to use it.
- **JWKS Cache**: A cached copy of the Cognito user pool's JSON Web Key Set, used for offline JWT validation.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Health endpoint responds within 1 second from the public internet
- **SC-002**: WebSocket connections with valid auth tokens are accepted within 2 seconds
- **SC-003**: Invalid auth tokens are rejected within 500 milliseconds
- **SC-004**: New deployments complete and serve traffic within 5 minutes of trigger
- **SC-005**: Service maintains 99% availability in staging/prod (measured over a rolling 7-day window); dev is best-effort with no SLA
- **SC-006**: All smoke tests pass within 30 seconds of execution
- **SC-007**: Container restarts automatically within 60 seconds after an unexpected crash

## Clarifications

### Session 2026-05-29

- Q: Should the load balancer use HTTPS even for dev? → A: Self-signed HTTPS for dev; valid ACM certificates required for non-dev environments.
- Q: Should the 99% availability target apply to dev? → A: Best-effort for dev (no SLA); 99% availability target applies to staging/prod only.

## Assumptions

- The builder-admin AWS account (885659622434) is the target deployment environment
- HTTPS with a self-signed certificate is used for the dev load balancer; production/staging environments require valid ACM certificates
- The Cognito user pool (`eu-west-1_cnb1SWJC4`) is already provisioned in the same account
- A single container instance is sufficient for dev (no autoscaling required initially)
- The backend runs in `LOCAL_MODE=false` when deployed
- GitHub OIDC federation is used for CI/CD (no long-lived credentials)
- The existing deploy workflow (`.github/workflows/deploy.yml`) is the deployment mechanism
- Smoke tests run as a post-deploy step in the same workflow
