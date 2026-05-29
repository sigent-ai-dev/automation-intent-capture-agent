#!/usr/bin/env bash
set -euo pipefail

SERVICE_URL="${SERVICE_URL:?SERVICE_URL environment variable required}"
PASSED=0
FAILED=0

echo "=== Smoke Tests: $SERVICE_URL ==="

# ST-01: Health liveness
echo -n "ST-01 Health liveness... "
RESPONSE=$(curl -sk --max-time 10 "$SERVICE_URL/health/live" 2>/dev/null || true)
if echo "$RESPONSE" | grep -q '"alive"'; then
  echo "PASS"
  ((PASSED++))
else
  echo "FAIL: $RESPONSE"
  ((FAILED++))
fi

# ST-02: Health readiness
echo -n "ST-02 Health readiness... "
RESPONSE=$(curl -sk --max-time 10 "$SERVICE_URL/health/ready" 2>/dev/null || true)
if echo "$RESPONSE" | grep -q '"ready"'; then
  echo "PASS"
  ((PASSED++))
else
  echo "FAIL: $RESPONSE"
  ((FAILED++))
fi

# ST-03: WebSocket auth accept (requires valid token)
echo -n "ST-03 WebSocket auth accept... "
if [ -n "${SMOKE_TEST_USERNAME:-}" ] && [ -n "${SMOKE_TEST_PASSWORD:-}" ]; then
  TOKEN=$(python3 -c "
import json, subprocess, sys
result = subprocess.run([
    'aws', 'cognito-idp', 'initiate-auth',
    '--client-id', '${COGNITO_CLIENT_ID}',
    '--auth-flow', 'USER_PASSWORD_AUTH',
    '--auth-parameters', 'USERNAME=${SMOKE_TEST_USERNAME},PASSWORD=${SMOKE_TEST_PASSWORD}',
    '--region', 'eu-west-1',
    '--output', 'json'
], capture_output=True, text=True)
if result.returncode != 0:
    print('', end='')
    sys.exit(0)
data = json.loads(result.stdout)
print(data.get('AuthenticationResult', {}).get('IdToken', ''), end='')
" 2>/dev/null || true)

  if [ -n "$TOKEN" ]; then
    WS_URL="${SERVICE_URL/https:/wss:}/ws/audio"
    WS_RESULT=$(python3 -c "
import asyncio, json, websockets

async def test():
    try:
        async with websockets.connect('$WS_URL', subprotocols=['v1.audio.intent', '$TOKEN'], open_timeout=10) as ws:
            await ws.send(json.dumps({'type':'codec_negotiate','codec':'pcm','sample_rate':16000,'bit_depth':16,'channels':1}))
            ack = json.loads(await asyncio.wait_for(ws.recv(), timeout=5))
            if ack.get('type') == 'codec_ack':
                print('PASS')
            else:
                print(f'FAIL: unexpected response {ack}')
    except Exception as e:
        print(f'FAIL: {e}')

asyncio.run(test())
" 2>/dev/null || echo "FAIL: python error")
    echo "$WS_RESULT"
    if [ "$WS_RESULT" = "PASS" ]; then ((PASSED++)); else ((FAILED++)); fi
  else
    echo "SKIP (could not obtain token)"
  fi
else
  echo "SKIP (no test credentials configured)"
fi

# ST-04: WebSocket auth reject (no token)
echo -n "ST-04 WebSocket auth reject... "
WS_URL="${SERVICE_URL/https:/wss:}/ws/audio"
REJECT_RESULT=$(python3 -c "
import asyncio, websockets

async def test():
    try:
        async with websockets.connect('$WS_URL', open_timeout=5) as ws:
            await ws.recv()
            print('FAIL: connection should have been rejected')
    except websockets.exceptions.ConnectionClosed as e:
        if e.code == 4001:
            print('PASS')
        else:
            print(f'FAIL: unexpected close code {e.code}')
    except websockets.exceptions.InvalidStatusCode as e:
        if e.status_code == 403 or 'Unauthorized' in str(e):
            print('PASS')
        else:
            print(f'FAIL: {e}')
    except Exception as e:
        # Some servers reject before upgrade completes
        if '4001' in str(e) or 'Unauthorized' in str(e):
            print('PASS')
        else:
            print(f'FAIL: {e}')

asyncio.run(test())
" 2>/dev/null || echo "FAIL: python error")
echo "$REJECT_RESULT"
if [ "$REJECT_RESULT" = "PASS" ]; then ((PASSED++)); else ((FAILED++)); fi

# ST-05: Codec negotiation (uses same token flow as ST-03)
echo -n "ST-05 Codec negotiation... "
if [ -n "${TOKEN:-}" ]; then
  CODEC_RESULT=$(python3 -c "
import asyncio, json, websockets

async def test():
    try:
        async with websockets.connect('$WS_URL', subprotocols=['v1.audio.intent', '$TOKEN'], open_timeout=10) as ws:
            await ws.send(json.dumps({'type':'codec_negotiate','codec':'pcm','sample_rate':16000,'bit_depth':16,'channels':1}))
            ack = json.loads(await asyncio.wait_for(ws.recv(), timeout=5))
            if ack.get('type') != 'codec_ack':
                print(f'FAIL: expected codec_ack got {ack}')
                return
            ready = json.loads(await asyncio.wait_for(ws.recv(), timeout=5))
            if ready.get('type') == 'session_ready':
                print('PASS')
            else:
                print(f'FAIL: expected session_ready got {ready}')
    except Exception as e:
        print(f'FAIL: {e}')

asyncio.run(test())
" 2>/dev/null || echo "FAIL: python error")
  echo "$CODEC_RESULT"
  if [ "$CODEC_RESULT" = "PASS" ]; then ((PASSED++)); else ((FAILED++)); fi
else
  echo "SKIP (no token available)"
fi

echo ""
echo "=== Results: $PASSED passed, $FAILED failed ==="

if [ "$FAILED" -gt 0 ]; then
  exit 1
fi
