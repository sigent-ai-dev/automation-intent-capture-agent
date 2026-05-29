# Implementation Plan: Deploy Voice Service Infrastructure

**Branch**: `011-deploy-voice-infra` | **Date**: 2026-05-29 | **Spec**: [spec.md](./spec.md)

**Input**: Feature specification from `specs/011-deploy-voice-infra/spec.md`

## Summary

Provision VPC, ECS Fargate, ALB, ECR, and DynamoDB in the builder-admin account (885659622434). Update the backend WebSocket auth handler to read Cognito tokens from the Sec-WebSocket-Protocol header. Configure GitHub OIDC for CI/CD deployment. Add post-deploy smoke tests for health, auth, and codec negotiation.

## Technical Context

**Language/Version**: Python 3.12 (backend), Terraform 1.5+ (IaC), GitHub Actions (CI/CD)

**Primary Dependencies**: FastAPI, Uvicorn, python-jose (JWT), httpx (JWKS fetch), websockets (smoke tests)

**Storage**: DynamoDB (session state), ECR (container images)

**Testing**: pytest (unit), custom smoke test script (post-deploy)

**Target Platform**: AWS ECS Fargate (eu-west-1), ALB with WebSocket support

**Project Type**: Web service (container deployment + infrastructure)

**Performance Goals**: Health <1s, WebSocket auth <2s, deploy <5min

**Constraints**: Self-signed HTTPS for dev ALB, single container instance, GitHub OIDC (no long-lived creds)

**Scale/Scope**: Single dev environment initially, single container, no autoscaling

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principle | Status | Notes |
|-----------|--------|-------|
| I. Meet Them Where They Are | PASS | Deployment makes the service accessible — users don't need local setup |
| II. Propose, Don't Interrogate | N/A | Infrastructure feature, not elicitation |
| III. Structured Output | N/A | Infrastructure feature |
| IV. Multi-Source Convergence | N/A | Infrastructure feature |
| V. Channel-Agnostic Core | PASS | Auth handler is in the WebSocket adapter layer, not the core engine |
| VI. Graceful Degradation | PASS | JWKS caching, health check degraded state, rollback on failed deploy |

| Quality Standard | Status | Notes |
|-----------------|--------|-------|
| API responses <200ms | PASS | Health endpoints are trivial; target is <1s from internet (includes network) |
| Tests cover each adapter independently | PASS | Smoke tests cover WebSocket auth independently |

**Gate result**: PASS — no violations.

## Project Structure

### Documentation (this feature)

```text
specs/011-deploy-voice-infra/
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
├── contracts/           # Phase 1 output
└── tasks.md             # Phase 2 output (/speckit-tasks)
```

### Source Code (repository root)

```text
src/voice_server/
├── ws/
│   └── auth.py              # MODIFIED — Sec-WebSocket-Protocol token extraction
├── auth/
│   ├── config.py            # Auth configuration (Cognito pool ID, region)
│   ├── jwks.py              # JWKS fetch + caching
│   └── middleware.py        # JWT validation (existing, reused)
└── ...

terraform/
├── modules/
│   ├── voice-service/       # Existing — ECS, ALB, ECR, DynamoDB, IAM
│   ├── cognito/             # Existing — user pool
│   └── networking/          # NEW — VPC, subnets, NAT, IGW
├── main.tf                  # Updated — add networking module, wire outputs
├── variables.tf             # Updated — remove hard-coded VPC vars
└── environments/
    └── dev.tfvars           # NEW — dev environment values

.github/
├── workflows/
│   └── deploy.yml           # MODIFIED — add smoke test step, OIDC role
└── scripts/
    └── smoke-test.sh        # NEW — post-deploy verification

tests/
└── unit/
    └── test_ws_auth.py      # NEW — unit tests for Sec-WebSocket-Protocol auth
```

**Structure Decision**: Extends existing terraform modules with a new networking module. Modifies the WebSocket auth handler. Adds a smoke test script to the deploy workflow.
