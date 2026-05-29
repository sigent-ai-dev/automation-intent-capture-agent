# Implementation Plan: Vite 6 Upgrade and Cognito Authentication

**Branch**: `006-vite6-cognito-auth` | **Date**: 2026-05-28 | **Spec**: [spec.md](./spec.md)

**Input**: Feature specification from `specs/006-vite6-cognito-auth/spec.md`

## Summary

Upgrade the frontend build tooling from Vite 5 to Vite 6 (with vitest 2.x), and add AWS Cognito-based authentication using Amplify v6. The auth layer includes email/password login (SRP), federated sign-in (Microsoft/Okta/Google), role-based route guards via Cognito groups, and token attachment to WebSocket connections via the Sec-WebSocket-Protocol header. Infrastructure is provisioned via Terraform (Cognito user pool, client, groups).

## Technical Context

**Language/Version**: TypeScript 5.6+, React 18.3, Python 3.12 (backend — token validation only)

**Primary Dependencies**: Vite 6, vitest 2, aws-amplify 6.16+, @aws-amplify/auth 6, @vitejs/plugin-react 4.3, Tailwind CSS 3.4

**Storage**: Cognito user pool (identity store), DynamoDB (existing session state)

**Testing**: vitest (unit), Playwright (E2E), @testing-library/react 16

**Target Platform**: Modern browsers (Chrome, Firefox, Safari, Edge — Web Crypto API required for SRP)

**Project Type**: Web application (React SPA + Python FastAPI backend)

**Performance Goals**: Login-to-interface <5s, federated redirect cycle <10s, production build <30s

**Constraints**: Token passed via Sec-WebSocket-Protocol header (not URL), Cognito built-in throttling for brute-force protection

**Scale/Scope**: Single-tenant initially, admin group guards future admin panel (no admin UI yet)

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principle | Status | Notes |
|-----------|--------|-------|
| I. Meet Them Where They Are | PASS | Auth login is minimal barrier — users access via browser as before |
| II. Propose, Don't Interrogate | N/A | Auth feature, not elicitation |
| III. Structured Output | N/A | Auth feature, not intent capture |
| IV. Multi-Source Convergence | N/A | Auth feature, not intent capture |
| V. Channel-Agnostic Core | PASS | Auth is a frontend adapter concern, doesn't touch elicitation engine |
| VI. Graceful Degradation | PASS | Missing Cognito config logs console error, app degrades gracefully |

| Quality Standard | Status | Notes |
|-----------------|--------|-------|
| API responses <200ms | PASS | Auth is client-side (Amplify SDK → Cognito), no backend API changes |
| Tests cover each adapter independently | PASS | Auth service tests are independent of voice/session tests |

**Gate result**: PASS — no violations.

## Project Structure

### Documentation (this feature)

```text
specs/006-vite6-cognito-auth/
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
├── contracts/           # Phase 1 output
└── tasks.md             # Phase 2 output (/speckit-tasks)
```

### Source Code (repository root)

```text
frontend/
├── src/
│   ├── components/
│   │   ├── auth/
│   │   │   ├── LoginForm.tsx
│   │   │   ├── NewPasswordForm.tsx
│   │   │   └── RoleGuard.tsx
│   │   ├── chat/
│   │   ├── common/
│   │   ├── connection/
│   │   ├── controls/
│   │   ├── layout/
│   │   └── session/
│   ├── config/
│   │   ├── amplify.ts
│   │   └── constants.ts
│   ├── contexts/
│   │   ├── AuthContext.tsx
│   │   ├── ConversationContext.tsx
│   │   ├── SessionContext.tsx
│   │   └── ThemeContext.tsx
│   ├── services/
│   │   ├── authService.ts
│   │   ├── sessionService.ts
│   │   └── websocketService.ts
│   ├── types/
│   │   ├── auth.ts
│   │   └── ...existing types
│   └── hooks/
│       └── ...existing hooks
├── tests/
│   ├── unit/
│   │   ├── services/authService.test.ts
│   │   └── components/auth/LoginForm.test.tsx
│   └── e2e/
│       └── auth.spec.ts
├── package.json
└── vite.config.ts

terraform/
├── modules/
│   ├── voice-service/        # existing
│   └── cognito/              # NEW
│       ├── main.tf
│       ├── variables.tf
│       └── outputs.tf
├── main.tf                   # updated to call cognito module
└── variables.tf              # new cognito variables
```

**Structure Decision**: Extends existing frontend/ directory with auth components, context, service, and types. Terraform gets a new cognito module alongside voice-service.
