import time

from fastapi import APIRouter

from voice_server.sessions.registry import registry

router = APIRouter(prefix="/health", tags=["health"])

_start_time = time.time()


def _uptime() -> float:
    return time.time() - _start_time


@router.get("/live")
async def liveness():
    return {"status": "alive"}


@router.get("/ready")
async def readiness():
    from voice_server.main import accepting_new

    if not accepting_new:
        return {
            "status": "draining",
            "active_sessions": registry.active_count,
            "uptime_seconds": _uptime(),
        }

    return {
        "status": "ready",
        "active_sessions": registry.active_count,
        "uptime_seconds": _uptime(),
    }
