import asyncio

from fastapi import WebSocket, WebSocketDisconnect

from voice_server.config import get_settings
from voice_server.models.codec import AudioCodec
from voice_server.models.session import Session, SessionState
from voice_server.observability.logging import get_logger
from voice_server.observability.metrics import (
    record_error,
    record_session_connect,
    record_session_disconnect,
)
from voice_server.sessions.registry import registry
from voice_server.ws.auth import extract_user_id
from voice_server.ws.protocol import (
    ProtocolError,
    codec_from_message,
    make_codec_ack,
    make_codec_reject,
    make_error,
    make_pong,
    make_session_ready,
    parse_control_message,
)

logger = get_logger(__name__)

CODEC_NEGOTIATION_TIMEOUT_SECONDS = 5


async def websocket_audio_endpoint(websocket: WebSocket) -> None:
    user_id = extract_user_id(websocket)
    if user_id is None:
        await websocket.close(code=4001, reason="Unauthorized")
        return

    await websocket.accept()

    session = Session(user_id=user_id)
    registry.create(session)
    record_session_connect(session.id)
    logger.info("session_created", session_id=session.id, user_id=user_id)

    bridge = None
    try:
        codec = await _negotiate_codec(websocket, session)
        if codec is None:
            return

        session.codec = codec
        session.transition_to(SessionState.STREAMING)

        await websocket.send_text(make_session_ready(session.id, user_id))
        logger.info("session_streaming", session_id=session.id)

        settings = get_settings()
        if not settings.local_mode:
            from voice_server.bidi.agent import AudioBridge

            bridge = AudioBridge(session_id=session.id, ws=websocket)
            await bridge.start()
            logger.info("audio_bridge_started", session_id=session.id)

        await _stream_loop(websocket, session, bridge)
    except WebSocketDisconnect:
        logger.info("client_disconnected", session_id=session.id)
    except Exception as e:
        record_error(session.id, type(e).__name__)
        logger.error("session_error", session_id=session.id, error=str(e))
    finally:
        if bridge:
            await bridge.stop()
        session.transition_to(SessionState.DISCONNECTING)
        registry.remove(session.id)
        record_session_disconnect(session.id)
        logger.info("session_closed", session_id=session.id)


async def _negotiate_codec(websocket: WebSocket, session: Session) -> AudioCodec | None:
    try:
        raw = await asyncio.wait_for(
            websocket.receive_text(), timeout=CODEC_NEGOTIATION_TIMEOUT_SECONDS
        )
    except asyncio.TimeoutError:
        await websocket.send_text(make_error("Codec negotiation timeout", "CODEC_TIMEOUT"))
        await websocket.close(code=4002, reason="Codec negotiation timeout")
        registry.remove(session.id)
        return None

    try:
        msg = parse_control_message(raw)
    except ProtocolError as e:
        await websocket.send_text(make_error(str(e), "INVALID_FRAME"))
        await websocket.close(code=4003, reason="Invalid negotiation message")
        registry.remove(session.id)
        return None

    if msg.get("type") != "codec_negotiate":
        await websocket.send_text(
            make_error("Expected codec_negotiate as first message", "INVALID_FRAME")
        )
        await websocket.close(code=4003, reason="Expected codec_negotiate")
        registry.remove(session.id)
        return None

    codec = codec_from_message(msg)
    if not codec.is_supported():
        reason = (
            f"Unsupported codec: {codec.format} {codec.sample_rate}Hz "
            f"{codec.bit_depth}-bit {codec.channels}ch. "
            f"Supported: pcm (16-bit, 16kHz, mono)"
        )
        await websocket.send_text(make_codec_reject(reason))
        await websocket.close(code=4004, reason="Unsupported codec")
        registry.remove(session.id)
        return None

    await websocket.send_text(make_codec_ack(session.id, codec))
    return codec


async def _stream_loop(websocket: WebSocket, session: Session, bridge: object | None) -> None:
    while True:
        message = await websocket.receive()
        session.touch()

        if "text" in message:
            await _handle_text_frame(websocket, session, message["text"])
        elif "bytes" in message:
            await _handle_binary_frame(session, bridge, message["bytes"])


async def _handle_text_frame(websocket: WebSocket, session: Session, raw: str) -> None:
    try:
        msg = parse_control_message(raw)
    except ProtocolError as e:
        await websocket.send_text(make_error(str(e), "INVALID_FRAME"))
        return

    msg_type = msg.get("type")
    if msg_type == "ping":
        await websocket.send_text(make_pong())
    else:
        await websocket.send_text(make_error(f"Unknown message type: {msg_type}", "INVALID_FRAME"))


async def _handle_binary_frame(session: Session, bridge: object | None, data: bytes) -> None:
    if bridge is not None:
        await bridge.push_audio(data)
