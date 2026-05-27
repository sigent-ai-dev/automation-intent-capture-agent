import base64
import json

import pytest

from voice_server.bidi.history import ConversationHistory
from voice_server.bidi.output import WebSocketBidiOutput


class FakeWebSocket:
    def __init__(self):
        self.bytes_sent: list[bytes] = []
        self.texts_sent: list[str] = []

    async def send_bytes(self, data: bytes) -> None:
        self.bytes_sent.append(data)

    async def send_text(self, data: str) -> None:
        self.texts_sent.append(data)


@pytest.fixture
def ws():
    return FakeWebSocket()


@pytest.fixture
def history():
    return ConversationHistory(session_id="test-session")


@pytest.fixture
def output(ws, history):
    return WebSocketBidiOutput(ws=ws, history=history)


async def test_audio_stream_downsampled_and_sent(output, ws):
    from strands.experimental.bidi import BidiAudioStreamEvent, BidiResponseStartEvent

    await output(BidiResponseStartEvent(response_id="r1"))
    # 6 samples at 24kHz -> 4 samples at 16kHz
    import struct

    audio_24k = struct.pack("<6h", 100, 200, 300, 400, 500, 600)
    audio_b64 = base64.b64encode(audio_24k).decode()
    event = BidiAudioStreamEvent(audio=audio_b64, format="pcm", sample_rate=24000, channels=1)
    await output(event)
    assert len(ws.bytes_sent) == 1
    assert len(ws.bytes_sent[0]) == 4 * 2  # 4 samples * 2 bytes


async def test_transcript_updates_history(output, ws, history):
    from strands.experimental.bidi import BidiTranscriptStreamEvent
    from strands.types.streaming import ContentBlockDelta

    delta = ContentBlockDelta(type="content_block_delta")
    event = BidiTranscriptStreamEvent(delta=delta, text="Hello there", role="user", is_final=True)
    await output(event)
    assert len(history.turns) == 1
    assert history.turns[0].role == "user"
    assert history.turns[0].text == "Hello there"


async def test_non_final_transcript_ignored(output, history):
    from strands.experimental.bidi import BidiTranscriptStreamEvent
    from strands.types.streaming import ContentBlockDelta

    delta = ContentBlockDelta(type="content_block_delta")
    event = BidiTranscriptStreamEvent(delta=delta, text="Hel", role="user", is_final=False)
    await output(event)
    assert len(history.turns) == 0


async def test_error_sends_json(output, ws):
    from strands.experimental.bidi import BidiErrorEvent

    event = BidiErrorEvent(error=RuntimeError("connection lost"))
    await output(event)
    msg = json.loads(ws.texts_sent[0])
    assert msg["type"] == "error"
    assert msg["code"] == "VOICE_ERROR"


async def test_response_start_sends_agent_speaking(output, ws):
    from strands.experimental.bidi import BidiResponseStartEvent

    await output(BidiResponseStartEvent(response_id="r1"))
    msg = json.loads(ws.texts_sent[0])
    assert msg["type"] == "agent_speaking"
    assert output.is_agent_speaking is True


async def test_response_complete_sends_agent_done(output, ws):
    from strands.experimental.bidi import BidiResponseCompleteEvent, BidiResponseStartEvent

    await output(BidiResponseStartEvent(response_id="r1"))
    await output(BidiResponseCompleteEvent(response_id="r1", stop_reason="complete"))
    msgs = [json.loads(t) for t in ws.texts_sent]
    assert msgs[1]["type"] == "agent_done"
    assert output.is_agent_speaking is False


async def test_barge_in_suppresses_audio(output, ws):
    from strands.experimental.bidi import (
        BidiAudioStreamEvent,
        BidiInterruptionEvent,
        BidiResponseStartEvent,
    )

    await output(BidiResponseStartEvent(response_id="r1"))
    await output(BidiInterruptionEvent(reason="user_speech"))
    assert output.barge_in_detected is True
    msg = json.loads(ws.texts_sent[-1])
    assert msg["type"] == "barge_in_ack"

    audio_b64 = base64.b64encode(b"\x00" * 100).decode()
    event = BidiAudioStreamEvent(audio=audio_b64, format="pcm", sample_rate=16000, channels=1)
    await output(event)
    assert len(ws.bytes_sent) == 0  # audio suppressed
