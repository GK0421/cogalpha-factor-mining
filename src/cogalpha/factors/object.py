"""Core FactorObject dataclass for the CogAlpha factor mining framework."""

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Optional


@dataclass
class FactorObject:
    """Represents a single mined factor and its metadata."""

    factor_id: str
    agent_id: str
    mode: str
    raw_response: str
    raw_code: str
    status: str = "pending"
    errors: list[str] = field(default_factory=list)
    metrics: dict = field(default_factory=dict)
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

    def composite_score(self) -> float:
        """Compute a composite score from metrics."""
        if not self.metrics:
            return 0.0
        ic = self.metrics.get("ic", 0.0)
        rankic = self.metrics.get("rankic", 0.0)
        icir = self.metrics.get("icir", 0.0)
        rankicir = self.metrics.get("rankicir", 0.0)
        return abs(ic) * 0.2 + abs(rankic) * 0.2 + abs(icir) * 0.3 + abs(rankicir) * 0.3

    def to_dict(self) -> dict:
        """Return a serializable dictionary representation."""
        return {
            "factor_id": self.factor_id,
            "agent_id": self.agent_id,
            "mode": self.mode,
            "raw_response": self.raw_response,
            "raw_code": self.raw_code,
            "status": self.status,
            "errors": self.errors,
            "metrics": self.metrics,
            "created_at": self.created_at.isoformat() if isinstance(self.created_at, datetime) else self.created_at,
        }
