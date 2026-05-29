# Data Model: Vite 6 Upgrade and Cognito Authentication

**Date**: 2026-05-28 | **Feature**: 006-vite6-cognito-auth

## Entities

### AuthUser

Represents an authenticated user's session state in the frontend.

| Field    | Type     | Description                                      |
| -------- | -------- | ------------------------------------------------ |
| username | string   | Display name (email or preferred_username)       |
| token    | string   | Cognito ID token (JWT) for backend authorization |
| groups   | string[] | Cognito group memberships (e.g., ["admin"])      |

**Source**: Extracted from Cognito session after successful authentication.

### AuthState

Represents the authentication lifecycle state machine.

| State                  | Description                                         | Transitions to            |
| ---------------------- | --------------------------------------------------- | ------------------------- |
| loading                | Initial state — checking for existing session       | authenticated, unauthenticated |
| unauthenticated        | No valid session — login form displayed             | authenticated, new-password-required |
| new-password-required  | Admin-created account needs password change         | authenticated             |
| authenticated          | Valid session — voice interface accessible           | unauthenticated           |

### CognitoUserPool (Infrastructure)

| Attribute                | Value                          |
| ------------------------ | ------------------------------ |
| Username attribute       | email                          |
| Auto-verified attributes | email                          |
| Password min length      | 8                              |
| Require lowercase        | yes                            |
| Require numbers          | yes                            |
| Require uppercase        | yes                            |
| Require symbols          | no                             |

### CognitoClient (Infrastructure)

| Attribute                          | Value                                  |
| ---------------------------------- | -------------------------------------- |
| Name                               | intent-capture-ui                      |
| Generate secret                    | no (SPA client)                        |
| Explicit auth flows                | ALLOW_USER_SRP_AUTH, ALLOW_REFRESH_TOKEN_AUTH |
| Supported identity providers       | COGNITO + configured federation providers |
| OAuth flows                        | code (for federation)                  |
| OAuth scopes                       | openid, email, profile                 |
| Callback URLs                      | app URL + localhost:5173 (dev)         |

### CognitoUserGroups (Infrastructure)

| Group  | Precedence | Description                                |
| ------ | ---------- | ------------------------------------------ |
| admin  | 1          | Guards future admin panel                  |
| user   | 2          | Default authenticated user (all users)     |

## Relationships

```
AuthUser ──reads from──▶ CognitoSession (Amplify-managed)
AuthUser.groups ──mapped from──▶ CognitoUserGroups
RoleGuard ──checks──▶ AuthUser.groups
WebSocket ──carries──▶ AuthUser.token (via Sec-WebSocket-Protocol)
```

## Validation Rules

- Email must be valid RFC 5322 format (enforced by Cognito)
- Password: ≥8 chars, at least 1 uppercase, 1 lowercase, 1 number
- Token: Valid JWT signed by the Cognito user pool (backend validates independently)
- Groups: Array of strings; empty array means default user (no special access)
