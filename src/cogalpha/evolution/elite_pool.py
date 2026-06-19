"""Elite pool for preserving top-performing factors."""
import csv
import difflib
from pathlib import Path
from typing import List
from cogalpha.factors.object import FactorObject


class ElitePool:
    """Stores and manages elite factors across evolution generations."""

    def __init__(self):
        self._elites: list[tuple[FactorObject, dict]] = []

    def add(self, factor: FactorObject, metrics: dict | None = None):
        """Add a factor and its metrics to the pool."""
        m = metrics or factor.metrics
        self._elites.append((factor, m))

    def get_top_k(self, k: int) -> list[FactorObject]:
        """Return top k factors sorted by composite score descending."""
        sorted_elites = sorted(
            self._elites,
            key=lambda item: item[0].composite_score(),
            reverse=True,
        )
        return [f for f, _ in sorted_elites[:k]]

    def preserve_elites(self, n: int = 2) -> list[FactorObject]:
        """Return top N elites for the next generation."""
        return self.get_top_k(n)

    def deduplicate(self, threshold: float = 0.95):
        """Remove duplicates based on code string similarity."""
        unique = []
        for factor, metrics in self._elites:
            is_duplicate = False
            for u_factor, _ in unique:
                ratio = difflib.SequenceMatcher(None, factor.raw_code, u_factor.raw_code).ratio()
                if ratio > threshold:
                    is_duplicate = True
                    break
            if not is_duplicate:
                unique.append((factor, metrics))
        self._elites = unique

    def to_csv(self, path: str):
        """Export all elites to a CSV file."""
        Path(path).parent.mkdir(parents=True, exist_ok=True)
        with open(path, "w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow([
                "factor_id", "agent_id", "status", "raw_code",
                "ic", "rankic", "icir", "rankicir",
                "composite_score", "long_short_return",
            ])
            for factor, _ in self._elites:
                m = factor.metrics
                writer.writerow([
                    factor.factor_id,
                    factor.agent_id,
                    factor.status,
                    factor.raw_code,
                    m.get("ic", ""),
                    m.get("rankic", ""),
                    m.get("icir", ""),
                    m.get("rankicir", ""),
                    m.get("composite_score", ""),
                    m.get("long_short_return", ""),
                ])

    def __len__(self) -> int:
        return len(self._elites)
