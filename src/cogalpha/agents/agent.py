"""Agent registry for CogAlpha."""
from cogalpha.llm.mock_provider import MockLLMProvider


class AgentRegistry:
    """Simple registry of agents that generate factors."""

    def __init__(self, num_agents: int = 21, llm_provider=None):
        self.num_agents = num_agents
        self.llm_provider = llm_provider or MockLLMProvider()

    def generate_batch(self, batch_size: int = 4) -> list[str]:
        """Generate a batch of raw factor strings from agents."""
        return self.llm_provider.generate_factors(n=batch_size)
