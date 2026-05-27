from __future__ import annotations

import asyncio
import base64
from typing import TYPE_CHECKING

from strands.experimental.bidi import BidiAudioInputEvent

if TYPE_CHECKING:
    from strands.experimental.bidi.agent.agent import BidiAgent
    from strands.experimental.bidi.types.events import BidiInputEvent


class WebSocketBidiInput:
    """Bridges WebSocket binary audio frames to the Strands BidiAgent input protocol."""

    def __init__(self) -> None:
        self._queue: asyncio.Queue[bytes] = asyncio.Queue()
        self._stopped = False

    async def start(self, agent: BidiAgent) -> None:
        self._stopped = False

    async def stop(self) -> None:
        self._stopped = True
        await self._queue.put(b"")

    async def __call__(self) -> BidiInputEvent:
        while True:
            chunk = await self._queue.get()
            if self._stopped:
                raise asyncio.CancelledError
            if chunk:
                return BidiAudioInputEvent(
                    audio=base64.b64encode(chunk).decode(),
                    format="pcm",
                    sample_rate=16000,
                    channels=1,
                )

    async def push(self, audio_bytes: bytes) -> None:
        if not self._stopped:
            await self._queue.put(audio_bytes)

    def clear(self) -> None:
        while not self._queue.empty():
            try:
                self._queue.get_nowait()
            except asyncio.QueueEmpty:
                break
