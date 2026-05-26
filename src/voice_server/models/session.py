from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from uuid import uuid4

from voice_server.models.codec import AudioCodec


class SessionState(Enum):
    CONNECTING = "connecting"
    STREAMING = "streaming"
    DISCONNECTING = "disconnecting"
    CLOSED = "closed"


@dataclass
class Session:
    id: str = field(default_factory=lambda: str(uuid4()))
    user_id: str = ""
    state: SessionState = SessionState.CONNECTING
    connected_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    last_activity: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    codec: AudioCodec = field(default_factory=AudioCodec.default)

    def touch(self) -> None:
        self.last_activity = datetime.now(timezone.utc)

    def transition_to(self, new_state: SessionState) -> None:
        self.state = new_state
        self.touch()
