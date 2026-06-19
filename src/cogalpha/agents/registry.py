"""Agent registry for the CogAlpha factor mining system.

Defines 21 specialized research agents across 7 levels of financial analysis.
"""
from dataclasses import dataclass


@dataclass(frozen=True)
class AgentSpec:
    """Specification for a single CogAlpha research agent."""
    agent_id: str
    level: int
    name: str
    perspective: str
    template_file: str


# ────────────────────────────────────────────
# Level 1: Market Structure & Cycle (3 agents)
# ────────────────────────────────────────────
_AGENT_01 = AgentSpec(
    agent_id="Agent_01",
    level=1,
    name="Trend and Phase",
    perspective="Market trend and cycle phase detection",
    template_file="prompts/agent_01_lv1_trend_phase.j2",
)

_AGENT_02 = AgentSpec(
    agent_id="Agent_02",
    level=1,
    name="Volatility Regime",
    perspective="Volatility state identification",
    template_file="prompts/agent_02_lv1_vol_regime.j2",
)

_AGENT_03 = AgentSpec(
    agent_id="Agent_03",
    level=1,
    name="Phase Transition",
    perspective="Market regime transition signals",
    template_file="prompts/agent_03_lv1_phase_shift.j2",
)

# ────────────────────────────────────────────
# Level 2: Extreme Risk & Fragility (3 agents)
# ────────────────────────────────────────────
_AGENT_04 = AgentSpec(
    agent_id="Agent_04",
    level=2,
    name="Tail Risk",
    perspective="Tail risk and crash precursors",
    template_file="prompts/agent_04_lv2_tail_risk.j2",
)

_AGENT_05 = AgentSpec(
    agent_id="Agent_05",
    level=2,
    name="Fragility",
    perspective="System fragility patterns",
    template_file="prompts/agent_05_lv2_fragility.j2",
)

_AGENT_06 = AgentSpec(
    agent_id="Agent_06",
    level=2,
    name="Liquidity Dry-up",
    perspective="Liquidity exhaustion detection",
    template_file="prompts/agent_06_lv2_liquidity_dry.j2",
)

# ────────────────────────────────────────────
# Level 3: Volume-Price Dynamics (3 agents)
# ────────────────────────────────────────────
_AGENT_07 = AgentSpec(
    agent_id="Agent_07",
    level=3,
    name="Order Imbalance",
    perspective="Order flow imbalance",
    template_file="prompts/agent_07_lv3_order_imbalance.j2",
)

_AGENT_08 = AgentSpec(
    agent_id="Agent_08",
    level=3,
    name="Volume-Price Sync",
    perspective="Volume-price synchronization",
    template_file="prompts/agent_08_lv3_volume_price_sync.j2",
)

_AGENT_09 = AgentSpec(
    agent_id="Agent_09",
    level=3,
    name="Turnover Anomaly",
    perspective="Turnover rate anomaly",
    template_file="prompts/agent_09_lv3_turnover_anomaly.j2",
)

# ────────────────────────────────────────────
# Level 4: Price Behavior (3 agents)
# ────────────────────────────────────────────
_AGENT_10 = AgentSpec(
    agent_id="Agent_10",
    level=4,
    name="Momentum",
    perspective="Momentum persistence",
    template_file="prompts/agent_10_lv4_momentum.j2",
)

_AGENT_11 = AgentSpec(
    agent_id="Agent_11",
    level=4,
    name="Mean Reversion",
    perspective="Short-term mean reversion",
    template_file="prompts/agent_11_lv4_mean_reversion.j2",
)

_AGENT_12 = AgentSpec(
    agent_id="Agent_12",
    level=4,
    name="Vol Clustering",
    perspective="Volatility clustering",
    template_file="prompts/agent_12_lv4_vol_clustering.j2",
)

# ────────────────────────────────────────────
# Level 5: Multi-scale Complexity (3 agents)
# ────────────────────────────────────────────
_AGENT_13 = AgentSpec(
    agent_id="Agent_13",
    level=5,
    name="Drawdown Geometry",
    perspective="Drawdown-recovery geometry",
    template_file="prompts/agent_13_lv5_drawdown_geo.j2",
)

_AGENT_14 = AgentSpec(
    agent_id="Agent_14",
    level=5,
    name="Hurst Exponent",
    perspective="Hurst exponent / long memory",
    template_file="prompts/agent_14_lv5_hurst.j2",
)

_AGENT_15 = AgentSpec(
    agent_id="Agent_15",
    level=5,
    name="DFA",
    perspective="Detrended fluctuation analysis",
    template_file="prompts/agent_15_lv5_dfa.j2",
)

# ────────────────────────────────────────────
# Level 6: Stability & Control (3 agents)
# ────────────────────────────────────────────
_AGENT_16 = AgentSpec(
    agent_id="Agent_16",
    level=6,
    name="Time Stability",
    perspective="Time stability assessment",
    template_file="prompts/agent_16_lv6_time_stability.j2",
)

_AGENT_17 = AgentSpec(
    agent_id="Agent_17",
    level=6,
    name="Adaptive Control",
    perspective="Adaptive control mechanism",
    template_file="prompts/agent_17_lv6_adaptive_ctrl.j2",
)

_AGENT_18 = AgentSpec(
    agent_id="Agent_18",
    level=6,
    name="Signal Gate",
    perspective="Signal activation gating",
    template_file="prompts/agent_18_lv6_signal_gate.j2",
)

# ────────────────────────────────────────────
# Level 7: Geometry & Fusion (3 agents)
# ────────────────────────────────────────────
_AGENT_19 = AgentSpec(
    agent_id="Agent_19",
    level=7,
    name="Candle Pattern",
    perspective="Candlestick pattern recognition",
    template_file="prompts/agent_19_lv7_candle_pattern.j2",
)

_AGENT_20 = AgentSpec(
    agent_id="Agent_20",
    level=7,
    name="Linear Fusion",
    perspective="Multi-factor linear fusion",
    template_file="prompts/agent_20_lv7_linear_fusion.j2",
)

_AGENT_21 = AgentSpec(
    agent_id="Agent_21",
    level=7,
    name="Nonlinear Fusion",
    perspective="Multi-factor nonlinear fusion",
    template_file="prompts/agent_21_lv7_fusion.j2",
)

# ────────────────────────────────────────────
# Registry container
# ────────────────────────────────────────────
_ALL_AGENTS: list[AgentSpec] = [
    _AGENT_01,
    _AGENT_02,
    _AGENT_03,
    _AGENT_04,
    _AGENT_05,
    _AGENT_06,
    _AGENT_07,
    _AGENT_08,
    _AGENT_09,
    _AGENT_10,
    _AGENT_11,
    _AGENT_12,
    _AGENT_13,
    _AGENT_14,
    _AGENT_15,
    _AGENT_16,
    _AGENT_17,
    _AGENT_18,
    _AGENT_19,
    _AGENT_20,
    _AGENT_21,
]

_AGENT_MAP: dict[str, AgentSpec] = {a.agent_id: a for a in _ALL_AGENTS}


def get_all_agents() -> list[AgentSpec]:
    """Return all 21 registered agents."""
    return list(_ALL_AGENTS)


def get_agent_by_id(agent_id: str) -> AgentSpec:
    """Retrieve a single agent by its agent_id.

    Args:
        agent_id: The agent identifier (e.g. "Agent_01").

    Raises:
        KeyError: If the agent_id does not exist in the registry.
    """
    if agent_id not in _AGENT_MAP:
        raise KeyError(f"Agent '{agent_id}' not found in registry.")
    return _AGENT_MAP[agent_id]
