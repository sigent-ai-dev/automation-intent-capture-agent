import asyncio
from datetime import datetime, timezone

from voice_server.config import get_settings
from voice_server.models.session import SessionState
from voice_server.observability.logging import get_logger
from voice_server.sessions.registry import registry

logger = get_logger(__name__)

CLEANUP_INTERVAL_SECONDS = 10

_cleanup_task: asyncio.Task | None = None


async def _cleanup_loop() -> None:
    settings = get_settings()
    timeout = settings.stale_session_timeout_seconds

    while True:
        try:
            await asyncio.sleep(CLEANUP_INTERVAL_SECONDS)
            now = datetime.now(timezone.utc)
            stale = []

            for session in registry.all_sessions():
                if session.state in (SessionState.CONNECTING, SessionState.STREAMING):
                    elapsed = (now - session.last_activity).total_seconds()
                    if elapsed > timeout:
                        stale.append(session.id)

            for session_id in stale:
                registry.remove(session_id)
                logger.info("stale_session_removed", session_id=session_id)

            if stale:
                logger.info("cleanup_sweep_complete", removed_count=len(stale))
        except asyncio.CancelledError:
            break
        except Exception as e:
            logger.error("cleanup_error", error=str(e))


def start_cleanup_task() -> None:
    global _cleanup_task
    if _cleanup_task is None or _cleanup_task.done():
        _cleanup_task = asyncio.create_task(_cleanup_loop())
        logger.info("cleanup_task_started")


def stop_cleanup_task() -> None:
    global _cleanup_task
    if _cleanup_task and not _cleanup_task.done():
        _cleanup_task.cancel()
        logger.info("cleanup_task_stopped")
