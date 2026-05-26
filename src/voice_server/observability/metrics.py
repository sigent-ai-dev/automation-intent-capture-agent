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
