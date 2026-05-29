from __future__ import annotations

import httpx

from voice_server.config import get_settings
from voice_server.notifications.events import ErrorOccurred, IntentFinalised
from voice_server.notifications.rate_limiter import RateLimiter
from voice_server.observability.logging import get_logger
from voice_server.observability.metrics import (
    record_notification_failed,
    record_notification_rate_limited,
    record_notification_sent,
)

logger = get_logger(__name__)

_rate_limiter = RateLimiter(window_seconds=60)


class SlackNotificationAdapter:
    def __init__(self) -> None:
        settings = get_settings()
        self._webhook_url = settings.slack_webhook_url
        self._channel = settings.slack_channel

    async def send(self, event) -> None:
        if not self._webhook_url:
            return

        event_type = type(event).__name__

        if isinstance(event, IntentFinalised):
            payload = _format_intent_notification(event, self._channel)
        elif isinstance(event, ErrorOccurred):
            if not _rate_limiter.allow(f"error:{event.error_type}"):
                record_notification_rate_limited(event_type)
                logger.debug("notification_rate_limited", error_type=event.error_type)
                return
            payload = _format_error_notification(event, self._channel)
        else:
            return

        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.post(self._webhook_url, json=payload)
                if response.status_code != 200:
                    record_notification_failed(event_type, f"HTTP {response.status_code}")
                    logger.warning(
                        "slack_delivery_failed",
                        status=response.status_code,
                        body=response.text[:200],
                    )
                else:
                    record_notification_sent(event_type)
        except Exception as e:
            record_notification_failed(event_type, str(e))
            logger.warning("slack_delivery_error", error=str(e))


def _format_intent_notification(event: IntentFinalised, channel: str) -> dict:
    fields_str = ", ".join(event.populated_fields) if event.populated_fields else "none"
    clr_str = f"{event.open_clarifications} open" if event.open_clarifications else "none"

    text = f"🎯 Intent Captured: {event.project_name}"

    blocks = [
        {
            "type": "header",
            "text": {"type": "plain_text", "text": f"🎯 Intent Captured: {event.project_name}"},
        },
        {
            "type": "section",
            "fields": [
                {"type": "mrkdwn", "text": f"*Actor:* {event.actor}"},
                {"type": "mrkdwn", "text": f"*ID:* {event.intent_id}"},
                {"type": "mrkdwn", "text": f"*Fields:* {len(event.populated_fields)}/6"},
                {"type": "mrkdwn", "text": f"*Clarifications:* {clr_str}"},
            ],
        },
        {
            "type": "section",
            "text": {"type": "mrkdwn", "text": f"*Intent:* {event.intent_summary}"},
        },
    ]

    if event.full_content and len(event.full_content) <= 2000:
        blocks.append(
            {
                "type": "section",
                "text": {"type": "mrkdwn", "text": f"```{event.full_content[:2000]}```"},
            }
        )
    elif event.full_content:
        blocks.append(
            {
                "type": "context",
                "elements": [
                    {
                        "type": "mrkdwn",
                        "text": f"_Document too long for inline display. See `.intent/{event.intent_id}.md`_",
                    }
                ],
            }
        )

    blocks.append(
        {
            "type": "context",
            "elements": [{"type": "mrkdwn", "text": f"Populated: {fields_str}"}],
        }
    )

    payload: dict = {"text": text, "blocks": blocks}
    if channel:
        payload["channel"] = channel
    return payload


def _format_error_notification(event: ErrorOccurred, channel: str) -> dict:
    text = f"⚠️ {event.error_type}: {event.description}"

    blocks = [
        {
            "type": "header",
            "text": {"type": "plain_text", "text": "⚠️ Voice Service Error"},
        },
        {
            "type": "section",
            "fields": [
                {"type": "mrkdwn", "text": f"*Type:* {event.error_type}"},
                {"type": "mrkdwn", "text": f"*Session:* {event.session_id}"},
                {"type": "mrkdwn", "text": f"*Time:* {event.timestamp.isoformat()}"},
            ],
        },
        {
            "type": "section",
            "text": {"type": "mrkdwn", "text": event.description},
        },
    ]

    payload: dict = {"text": text, "blocks": blocks}
    if channel:
        payload["channel"] = channel
    return payload
