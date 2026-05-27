"""Integration test for full voice flow: connect → negotiate → send audio → receive response → disconnect.

Requires real AWS credentials with Bedrock Nova Sonic access.
Run with: uv run pytest tests/integration/test_bidi_agent.py -v
"""

import asyncio
import struct

import pytest
import websockets

ENDPOINT = "ws://localhost:8080/ws/audio"
pytestmark = pytest.mark.skipif(
    "not config.getoption('--run-integration', default=False)",
    reason="Requires --run-integration flag and running server",
)


def _generate_silence_pcm(duration_ms: int = 500, sample_rate: int = 16000) -> bytes:
    """Generate silence PCM audio (16-bit mono)."""
    num_samples = int(sample_rate * duration_ms / 1000)
    return struct.pack(f"<{num_samples}h", *([0] * num_samples))


@pytest.fixture
def anyio_backend():
    return "asyncio"


async def test_full_voice_flow():
    """Connect, negotiate codec, send audio, receive agent response, disconnect."""
    import json

    async with websockets.connect(
        ENDPOINT, additional_headers={"X-User-Id": "integration-test-user"}
    ) as ws:
        # Negotiate codec
        await ws.send(
            json.dumps(
                {
                    "type": "codec_negotiate",
                    "codec": "pcm",
                    "sample_rate": 16000,
                    "bit_depth": 16,
                    "channels": 1,
                }
            )
        )

        # Expect codec_ack
        ack = json.loads(await asyncio.wait_for(ws.recv(), timeout=5))
        assert ack["type"] == "codec_ack"

        # Expect session_ready
        ready = json.loads(await asyncio.wait_for(ws.recv(), timeout=5))
        assert ready["type"] == "session_ready"

        # Send silence audio (agent should still process it)
        audio = _generate_silence_pcm(duration_ms=1000)
        chunk_size = 3200  # 100ms at 16kHz 16-bit mono
        for i in range(0, len(audio), chunk_size):
            await ws.send(audio[i : i + chunk_size])
            await asyncio.sleep(0.1)

        # Wait for agent response (either audio bytes or control message)
        received_audio = False
        received_agent_done = False
        deadline = asyncio.get_event_loop().time() + 15

        while asyncio.get_event_loop().time() < deadline:
            try:
                msg = await asyncio.wait_for(ws.recv(), timeout=2)
                if isinstance(msg, bytes):
                    received_audio = True
                elif isinstance(msg, str):
                    data = json.loads(msg)
                    if data.get("type") == "agent_done":
                        received_agent_done = True
                        break
            except asyncio.TimeoutError:
                break

        assert received_audio or received_agent_done, (
            "Expected either audio or agent_done from the voice agent"
        )
