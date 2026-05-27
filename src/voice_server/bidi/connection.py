from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from enum import Enum
from uuid import uuid4

from voice_server.observability.logging import get_logger

logger = get_logger(__name__)


class VoiceConnectionState(Enum):
    CONNECTING = "connecting"
    ACTIVE = "active"
    RECONNECTING = "reconnecting"
    DRAINING = "draining"
    CLOSED = "closed"


@dataclass
class VoiceConnection:
    session_id: str
    id: str = field(default_factory=lambda: str(uuid4()))
    state: VoiceConnectionState = VoiceConnectionState.CONNECTING
    started_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

    @property
    def expires_at(self) -> datetime:
        return self.started_at + timedelta(minutes=8)

    @property
    def reconnect_at(self) -> datetime:
        return self.started_at + timedelta(minutes=7)

    def transition_to(self, new_state: VoiceConnectionState) -> None:
        old_state = self.state
        self.state = new_state
        logger.info(
            "voice_connection_state_change",
            connection_id=self.id,
            session_id=self.session_id,
            from_state=old_state.value,
            to_state=new_state.value,
        )
