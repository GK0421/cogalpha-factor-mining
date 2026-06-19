"""Feedback log for tracking invalid factors and elite ideas."""
from collections import Counter
from cogalpha.factors.object import FactorObject
from cogalpha.evolution.elite_pool import ElitePool


class FeedbackLog:
    """Tracks invalid factor summaries and elite ideas for prompt injection."""

    def __init__(self):
        self._invalid: list[FactorObject] = []

    def add_invalid(self, factor: FactorObject):
        """Record an invalid factor."""
        self._invalid.append(factor)

    def get_summary(self) -> str:
        """Return a text summary of invalid factors by error type."""
        if not self._invalid:
            return "No invalid factors recorded so far."
        counts = Counter(f.error_type for f in self._invalid if f.error_type)
        lines = ["Invalid factor summary:", f"  Total invalid: {len(self._invalid)}"]
        for err_type, count in counts.items():
            lines.append(f"  {err_type}: {count}")
        return "\n".join(lines)

    def get_elite_ideas(self, pool: ElitePool, n: int = 3) -> str:
        """Return brief ideas of top elites for prompt injection."""
        top = pool.get_top_k(n)
        if not top:
            return "No elite ideas available yet."
        lines = ["Elite factor ideas:"]
        for factor in top:
            lines.append(f"  - {factor.factor_id} (agent={factor.agent_id}): {factor.raw_code[:60]}...")
        return "\n".join(lines)
