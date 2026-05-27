from __future__ import annotations

import asyncio
import json

from strands.experimental.bidi import BidiAgent
from strands.experimental.bidi.models.nova_sonic import BidiNovaSonicModel

from voice_server.bidi.history import ConversationHistory
from voice_server.bidi.input import WebSocketBidiInput
from voice_server.bidi.output import WebSocketBidiOutput, WebSocketSender
from voice_server.bidi.reconnect import ReconnectionManager
from voice_server.config import get_settings
from voice_server.observability.logging import get_logger

logger = get_logger(__name__)


def create_bidi_agent(
    system_prompt: str | None = None, tools: list | None = None
) -> BidiAgent:
    settings = get_settings()
    model = BidiNovaSonicModel(model_id=settings.nova_sonic_model_id)
    from voice_server.elicitation.tools import (
        create_intent,
        finalise_intent,
        read_intent,
        update_intent_section,
    )

    all_tools = [create_intent, update_intent_section, read_intent, finalise_intent]
    if tools:
        all_tools.extend(tools)
    return BidiAgent(model=model, system_prompt=system_prompt, tools=all_tools)


class AudioBridge:
    """Owns BidiInput, BidiOutput, and the BidiAgent lifecycle for a session."""

    def __init__(self, session_id: str, ws: WebSocketSender) -> None:
        self.session_id = session_id
        settings = get_settings()
        self.history = ConversationHistory(
            session_id=session_id, window_size=settings.history_window_size
        )
        self.input = WebSocketBidiInput()
        self.output = WebSocketBidiOutput(ws=ws, history=self.history)
        self._ws = ws
        self._agent: BidiAgent | None = None
        self._agent_task: asyncio.Task | None = None
        self._reconnection: ReconnectionManager | None = None
        self._max_retries = settings.max_voice_retries
        self._retrying = False

    async def start(self) -> None:
        from voice_server.elicitation.prompts import build_resume_context, build_system_prompt
        from voice_server.elicitation.storage import find_draft_intents, load_intent

        settings = get_settings()
        self._trace_subsegment("voice_connection.start")

        resume_context = None
        drafts = find_draft_intents()
        if drafts:
            doc = load_intent(drafts[-1])
            if doc:
                resume_context = build_resume_context(doc)

        system_prompt = build_system_prompt(resume_context=resume_context)
        self._agent = create_bidi_agent(system_prompt=system_prompt)
        self._agent_task = asyncio.create_task(self._run_agent())
        self._reconnection = ReconnectionManager(
            bridge=self, reconnect_before_seconds=settings.reconnect_before_seconds
        )
        self._reconnection.start()
        self._end_subsegment()
        logger.info("audio_bridge_started", session_id=self.session_id)

    async def _run_agent(self) -> None:
        if self._agent is None:
            return
        try:
            await self._agent.run(
                inputs=[self.input],
                outputs=[self.output],
            )
        except asyncio.CancelledError:
            pass
        except Exception as e:
            logger.error("bidi_agent_error", session_id=self.session_id, error=str(e))
            if not self._retrying:
                await self._handle_agent_error(e)

    async def _handle_agent_error(self, error: Exception) -> None:
        self._retrying = True
        for attempt in range(1, self._max_retries + 1):
            logger.info(
                "bidi_agent_retry",
                session_id=self.session_id,
                attempt=attempt,
                error=str(error),
            )
            try:
                history_context = self.history.get_summary_and_recent()
                system_prompt = (
                    "You are a helpful voice assistant for capturing business intent. "
                    "Listen carefully and respond concisely.\n\n"
                    f"Conversation so far:\n{history_context}"
                )
                self._agent = create_bidi_agent(system_prompt=system_prompt)
                self._retrying = False
                self._agent_task = asyncio.create_task(self._run_agent())
                return
            except Exception as retry_error:
                logger.error(
                    "bidi_agent_retry_failed",
                    session_id=self.session_id,
                    attempt=attempt,
                    error=str(retry_error),
                )

        await self._ws.send_text(json.dumps({"type": "error", "code": "VOICE_SERVICE_UNAVAILABLE"}))

    async def stop(self) -> None:
        self._trace_subsegment("voice_connection.stop")
        if self._reconnection:
            await self._reconnection.stop()
            self._reconnection = None
        await self.input.stop()
        if self._agent_task and not self._agent_task.done():
            self._agent_task.cancel()
            try:
                await self._agent_task
            except (asyncio.CancelledError, Exception):
                pass
        if self._agent:
            try:
                await self._agent.stop()
            except Exception:
                pass
            self._agent = None
        self._agent_task = None
        self._end_subsegment()
        logger.info("audio_bridge_stopped", session_id=self.session_id)

    def _trace_subsegment(self, name: str) -> None:
        try:
            from aws_xray_sdk.core import xray_recorder

            segment = xray_recorder.begin_subsegment(name)
            if segment:
                segment.put_metadata("session_id", self.session_id)
        except Exception:
            pass

    def _end_subsegment(self) -> None:
        try:
            from aws_xray_sdk.core import xray_recorder

            xray_recorder.end_subsegment()
        except Exception:
            pass

    async def push_audio(self, data: bytes) -> None:
        await self.input.push(data)

    async def handle_silence_timeout(self) -> None:
        """Handle voice service disconnect after silence timeout — recover on next audio."""
        logger.info("silence_timeout_detected", session_id=self.session_id)
        await self._ws.send_text(json.dumps({"type": "voice_timeout"}))

    async def resume_after_timeout(self) -> None:
        """Reconnect with history replay when user resumes speaking after timeout."""
        logger.info("resuming_after_timeout", session_id=self.session_id)
        history_context = self.history.get_summary_and_recent()
        system_prompt = (
            "You are a helpful voice assistant for capturing business intent. "
            "Listen carefully and respond concisely.\n\n"
            f"Conversation so far:\n{history_context}"
        )
        self._agent = create_bidi_agent(system_prompt=system_prompt)
        self.input = WebSocketBidiInput()
        self.output = WebSocketBidiOutput(ws=self._ws, history=self.history)
        self._agent_task = asyncio.create_task(self._run_agent())
        if self._reconnection:
            await self._reconnection.stop()
        settings = get_settings()
        self._reconnection = ReconnectionManager(
            bridge=self, reconnect_before_seconds=settings.reconnect_before_seconds
        )
        self._reconnection.start()
        await self._ws.send_text(json.dumps({"type": "voice_recovered"}))
