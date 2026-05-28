"""Unit tests for JWT validation middleware."""

import os
from unittest.mock import AsyncMock, patch

import pytest

os.environ.setdefault("LOCAL_MODE", "true")

from voice_server.auth.middleware import get_current_user, validate_ws_token


@pytest.mark.asyncio
async def test_local_mode_returns_local_claims():
    claims = await get_current_user(authorization=None)
    assert claims.sub == "local"
    assert claims.email == "local@dev"


@pytest.mark.asyncio
async def test_local_mode_ignores_token():
    claims = await get_current_user(authorization="Bearer anything")
    assert claims.sub == "local"


@pytest.mark.asyncio
async def test_missing_auth_header_in_prod():
    with patch("voice_server.auth.middleware.get_auth_config") as mock_config:
        mock_config.return_value.local_mode = False
        from fastapi import HTTPException

        with pytest.raises(HTTPException) as exc_info:
            await get_current_user(authorization=None)
        assert exc_info.value.status_code == 401
        assert "Not authenticated" in exc_info.value.detail


@pytest.mark.asyncio
async def test_invalid_auth_scheme_in_prod():
    with patch("voice_server.auth.middleware.get_auth_config") as mock_config:
        mock_config.return_value.local_mode = False
        from fastapi import HTTPException

        with pytest.raises(HTTPException) as exc_info:
            await get_current_user(authorization="Basic dXNlcjpwYXNz")
        assert exc_info.value.status_code == 401
        assert "Invalid authorization scheme" in exc_info.value.detail


@pytest.mark.asyncio
async def test_ws_local_mode_returns_claims():
    ws = AsyncMock()
    ws.query_params = {}
    claims = await validate_ws_token(ws)
    assert claims is not None
    assert claims.sub == "local"


@pytest.mark.asyncio
async def test_ws_missing_token_in_prod():
    with patch("voice_server.auth.middleware.get_auth_config") as mock_config:
        mock_config.return_value.local_mode = False
        ws = AsyncMock()
        ws.query_params = {}
        claims = await validate_ws_token(ws)
        assert claims is None
        ws.close.assert_called_once_with(code=4001, reason="Missing auth token")
