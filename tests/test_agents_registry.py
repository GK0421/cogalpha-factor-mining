"""Tests for the CogAlpha agent registry and prompt infrastructure."""

from pathlib import Path

import pytest

from cogalpha.agents.registry import get_all_agents, get_agent_by_id
from cogalpha.agents.prompt_renderer import PromptRenderer, get_mode_temperature


PROJECT_ROOT = Path(__file__).resolve().parents[1]


class TestAgentRegistry:
    """Validate the 21-agent registry structure."""

    def test_get_all_agents_returns_21(self):
        agents = get_all_agents()
        assert len(agents) == 21

    def test_levels_are_1_to_7(self):
        agents = get_all_agents()
        levels = sorted({a.level for a in agents})
        assert levels == list(range(1, 8))

    def test_three_agents_per_level(self):
        agents = get_all_agents()
        for level in range(1, 8):
            level_agents = [a for a in agents if a.level == level]
            assert len(level_agents) == 3, f"Level {level} should have 3 agents"

    def test_agent_ids_are_unique(self):
        agents = get_all_agents()
        ids = [a.agent_id for a in agents]
        assert len(ids) == len(set(ids))

    def test_agent_ids_follow_naming(self):
        agents = get_all_agents()
        for i, agent in enumerate(agents, start=1):
            expected_id = f"Agent_{i:02d}"
            assert agent.agent_id == expected_id

    def test_get_agent_by_id_valid(self):
        agent = get_agent_by_id("Agent_01")
        assert agent.agent_id == "Agent_01"
        assert agent.level == 1

    def test_get_agent_by_id_invalid_raises(self):
        with pytest.raises(KeyError):
            get_agent_by_id("Agent_99")

    def test_all_template_files_exist(self):
        agents = get_all_agents()
        for agent in agents:
            template_path = PROJECT_ROOT / agent.template_file
            assert template_path.exists(), f"Template missing: {agent.template_file}"
            assert template_path.is_file()


class TestPromptRenderer:
    """Validate the prompt rendering pipeline."""

    def test_mode_temperature_values(self):
        assert get_mode_temperature("mild") == 0.3
        assert get_mode_temperature("moderate") == 0.5
        assert get_mode_temperature("creative") == 0.7
        assert get_mode_temperature("divergent") == 0.9
        assert get_mode_temperature("concrete") == 0.2
        assert get_mode_temperature("unknown") == 0.5  # default

    def test_renderer_init_default(self):
        renderer = PromptRenderer()
        assert renderer.template_dir is not None
        assert Path(renderer.template_dir).exists()

    def test_renderer_init_custom(self):
        custom_dir = str(PROJECT_ROOT / "prompts")
        renderer = PromptRenderer(custom_dir)
        assert renderer.template_dir == custom_dir

    def test_render_agent_01(self):
        renderer = PromptRenderer(str(PROJECT_ROOT / "prompts"))
        prompt = renderer.render(
            agent_id="Agent_01",
            mode="moderate",
            invalid_cases="none",
            elite_ideas="none",
        )
        assert "Agent_01" in prompt or "trend" in prompt.lower()
        assert "{{ mode }}" not in prompt  # Jinja variables should be resolved
        assert "{{ temperature }}" not in prompt
        assert "0.5" in prompt  # moderate temperature

    def test_render_all_agents(self):
        renderer = PromptRenderer(str(PROJECT_ROOT / "prompts"))
        for agent in get_all_agents():
            prompt = renderer.render(
                agent_id=agent.agent_id,
                mode="creative",
                invalid_cases="test",
                elite_ideas="test",
            )
            assert len(prompt) > 100
            assert "<function 1>" in prompt
            assert "```python" in prompt


class TestPromptTemplates:
    """Validate the prompt template utilities."""

    def test_base_system_prompt_not_empty(self):
        from cogalpha.agents.prompt_templates import BASE_SYSTEM_PROMPT

        assert len(BASE_SYSTEM_PROMPT) > 50

    def test_mode_descriptions_cover_all_modes(self):
        from cogalpha.agents.prompt_templates import MODE_DESCRIPTIONS

        expected_modes = {"mild", "moderate", "creative", "divergent", "concrete"}
        assert set(MODE_DESCRIPTIONS.keys()) == expected_modes

    def test_build_prompt_payload(self):
        from cogalpha.agents.prompt_templates import build_prompt_payload

        payload = build_prompt_payload(
            agent_id="Agent_01",
            mode="mild",
            invalid_cases="case_a",
            elite_ideas="idea_x",
            temperature=0.3,
        )
        assert payload["agent_id"] == "Agent_01"
        assert payload["mode"] == "mild"
        assert payload["temperature"] == 0.3
        assert "mode_description" in payload
