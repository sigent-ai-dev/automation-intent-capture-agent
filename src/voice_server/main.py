import asyncio
import signal
from contextlib import asynccontextmanager

from fastapi import FastAPI, WebSocket

from voice_server.config import get_settings
from voice_server.health.endpoints import router as health_router
from voice_server.observability.logging import configure_logging, get_logger
from voice_server.sessions.cleanup import start_cleanup_task, stop_cleanup_task
from voice_server.sessions.registry import registry
from voice_server.ws.handler import websocket_audio_endpoint
from voice_server.ws.protocol import make_server_shutdown

settings = get_settings()
configure_logging(settings.log_level)
logger = get_logger(__name__)

accepting_new = True
shutdown_event = asyncio.Event()


def _signal_handler(signum: int, _frame: object) -> None:
    global accepting_new
    logger.info("shutdown_signal_received", signal=signum)
    accepting_new = False
    shutdown_event.set()


async def _graceful_shutdown() -> None:
    if not shutdown_event.is_set():
        return
    drain_seconds = settings.shutdown_drain_seconds
    logger.info("graceful_shutdown_started", drain_seconds=drain_seconds)
    for i in range(drain_seconds):
        if registry.active_count == 0:
            logger.info("all_sessions_drained")
            return
        await asyncio.sleep(1)
    logger.warning("shutdown_drain_timeout", remaining_sessions=registry.active_count)


@asynccontextmanager
async def lifespan(app: FastAPI):
    signal.signal(signal.SIGTERM, _signal_handler)
    signal.signal(signal.SIGINT, _signal_handler)
    start_cleanup_task()
    logger.info("server_starting", port=settings.port, local_mode=settings.local_mode)
    yield
    stop_cleanup_task()
    await _graceful_shutdown()
    logger.info("server_shutting_down")


app = FastAPI(
    title="Voice Server",
    description="WebSocket audio server for Intent Capture Agent",
    version="0.1.0",
    lifespan=lifespan,
)

app.include_router(health_router)


@app.websocket("/ws/audio")
async def ws_audio(websocket: WebSocket) -> None:
    await websocket_audio_endpoint(websocket)


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "voice_server.main:app",
        host=settings.host,
        port=settings.port,
        reload=settings.local_mode,
    )
