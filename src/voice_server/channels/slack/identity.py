from __future__ import annotations

from voice_server.observability.logging import get_logger

logger = get_logger(__name__)


async def resolve_email_from_slack(client, user_id: str) -> str | None:
    try:
        response = await client.users_info(user=user_id)
        profile = response.get("user", {}).get("profile", {})
        email = profile.get("email")
        if not email:
            logger.warning("slack_email_not_available", user_id=user_id)
            return None
        return email
    except Exception as e:
        logger.warning("slack_identity_resolution_failed", user_id=user_id, error=str(e))
        return None
