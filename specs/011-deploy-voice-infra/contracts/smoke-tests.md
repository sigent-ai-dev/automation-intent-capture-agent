# Contract: Smoke Tests

**Type**: Post-deploy verification | **Scope**: `.github/scripts/smoke-test.sh`

## Test Suite

| Test ID | Name                  | Method                               | Expected Result                          |
| ------- | --------------------- | ------------------------------------ | ---------------------------------------- |
| ST-01   | Health liveness       | `GET /health/live`                   | 200, body contains `"alive"`             |
| ST-02   | Health readiness      | `GET /health/ready`                  | 200, body contains `"ready"`             |
| ST-03   | WebSocket auth accept | WS upgrade with valid token          | Connection accepted, protocol echoed     |
| ST-04   | WebSocket auth reject | WS upgrade without token             | Connection closed with code 4001         |
| ST-05   | Codec negotiation     | Send `codec_negotiate` after connect | Receive `codec_ack` + `session_ready`    |

## Inputs

- `SERVICE_URL`: ALB endpoint (passed as environment variable)
- `TEST_TOKEN`: Valid Cognito ID token (generated during test or from secret)

## Exit Codes

- `0`: All tests passed
- `1`: One or more tests failed (deploy step should fail)

## Timeout

- Each individual test: 10 second timeout
- Total suite: 30 second timeout
