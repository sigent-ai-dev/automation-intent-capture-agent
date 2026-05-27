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


def record_intent_created(intent_id: str) -> None:
    logger.info("metric_intent_created", intent_id=intent_id)


def record_intent_finalised(intent_id: str, sections_populated: int) -> None:
    logger.info(
        "metric_intent_finalised",
        intent_id=intent_id,
        sections_populated=sections_populated,
    )


def record_persistence_write(session_id: str, record_type: str, latency_ms: float) -> None:
    logger.info(
        "metric_persistence_write",
        session_id=session_id,
        record_type=record_type,
        latency_ms=round(latency_ms, 1),
    )


def record_persistence_read(session_id: str, record_type: str, latency_ms: float) -> None:
    logger.info(
        "metric_persistence_read",
        session_id=session_id,
        record_type=record_type,
        latency_ms=round(latency_ms, 1),
    )


def record_persistence_failure(session_id: str, operation: str, error_type: str) -> None:
    logger.info(
        "metric_persistence_failure",
        session_id=session_id,
        operation=operation,
        error_type=error_type,
    )


def record_drain_result(total_sessions: int, failed_count: int) -> None:
    logger.info(
        "metric_drain_result",
        total_sessions=total_sessions,
        failed_count=failed_count,
    )
