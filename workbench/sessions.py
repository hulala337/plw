"""Session lifecycle policy."""
from dataclasses import dataclass
from datetime import datetime

@dataclass(frozen=True)
class SessionWindow:
    started_at: datetime
    ended_at: datetime | None = None

    @property
    def duration_seconds(self) -> float:
        return max(0.0, ((self.ended_at or datetime.now()) - self.started_at).total_seconds())
