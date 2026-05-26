import json

import pytest
from starlette.testclient import TestClient

import voice_server.main as main_module
from voice_server.main import app


@pytest.fixture
def client():
    return TestClient(app)


def test_health_ready_returns_draining_during_shutdown(client):
    original = main_module.accepting_new
    main_module.accepting_new = False
    try:
        response = client.get("/health/ready")
        data = response.json()
        assert data["status"] == "draining"
    finally:
        main_module.accepting_new = original


def test_websocket_still_works_during_drain(client):
    """Existing connections should still function during drain."""
    with client.websocket_connect("/ws/audio") as ws:
        ws.send_text(
            json.dumps(
                {
                    "type": "codec_negotiate",
                    "codec": "pcm",
                    "sample_rate": 16000,
                    "bit_depth": 16,
                    "channels": 1,
                }
            )
        )
        response = json.loads(ws.receive_text())
        assert response["type"] == "codec_ack"
