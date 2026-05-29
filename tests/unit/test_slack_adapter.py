from unittest.mock import AsyncMock

from voice_server.channels.slack.identity import resolve_email_from_slack


async def test_resolve_email_success():
    client = AsyncMock()
    client.users_info.return_value = {
        "user": {"profile": {"email": "alice@example.com"}}
    }
    result = await resolve_email_from_slack(client, "U1234")
    assert result == "alice@example.com"


async def test_resolve_email_hidden():
    client = AsyncMock()
    client.users_info.return_value = {"user": {"profile": {}}}
    result = await resolve_email_from_slack(client, "U1234")
    assert result is None


async def test_resolve_email_api_error():
    client = AsyncMock()
    client.users_info.side_effect = Exception("API error")
    result = await resolve_email_from_slack(client, "U1234")
    assert result is None
