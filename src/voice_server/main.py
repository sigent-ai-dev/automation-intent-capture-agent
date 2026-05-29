import asyncio
import signal
from contextlib import asynccontextmanager

from fastapi import FastAPI, WebSocket
from fastapi.middleware.cors import CORSMiddleware

from voice_server.config import get_settings
from voice_server.capture.endpoints import router as capture_router
from voice_server.health.endpoints import router as health_router
from voice_server.observability.logging import configure_logging, get_logger
from voice_server.sessions.cleanup import start_cleanup_task, stop_cleanup_task
from voice_server.persistence.session_adapter import SessionPersistenceAdapter
from voice_server.sessions.registry import registry
from voice_server.ws.handler import websocket_audio_endpoint

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

    active_sessions = registry.all_sessions()
    if active_sessions and registry._persistence:
        failed = registry._persistence.drain_all(active_sessions)
        if failed:
            logger.warning("drain_persistence_failed", failed_count=len(failed))
        else:
            logger.info("all_sessions_persisted", count=len(active_sessions))

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
    if not settings.local_mode:
        registry._persistence = SessionPersistenceAdapter()
        logger.info("dynamo_persistence_enabled", table=settings.dynamo_table_name)
    if settings.slack_webhook_url and settings.slack_enabled:
        from voice_server.notifications import register_adapter
        from voice_server.notifications.slack import SlackNotificationAdapter

        register_adapter(SlackNotificationAdapter())
        logger.info("slack_notifications_enabled")
    if settings.slack_bot_token:
        from voice_server.channels.slack.app import create_slack_app

        create_slack_app()
        logger.info("slack_bot_registered")
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

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5174", "http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

from voice_server.channels.endpoints import router as channels_router  # noqa: E402

app.include_router(health_router)
app.include_router(capture_router)
app.include_router(channels_router)


@app.post("/slack/events")
async def slack_events(request):
    from voice_server.channels.slack.app import get_slack_handler

    handler = get_slack_handler()
    if handler is None:
        from fastapi.responses import JSONResponse

        return JSONResponse({"error": "Slack bot not configured"}, status_code=503)
    return await handler.handle(request)


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
