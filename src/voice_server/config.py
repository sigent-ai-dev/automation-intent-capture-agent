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
    nova_sonic_model_id: str = field(
        default_factory=lambda: os.environ.get("NOVA_SONIC_MODEL_ID", "amazon.nova-sonic-v2:0")
    )
    reconnect_before_seconds: int = field(
        default_factory=lambda: int(os.environ.get("RECONNECT_BEFORE_SECONDS", "60"))
    )
    history_window_size: int = field(
        default_factory=lambda: int(os.environ.get("HISTORY_WINDOW_SIZE", "10"))
    )
    barge_in_energy_threshold: float = field(
        default_factory=lambda: float(os.environ.get("BARGE_IN_ENERGY_THRESHOLD", "0.15"))
    )
    max_voice_retries: int = field(
        default_factory=lambda: int(os.environ.get("MAX_VOICE_RETRIES", "3"))
    )
    public_url: str = field(default_factory=lambda: os.environ.get("PUBLIC_URL", ""))
    intent_dir: str = field(default_factory=lambda: os.environ.get("INTENT_DIR", ".intent"))
    dynamo_table_name: str = field(
        default_factory=lambda: os.environ.get("DYNAMO_TABLE_NAME", "intent-capture-sessions")
    )
    dynamo_endpoint_url: str = field(
        default_factory=lambda: os.environ.get("DYNAMO_ENDPOINT_URL", "")
    )
    session_ttl_seconds: int = field(
        default_factory=lambda: int(os.environ.get("SESSION_TTL_SECONDS", "86400"))
    )
    slack_webhook_url: str = field(default_factory=lambda: os.environ.get("SLACK_WEBHOOK_URL", ""))
    slack_channel: str = field(default_factory=lambda: os.environ.get("SLACK_CHANNEL", ""))
    slack_enabled: bool = field(
        default_factory=lambda: os.environ.get("SLACK_ENABLED", "true").lower() == "true"
    )
    slack_bot_token: str = field(default_factory=lambda: os.environ.get("SLACK_BOT_TOKEN", ""))
    slack_signing_secret: str = field(
        default_factory=lambda: os.environ.get("SLACK_SIGNING_SECRET", "")
    )
    history_summarise_threshold: int = field(
        default_factory=lambda: int(os.environ.get("HISTORY_SUMMARISE_THRESHOLD", "30"))
    )


def get_settings() -> Settings:
    return Settings()
