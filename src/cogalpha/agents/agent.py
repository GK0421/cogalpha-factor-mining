"""Agent registry for CogAlpha."""
import random

from cogalpha.llm.mock_provider import MockLLMProvider
from .prompt_renderer import PromptRenderer
from .registry import get_all_agents


class AgentRegistry:
    """Simple registry of agents that generate factors."""

    def __init__(self, num_agents: int = 21, llm_provider=None):
        self.num_agents = num_agents
        self.llm_provider = llm_provider or MockLLMProvider()
        self.prompt_renderer = PromptRenderer()

    def generate_batch(self, batch_size: int = 4) -> list[str]:
        """Generate a batch of raw factor strings from agents.

        Uses the configured LLM provider. If the provider is a MockLLMProvider,
        uses its generate_factors() helper. Otherwise, renders a proper prompt
        for a randomly chosen agent and calls generate_sync().
        """
        # Check if this is the mock provider (has generate_factors method)
        if hasattr(self.llm_provider, 'generate_factors'):
            return self.llm_provider.generate_factors(n=batch_size)

        # Real LLM provider: render prompt and call generate_sync
        agents = get_all_agents()
        raw_outputs = []
        modes = ["mild", "moderate", "creative", "divergent", "concrete"]

        for _ in range(batch_size):
            agent = random.choice(agents)
            mode = random.choice(modes)
            prompt = self.prompt_renderer.render(
                agent_id=agent.agent_id,
                mode=mode,
                invalid_cases="None yet",
                elite_ideas="None yet",
            )
            try:
                response = self.llm_provider.generate_sync(
                    prompt=prompt,
                    temperature=random.uniform(0.2, 0.9),
                    max_tokens=2048,
                    timeout=60,
                )
                raw_outputs.append(response)
            except Exception as e:
                print(f"[WARN] LLM generation failed for {agent.agent_id}: {e}")
                continue

        return raw_outputs
