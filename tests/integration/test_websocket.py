import json

import pytest
from httpx import ASGITransport, AsyncClient
from starlette.testclient import TestClient
from starlette.websockets import WebSocketDisconnect

from voice_server.main import app


@pytest.fixture
def client():
    return TestClient(app)


def test_websocket_connect_and_negotiate(client):
    with client.websocket_connect("/ws/audio") as ws:
        ws.send_text(json.dumps({
            "type": "codec_negotiate",
            "codec": "pcm",
            "sample_rate": 16000,
            "bit_depth": 16,
            "channels": 1,
        }))
        response = json.loads(ws.receive_text())
        assert response["type"] == "codec_ack"
        assert response["codec"] == "pcm"
        assert "session_id" in response

        ready = json.loads(ws.receive_text())
        assert ready["type"] == "session_ready"


def test_websocket_reject_unsupported_codec(client):
    with client.websocket_connect("/ws/audio") as ws:
        ws.send_text(json.dumps({
            "type": "codec_negotiate",
            "codec": "opus",
            "sample_rate": 48000,
            "bit_depth": 16,
            "channels": 2,
        }))
        response = json.loads(ws.receive_text())
        assert response["type"] == "codec_reject"
        assert "opus" in response["reason"].lower() or "Unsupported" in response["reason"]


def test_websocket_binary_audio_exchange(client):
    with client.websocket_connect("/ws/audio") as ws:
        ws.send_text(json.dumps({
            "type": "codec_negotiate",
            "codec": "pcm",
            "sample_rate": 16000,
            "bit_depth": 16,
            "channels": 1,
        }))
        ws.receive_text()  # codec_ack
        ws.receive_text()  # session_ready

        audio_frame = b"\x00\x01" * 4096
        ws.send_bytes(audio_frame)
        # Server receives without error — no response expected for audio in MVP
        # (downstream BidiAgent not connected yet)


def test_websocket_ping_pong(client):
    with client.websocket_connect("/ws/audio") as ws:
        ws.send_text(json.dumps({
            "type": "codec_negotiate",
            "codec": "pcm",
            "sample_rate": 16000,
            "bit_depth": 16,
            "channels": 1,
        }))
        ws.receive_text()  # codec_ack
        ws.receive_text()  # session_ready

        ws.send_text(json.dumps({"type": "ping"}))
        response = json.loads(ws.receive_text())
        assert response["type"] == "pong"


def test_websocket_invalid_message(client):
    with client.websocket_connect("/ws/audio") as ws:
        ws.send_text(json.dumps({
            "type": "codec_negotiate",
            "codec": "pcm",
            "sample_rate": 16000,
            "bit_depth": 16,
            "channels": 1,
        }))
        ws.receive_text()  # codec_ack
        ws.receive_text()  # session_ready

        ws.send_text("not valid json {{{")
        response = json.loads(ws.receive_text())
        assert response["type"] == "error"
        assert response["code"] == "INVALID_FRAME"
