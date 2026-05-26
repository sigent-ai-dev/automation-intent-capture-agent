import json

import pytest

from voice_server.models.codec import AudioCodec
from voice_server.ws.protocol import (
    ProtocolError,
    codec_from_message,
    make_codec_ack,
    make_codec_reject,
    make_error,
    make_pong,
    make_session_ready,
    make_server_shutdown,
    parse_control_message,
)


def test_parse_valid_message():
    raw = json.dumps({"type": "ping"})
    msg = parse_control_message(raw)
    assert msg["type"] == "ping"


def test_parse_invalid_json():
    with pytest.raises(ProtocolError, match="Invalid JSON"):
        parse_control_message("not json {{{")


def test_parse_missing_type():
    with pytest.raises(ProtocolError, match="Missing 'type'"):
        parse_control_message(json.dumps({"data": "hello"}))


def test_codec_from_message():
    msg = {"codec": "pcm", "sample_rate": 16000, "bit_depth": 16, "channels": 1}
    codec = codec_from_message(msg)
    assert codec == AudioCodec.default()


def test_codec_from_message_missing_fields():
    codec = codec_from_message({})
    assert codec.format == ""
    assert codec.sample_rate == 0


def test_make_codec_ack():
    codec = AudioCodec.default()
    raw = make_codec_ack("session-123", codec)
    msg = json.loads(raw)
    assert msg["type"] == "codec_ack"
    assert msg["session_id"] == "session-123"
    assert msg["codec"] == "pcm"
    assert msg["sample_rate"] == 16000


def test_make_codec_reject():
    raw = make_codec_reject("Unsupported codec: opus")
    msg = json.loads(raw)
    assert msg["type"] == "codec_reject"
    assert "opus" in msg["reason"]


def test_make_session_ready():
    raw = make_session_ready("sess-1", "user-1")
    msg = json.loads(raw)
    assert msg["type"] == "session_ready"
    assert msg["session_id"] == "sess-1"
    assert msg["user_id"] == "user-1"
    assert "timestamp" in msg


def test_make_pong():
    msg = json.loads(make_pong())
    assert msg["type"] == "pong"
    assert "timestamp" in msg


def test_make_error():
    msg = json.loads(make_error("something broke", "INVALID_FRAME"))
    assert msg["type"] == "error"
    assert msg["message"] == "something broke"
    assert msg["code"] == "INVALID_FRAME"


def test_make_server_shutdown():
    msg = json.loads(make_server_shutdown(30))
    assert msg["type"] == "server_shutdown"
    assert msg["drain_seconds"] == 30
