"""Data models for capture sessions."""

from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from uuid import uuid4


class CaptureStatus(Enum):
    PENDING = "pending"
    ACTIVE = "active"
    COMPLETE = "complete"
    FAILED = "failed"
    CANCELLED = "cancelled"


@dataclass
class CaptureProgress:
    sections_covered: list[str] = field(default_factory=list)
    proposal_rounds: int = 0
    alignment_reached: bool = False

    def to_dict(self) -> dict:
        return {
            "sections_covered": self.sections_covered,
            "proposal_rounds": self.proposal_rounds,
            "alignment_reached": self.alignment_reached,
        }


@dataclass
class CaptureResult:
    intent_md: str = ""
    state: dict = field(default_factory=dict)
    audit_md: str = ""

    def to_dict(self) -> dict:
        return {
            "intent_md": self.intent_md,
            "state": self.state,
            "audit_md": self.audit_md,
        }


@dataclass
class CaptureSession:
    id: str = field(default_factory=lambda: str(uuid4()))
    project_name: str = ""
    downstream_tool: str | None = None
    notification_webhook: str | None = None
    status: CaptureStatus = CaptureStatus.PENDING
    progress: CaptureProgress = field(default_factory=CaptureProgress)
    result: CaptureResult | None = None
    participants: list[str] = field(default_factory=list)
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    error: str | None = None

    @property
    def join_url(self) -> str:
        from voice_server.config import get_settings

        settings = get_settings()
        base = settings.public_url or f"http://localhost:{settings.port}"
        return f"{base}/join/{self.id}"

    def touch(self) -> None:
        self.updated_at = datetime.now(timezone.utc)

    def to_summary_dict(self) -> dict:
        return {
            "session_id": self.id,
            "project_name": self.project_name,
            "status": self.status.value,
            "join_url": self.join_url,
            "created_at": self.created_at.isoformat(),
        }

    def to_detail_dict(self) -> dict:
        d = self.to_summary_dict()
        d["progress"] = self.progress.to_dict()
        d["participants"] = self.participants
        d["updated_at"] = self.updated_at.isoformat()
        if self.error:
            d["error"] = self.error
        return d
