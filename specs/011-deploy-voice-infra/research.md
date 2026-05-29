# Research: Deploy Voice Service Infrastructure

**Date**: 2026-05-29 | **Feature**: 011-deploy-voice-infra

## R1: VPC Architecture for ECS Fargate

**Decision**: Create a dedicated VPC module with 2 AZ public/private subnet layout

**Rationale**: ECS Fargate tasks run in private subnets (no direct internet exposure). The ALB sits in public subnets. NAT Gateway provides egress for Cognito JWKS fetches and Bedrock API calls. Two AZs provide basic redundancy.

**Layout**:
- VPC CIDR: 10.0.0.0/16
- Public subnets: 10.0.1.0/24, 10.0.2.0/24 (AZ-a, AZ-b)
- Private subnets: 10.0.10.0/24, 10.0.11.0/24 (AZ-a, AZ-b)
- Single NAT Gateway (dev cost optimization — prod would use one per AZ)

**Alternatives considered**:
- Default VPC: Rejected — no private subnets, no isolation
- Shared VPC from another account: Rejected — adds cross-account complexity for a dev setup

## R2: Self-Signed HTTPS for Dev ALB

**Decision**: Generate a self-signed certificate and import to ACM for the dev ALB listener

**Rationale**: Per clarification, dev uses self-signed HTTPS to encrypt token transit. ALB requires a certificate in ACM even for self-signed. Browsers will show a warning but the connection is encrypted.

**Implementation**:
- Generate cert with `openssl req -x509 -nodes -days 365`
- Import to ACM via `aws acm import-certificate`
- Reference ARN in ALB HTTPS listener
- Document browser certificate exception in quickstart

**Alternatives considered**:
- HTTP only: Rejected — tokens in transit would be unencrypted
- Let's Encrypt: Requires a real domain name — overkill for dev
- AWS-issued ACM cert: Requires Route53 hosted zone or DNS validation — deferred to prod

## R3: Sec-WebSocket-Protocol Token Extraction

**Decision**: Modify `ws/auth.py` to parse the `Sec-WebSocket-Protocol` header for JWT extraction

**Rationale**: The frontend sends `new WebSocket(url, ['v1.audio.intent', token])`. The server receives this as a comma-separated `Sec-WebSocket-Protocol` header. The handler must:
1. Split the header by comma
2. First value = protocol identifier (`v1.audio.intent`)
3. Second value = Cognito ID token (JWT)
4. Validate JWT using existing `auth/middleware.py` logic
5. On success: accept connection with `Sec-WebSocket-Protocol: v1.audio.intent` response header

**FastAPI/Starlette integration**: FastAPI's `WebSocket` object exposes headers via `websocket.headers`. The accepted subprotocol is set via `websocket.accept(subprotocol='v1.audio.intent')`.

**Alternatives considered**:
- Query parameter `?token=`: Already implemented in middleware.py but rejected per spec (URL leakage)
- First message auth: Rejected — adds latency before codec negotiation
- Custom header: Rejected — browser WebSocket API doesn't support custom headers

## R4: GitHub OIDC for CI/CD

**Decision**: Create an IAM OIDC provider + deploy role in the builder-admin account

**Rationale**: GitHub Actions OIDC eliminates long-lived credentials. The deploy role needs:
- ECR push permissions
- ECS update-service
- Scoped to the specific repo (`sigent-ai-dev/automation-intent-capture-agent`)

**Resources**:
- `aws_iam_openid_connect_provider` for `token.actions.githubusercontent.com`
- `aws_iam_role` with trust policy restricting to repo + branch
- Policy: ECR push, ECS update-service, ECS describe

**Alternatives considered**:
- IAM user + access keys: Rejected — long-lived credentials are a security risk
- AWS CodePipeline: Over-engineered for a single deploy target

## R5: Smoke Test Strategy

**Decision**: Shell script (`smoke-test.sh`) run as a post-deploy step in the GitHub workflow

**Rationale**: Keeps smoke tests simple, fast, and CI-native. The script:
1. Curls `/health/live` and `/health/ready`
2. Uses Python + websockets library to test WebSocket auth (valid + invalid)
3. Sends `codec_negotiate` and verifies `codec_ack` + `session_ready`
4. Exits non-zero on any failure (deploy step fails)

**Token for testing**: Generate a test token by calling Cognito `admin-initiate-auth` in the smoke test, or use a pre-generated long-lived token stored as a GitHub secret.

**Alternatives considered**:
- Playwright E2E from frontend: Too heavy for deployment verification
- AWS Synthetic Canaries: Good for ongoing monitoring but overkill for deploy-time check
- pytest-based: Would work but requires Python runtime in the deploy job (already available via uv)

## R6: Rollback Strategy

**Decision**: Rely on ECS rolling deployment with circuit breaker

**Rationale**: ECS rolling deployment with `deployment_circuit_breaker { enable = true, rollback = true }` automatically rolls back if the new task fails health checks. No manual intervention needed.

**Alternatives considered**:
- Blue/green: More complex, higher cost (double resources during deploy) — overkill for dev
- Manual rollback: Error-prone, slow
