import json
import time
from typing import Any

from voice_server.models.codec import AudioCodec


class ProtocolError(Exception):
    pass


def parse_control_message(raw: str) -> dict[str, Any]:
    try:
        msg = json.loads(raw)
    except json.JSONDecodeError as e:
        raise ProtocolError(f"Invalid JSON: {e}") from e
    if "type" not in msg:
        raise ProtocolError("Missing 'type' field in control message")
    return msg


def codec_from_message(msg: dict[str, Any]) -> AudioCodec:
    return AudioCodec(
        format=msg.get("codec", ""),
        sample_rate=msg.get("sample_rate", 0),
        bit_depth=msg.get("bit_depth", 0),
        channels=msg.get("channels", 0),
    )


def make_codec_ack(session_id: str, codec: AudioCodec) -> str:
    return json.dumps({
        "type": "codec_ack",
        "session_id": session_id,
        "codec": codec.format,
        "sample_rate": codec.sample_rate,
        "bit_depth": codec.bit_depth,
        "channels": codec.channels,
    })


def make_codec_reject(reason: str) -> str:
    return json.dumps({"type": "codec_reject", "reason": reason})


def make_session_ready(session_id: str, user_id: str) -> str:
    return json.dumps({
        "type": "session_ready",
        "session_id": session_id,
        "user_id": user_id,
        "timestamp": int(time.time() * 1000),
    })


def make_pong() -> str:
    return json.dumps({"type": "pong", "timestamp": int(time.time() * 1000)})


def make_error(message: str, code: str = "INTERNAL_ERROR") -> str:
    return json.dumps({"type": "error", "message": message, "code": code})


def make_server_shutdown(drain_seconds: int) -> str:
    return json.dumps({
        "type": "server_shutdown",
        "drain_seconds": drain_seconds,
        "message": "Server is shutting down for deployment",
    })
