from __future__ import annotations

import base64
import json
from typing import TYPE_CHECKING, Protocol

from strands.experimental.bidi import (
    BidiAudioStreamEvent,
    BidiErrorEvent,
    BidiInterruptionEvent,
    BidiOutputEvent,
    BidiResponseCompleteEvent,
    BidiResponseStartEvent,
    BidiTranscriptStreamEvent,
)

from voice_server.audio.resample import downsample_24k_to_16k
from voice_server.bidi.history import ConversationHistory
from voice_server.observability.logging import get_logger

if TYPE_CHECKING:
    from strands.experimental.bidi.agent.agent import BidiAgent

logger = get_logger(__name__)


class WebSocketSender(Protocol):
    async def send_bytes(self, data: bytes) -> None: ...
    async def send_text(self, data: str) -> None: ...


class WebSocketBidiOutput:
    """Bridges Strands BidiAgent output events to WebSocket frames."""

    def __init__(self, ws: WebSocketSender, history: ConversationHistory) -> None:
        self._ws = ws
        self._history = history
        self.is_agent_speaking = False
        self.barge_in_detected = False
        self._current_assistant_transcript = ""

    async def start(self, agent: BidiAgent) -> None:
        pass

    async def stop(self) -> None:
        pass

    async def __call__(self, event: BidiOutputEvent) -> None:
        if isinstance(event, BidiResponseStartEvent):
            self.is_agent_speaking = True
            self.barge_in_detected = False
            self._current_assistant_transcript = ""
            await self._ws.send_text(json.dumps({"type": "agent_speaking"}))

        elif isinstance(event, BidiAudioStreamEvent):
            if self.barge_in_detected:
                return
            audio_bytes = base64.b64decode(event.audio)
            if event.sample_rate == 24000:
                audio_bytes = downsample_24k_to_16k(audio_bytes)
            await self._ws.send_bytes(audio_bytes)

        elif isinstance(event, BidiTranscriptStreamEvent):
            if event.is_final:
                if event.role == "user":
                    self._history.add_turn("user", event.text)
                elif event.role == "assistant":
                    self._history.add_turn("assistant", event.text)

        elif isinstance(event, BidiInterruptionEvent):
            self.barge_in_detected = True
            self.is_agent_speaking = False
            await self._ws.send_text(json.dumps({"type": "barge_in_ack"}))

        elif isinstance(event, BidiResponseCompleteEvent):
            self.is_agent_speaking = False
            await self._ws.send_text(json.dumps({"type": "agent_done"}))

        elif isinstance(event, BidiErrorEvent):
            await self._ws.send_text(
                json.dumps({"type": "error", "code": "VOICE_ERROR", "message": event.message})
            )
