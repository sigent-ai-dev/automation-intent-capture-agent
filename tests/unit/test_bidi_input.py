import asyncio
import base64

import pytest

from voice_server.bidi.input import WebSocketBidiInput


@pytest.fixture
def bidi_input():
    return WebSocketBidiInput()


async def test_push_and_yield(bidi_input: WebSocketBidiInput):
    audio = b"\x00\x01" * 160
    await bidi_input.push(audio)

    event = await asyncio.wait_for(bidi_input(), timeout=1.0)
    assert event["type"] == "bidi_audio_input"
    assert base64.b64decode(event["audio"]) == audio
    assert event["sample_rate"] == 16000
    assert event["channels"] == 1
    assert event["format"] == "pcm"


async def test_empty_queue_blocks(bidi_input: WebSocketBidiInput):
    with pytest.raises(asyncio.TimeoutError):
        await asyncio.wait_for(bidi_input(), timeout=0.1)


async def test_stop_raises_cancelled(bidi_input: WebSocketBidiInput):
    async def stop_after_delay():
        await asyncio.sleep(0.05)
        await bidi_input.stop()

    asyncio.create_task(stop_after_delay())
    with pytest.raises(asyncio.CancelledError):
        await bidi_input()


async def test_push_ignored_after_stop(bidi_input: WebSocketBidiInput):
    await bidi_input.stop()
    await bidi_input.push(b"\x00\x01" * 160)
    assert bidi_input._queue.qsize() == 1  # only the stop sentinel


async def test_clear_empties_queue(bidi_input: WebSocketBidiInput):
    await bidi_input.push(b"\x01" * 100)
    await bidi_input.push(b"\x02" * 100)
    assert bidi_input._queue.qsize() == 2
    bidi_input.clear()
    assert bidi_input._queue.empty()
