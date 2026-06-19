"""Evolution loop for CogAlpha MVP."""
from typing import List
from cogalpha.factors.object import FactorObject
from cogalpha.agents.agent import AgentRegistry
from cogalpha.factors.parser import FactorParser


class EvolutionLoop:
    """Simplified evolution loop for the MVP."""

    def __init__(self, config, agents, llm_provider, evaluator):
        self.config = config
        self.agents = agents
        self.llm_provider = llm_provider
        self.evaluator = evaluator
        self.injection_interval = config.get("evolution", {}).get("injection_interval", 2)
        self.mutation_rate = config.get("evolution", {}).get("mutation_rate", 0.4)
        self.crossover_rate = config.get("evolution", {}).get("crossover_rate", 0.3)

    def run_generation(self, generation: int, parent_pool: list) -> list[FactorObject]:
        """Run one generation of the evolution loop."""
        if generation % self.injection_interval == 0:
            # Inject new factors from agents
            raw_outputs = self.agents.generate_batch(batch_size=self.config.get("evolution", {}).get("initial_population_size", 8))
            new_factors = []
            for raw in raw_outputs:
                parsed = FactorParser.parse_to_objects(raw, agent_id="injected")
                new_factors.extend(parsed)
            return new_factors
        else:
            # Mutate and crossover from parent pool (stubs for MVP)
            return self._mutate_and_crossover(parent_pool)

    def _mutate_and_crossover(self, parent_pool: list) -> list[FactorObject]:
        """Stub: mutate and crossover. For MVP, returns a copy of parents."""
        import copy
        return [copy.deepcopy(f) for f in parent_pool]
