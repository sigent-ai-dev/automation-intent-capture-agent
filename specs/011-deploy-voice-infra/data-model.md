# Data Model: Deploy Voice Service Infrastructure

**Date**: 2026-05-29 | **Feature**: 011-deploy-voice-infra

## Entities

### DeploymentTarget

Represents the deployed service environment.

| Field           | Type   | Description                                     |
| --------------- | ------ | ----------------------------------------------- |
| environment     | string | Environment name (dev, staging, prod)           |
| alb_url         | string | Load balancer endpoint URL                      |
| ecs_cluster     | string | Container orchestration cluster name            |
| ecs_service     | string | Service name within the cluster                 |
| ecr_repository  | string | Container image registry URI                    |
| image_tag       | string | Currently deployed image version                |

### WebSocketAuthResult

Represents the outcome of token validation on WebSocket upgrade.

| Field          | Type    | Description                                      |
| -------------- | ------- | ------------------------------------------------ |
| authenticated  | boolean | Whether the token was valid                      |
| user_id        | string  | Cognito `sub` claim (if valid)                   |
| email          | string  | User email from token (if valid)                 |
| protocol       | string  | Accepted protocol (`v1.audio.intent`) or null    |
| reject_code    | int     | WebSocket close code if rejected (4001)          |

### SmokeTestResult

Represents the outcome of a smoke test run.

| Field       | Type    | Description                          |
| ----------- | ------- | ------------------------------------ |
| test_name   | string  | Name of the specific check           |
| passed      | boolean | Whether the check succeeded          |
| duration_ms | int     | Time taken for the check             |
| error       | string  | Error message if failed              |

## State Transitions

### Deployment Lifecycle

```
IDLE → BUILDING → PUSHING → DEPLOYING → HEALTHY
                                       → FAILED → ROLLED_BACK
```

### WebSocket Auth Flow

```
UPGRADE_RECEIVED → EXTRACT_TOKEN → VALIDATE_JWT → ACCEPTED (echo protocol)
                                                → REJECTED (close 4001)
                 → NO_TOKEN → REJECTED (close 4001)
```
