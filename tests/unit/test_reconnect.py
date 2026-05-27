import asyncio
from unittest.mock import AsyncMock, MagicMock

import pytest

from voice_server.bidi.reconnect import ReconnectionManager


@pytest.fixture
def mock_bridge():
    bridge = MagicMock()
    bridge.session_id = "test-session"
    bridge.input = MagicMock()
    bridge.input.clear = MagicMock()
    bridge.output = MagicMock()
    bridge.history = MagicMock()
    bridge.history.get_summary_and_recent = MagicMock(return_value="summary text")
    bridge._agent = MagicMock()
    bridge._agent.stop = AsyncMock()
    bridge._agent_task = None
    return bridge


async def test_timer_fires_and_triggers_swap(mock_bridge):
    mgr = ReconnectionManager(bridge=mock_bridge, reconnect_before_seconds=480)
    mgr._do_swap = AsyncMock()
    mgr.start()
    await asyncio.sleep(0.1)
    mgr._do_swap.assert_called_once()
    await mgr.stop()


async def test_stop_cancels_timer(mock_bridge):
    mgr = ReconnectionManager(bridge=mock_bridge, reconnect_before_seconds=60)
    mgr.start()
    await mgr.stop()
    assert mgr._timer_task is None or mgr._timer_task.done()
