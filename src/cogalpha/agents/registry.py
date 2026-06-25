"""Agent registry for the CogAlpha factor mining system.

Defines 21 specialized research agents across 7 levels of financial analysis.
"""
from dataclasses import dataclass
from typing import Final


@dataclass(frozen=True)
class AgentSpec:
    """Specification for a single CogAlpha research agent."""
    agent_id: str
    level: int
    name: str
    perspective: str
    template_file: str


# ponytail: compact table — 21 agents, 7 levels, 3 per level
_AGENT_TABLE: Final[tuple[tuple[int, str, str, str], ...]] = (
    # Level 1: Market Structure & Cycle
    (1, "Trend and Phase", "Market trend and cycle phase detection", "trend_phase"),
    (1, "Volatility Regime", "Volatility state identification", "vol_regime"),
    (1, "Phase Transition", "Market regime transition signals", "phase_shift"),
    # Level 2: Extreme Risk & Fragility
    (2, "Tail Risk", "Tail risk and crash precursors", "tail_risk"),
    (2, "Fragility", "System fragility patterns", "fragility"),
    (2, "Liquidity Dry-up", "Liquidity exhaustion detection", "liquidity_dry"),
    # Level 3: Volume-Price Dynamics
    (3, "Order Imbalance", "Order flow imbalance", "order_imbalance"),
    (3, "Volume-Price Sync", "Volume-price synchronization", "volume_price_sync"),
    (3, "Turnover Anomaly", "Turnover rate anomaly", "turnover_anomaly"),
    # Level 4: Price Behavior
    (4, "Momentum", "Momentum persistence", "momentum"),
    (4, "Mean Reversion", "Short-term mean reversion", "mean_reversion"),
    (4, "Vol Clustering", "Volatility clustering", "vol_clustering"),
    # Level 5: Multi-scale Complexity
    (5, "Drawdown Geometry", "Drawdown-recovery geometry", "drawdown_geo"),
    (5, "Hurst Exponent", "Hurst exponent / long memory", "hurst"),
    (5, "DFA", "Detrended fluctuation analysis", "dfa"),
    # Level 6: Stability & Control
    (6, "Time Stability", "Time stability assessment", "time_stability"),
    (6, "Adaptive Control", "Adaptive control mechanism", "adaptive_ctrl"),
    (6, "Signal Gate", "Signal activation gating", "signal_gate"),
    # Level 7: Geometry & Fusion
    (7, "Candle Pattern", "Candlestick pattern recognition", "candle_pattern"),
    (7, "Linear Fusion", "Multi-factor linear fusion", "linear_fusion"),
    (7, "Nonlinear Fusion", "Multi-factor nonlinear fusion", "fusion"),
)

_ALL_AGENTS: Final[list[AgentSpec]] = [
    AgentSpec(
        agent_id=f"Agent_{i:02d}",
        level=level,
        name=name,
        perspective=perspective,
        template_file=f"prompts/agent_{i:02d}_lv{level}_{slug}.j2",
    )
    for i, (level, name, perspective, slug) in enumerate(_AGENT_TABLE, start=1)
]

_AGENT_MAP: Final[dict[str, AgentSpec]] = {a.agent_id: a for a in _ALL_AGENTS}


def get_all_agents() -> list[AgentSpec]:
    """Return all 21 registered agents."""
    return list(_ALL_AGENTS)


def get_agent_by_id(agent_id: str) -> AgentSpec:
    """Retrieve a single agent by its agent_id."""
    try:
        return _AGENT_MAP[agent_id]
    except KeyError as exc:
        raise KeyError(f"Agent '{agent_id}' not found in registry.") from exc
