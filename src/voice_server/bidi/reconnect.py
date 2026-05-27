from __future__ import annotations

import asyncio
import json
from typing import TYPE_CHECKING

from voice_server.observability.logging import get_logger

if TYPE_CHECKING:
    from voice_server.bidi.agent import AudioBridge

logger = get_logger(__name__)


class ReconnectionManager:
    """Manages proactive hot-swap reconnection before the 8-minute limit."""

    def __init__(self, bridge: AudioBridge, reconnect_before_seconds: int = 60) -> None:
        self._bridge = bridge
        self._reconnect_seconds = reconnect_before_seconds
        self._timer_task: asyncio.Task | None = None
        self._swap_delay = max(0, 480 - reconnect_before_seconds)

    def start(self) -> None:
        self._timer_task = asyncio.create_task(self._timer())

    async def _timer(self) -> None:
        try:
            await asyncio.sleep(self._swap_delay)
            await self._do_swap()
        except asyncio.CancelledError:
            pass

    async def _do_swap(self) -> None:
        from voice_server.bidi.agent import create_bidi_agent

        logger.info("reconnection_starting", session_id=self._bridge.session_id)

        ws = self._bridge.output._ws
        await ws.send_text(json.dumps({"type": "voice_reconnecting"}))

        old_agent = self._bridge._agent
        old_task = self._bridge._agent_task

        history_context = self._bridge.history.get_summary_and_recent()
        system_prompt = (
            "You are a helpful voice assistant for capturing business intent. "
            "Listen carefully and respond concisely.\n\n"
            f"Conversation so far:\n{history_context}"
        )

        new_agent = create_bidi_agent(system_prompt=system_prompt)
        self._bridge._agent = new_agent
        self._bridge.input.clear()

        self._bridge._agent_task = asyncio.create_task(self._bridge._run_agent())

        if old_task and not old_task.done():
            old_task.cancel()
            try:
                await old_task
            except (asyncio.CancelledError, Exception):
                pass
        if old_agent:
            try:
                await old_agent.stop()
            except Exception:
                pass

        await ws.send_text(json.dumps({"type": "voice_reconnected"}))
        logger.info("reconnection_complete", session_id=self._bridge.session_id)

        # Restart timer for next reconnection
        self._timer_task = asyncio.create_task(self._timer())

    async def stop(self) -> None:
        if self._timer_task and not self._timer_task.done():
            self._timer_task.cancel()
            try:
                await self._timer_task
            except (asyncio.CancelledError, Exception):
                pass
        self._timer_task = None
