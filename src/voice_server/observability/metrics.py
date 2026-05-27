import time

from voice_server.observability.logging import get_logger

logger = get_logger(__name__)

_connection_start_times: dict[str, float] = {}


def record_session_connect(session_id: str) -> None:
    _connection_start_times[session_id] = time.time()
    logger.info("metric_session_connect", session_id=session_id)


def record_session_disconnect(session_id: str) -> None:
    start = _connection_start_times.pop(session_id, None)
    duration = time.time() - start if start else 0.0
    logger.info(
        "metric_session_disconnect",
        session_id=session_id,
        duration_seconds=round(duration, 2),
    )


def record_session_timeout(session_id: str) -> None:
    _connection_start_times.pop(session_id, None)
    logger.info("metric_session_timeout", session_id=session_id)


def record_error(session_id: str, error_type: str) -> None:
    logger.info("metric_error", session_id=session_id, error_type=error_type)


def record_reconnection(session_id: str, duration_ms: float) -> None:
    logger.info(
        "metric_voice_reconnection",
        session_id=session_id,
        duration_ms=round(duration_ms, 1),
    )


def record_barge_in(session_id: str, latency_ms: float) -> None:
    logger.info(
        "metric_barge_in",
        session_id=session_id,
        latency_ms=round(latency_ms, 1),
    )


def record_audio_round_trip(session_id: str, round_trip_ms: float) -> None:
    logger.info(
        "metric_audio_round_trip",
        session_id=session_id,
        round_trip_ms=round(round_trip_ms, 1),
    )


def record_voice_error(session_id: str, error_type: str) -> None:
    logger.info(
        "metric_voice_error",
        session_id=session_id,
        error_type=error_type,
    )
