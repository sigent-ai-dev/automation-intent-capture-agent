import os
from dataclasses import dataclass, field


@dataclass(frozen=True)
class Settings:
    port: int = field(default_factory=lambda: int(os.environ.get("PORT", "8080")))
    host: str = field(default_factory=lambda: os.environ.get("HOST", "0.0.0.0"))
    log_level: str = field(default_factory=lambda: os.environ.get("LOG_LEVEL", "INFO"))
    stale_session_timeout_seconds: int = field(
        default_factory=lambda: int(os.environ.get("STALE_SESSION_TIMEOUT_SECONDS", "30"))
    )
    shutdown_drain_seconds: int = field(
        default_factory=lambda: int(os.environ.get("SHUTDOWN_DRAIN_SECONDS", "30"))
    )
    local_mode: bool = field(
        default_factory=lambda: os.environ.get("LOCAL_MODE", "false").lower() == "true"
    )


def get_settings() -> Settings:
    return Settings()
