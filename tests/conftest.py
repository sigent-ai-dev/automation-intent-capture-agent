import os

os.environ.setdefault("LOCAL_MODE", "true")

import pytest
from httpx import ASGITransport, AsyncClient

from voice_server.main import app
from voice_server.models.codec import AudioCodec
from voice_server.models.session import Session, SessionState
from voice_server.sessions.registry import registry


@pytest.fixture(autouse=True)
def clean_registry():
    yield
    for session in list(registry._sessions.values()):
        registry.remove(session.id)


@pytest.fixture
def sample_session() -> Session:
    return Session(user_id="test-user-001", state=SessionState.STREAMING)


@pytest.fixture
def sample_codec() -> AudioCodec:
    return AudioCodec.default()


@pytest.fixture
async def http_client():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        yield client
