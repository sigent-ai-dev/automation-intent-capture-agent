from __future__ import annotations

from slack_bolt.async_app import AsyncApp
from slack_bolt.adapter.fastapi.async_handler import AsyncSlackRequestHandler

from voice_server.channels.slack.elicitation import handle_slack_message
from voice_server.config import get_settings
from voice_server.observability.logging import get_logger

logger = get_logger(__name__)

_slack_app: AsyncApp | None = None
_handler: AsyncSlackRequestHandler | None = None


def create_slack_app() -> AsyncApp | None:
    global _slack_app, _handler
    settings = get_settings()

    if not settings.slack_bot_token:
        logger.info("slack_bot_disabled", reason="SLACK_BOT_TOKEN not configured")
        return None

    _slack_app = AsyncApp(
        token=settings.slack_bot_token,
        signing_secret=settings.slack_signing_secret,
    )

    @_slack_app.event("app_mention")
    async def handle_mention(event, client, say):
        await handle_slack_message(client, event, say)

    @_slack_app.event("message")
    async def handle_dm(event, client, say):
        if event.get("channel_type") == "im":
            await handle_slack_message(client, event, say)

    _handler = AsyncSlackRequestHandler(_slack_app)
    logger.info("slack_bot_enabled")
    return _slack_app


def get_slack_handler() -> AsyncSlackRequestHandler | None:
    return _handler
