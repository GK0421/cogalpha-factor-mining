"""FactorLibrary — store and persist mined factor objects."""

import pandas as pd

from .object import FactorObject


class FactorLibrary:
    """In-memory store for FactorObjects with export utilities."""

    def __init__(self):
        self._factors: list[FactorObject] = []

    def add(self, factor: FactorObject) -> None:
        """Add a FactorObject to the library."""
        if not isinstance(factor, FactorObject):
            raise TypeError(f"Expected FactorObject, got {type(factor)}")
        self._factors.append(factor)

    def get_by_status(self, status: str) -> list[FactorObject]:
        """Return all factors matching the given status."""
        return [f for f in self._factors if f.status == status]

    def get_elites(self) -> list[FactorObject]:
        """Return all factors with status 'elite'."""
        return self.get_by_status("elite")

    def to_dataframe(self) -> pd.DataFrame:
        """
        Return a DataFrame summarising the library.
        Columns include factor_id, agent_id, status, and common metrics.
        """
        if not self._factors:
            return pd.DataFrame(
                columns=[
                    "factor_id",
                    "agent_id",
                    "status",
                    "ic",
                    "rankic",
                    "icir",
                    "rankicir",
                ]
            )

        rows = []
        for f in self._factors:
            m = f.metrics
            rows.append(
                {
                    "factor_id": f.factor_id,
                    "agent_id": f.agent_id,
                    "status": f.status,
                    "ic": m.get("ic"),
                    "rankic": m.get("rankic"),
                    "icir": m.get("icir"),
                    "rankicir": m.get("rankicir"),
                    "long_short_return": m.get("long_short_return"),
                }
            )
        return pd.DataFrame(rows)

    def save(self, path: str) -> None:
        """Persist the library summary to a CSV file."""
        self.to_dataframe().to_csv(path, index=False)
