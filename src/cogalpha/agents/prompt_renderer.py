"""Jinja2 prompt renderer for CogAlpha agent templates."""

from __future__ import annotations

import os
from pathlib import Path

from jinja2 import Environment, FileSystemLoader, TemplateNotFound

from .prompt_templates import compose_system_prompt, build_prompt_payload


# Default mode-to-temperature mapping.
_MODE_TEMPERATURE_MAP = {
    "mild": 0.3,
    "moderate": 0.5,
    "creative": 0.7,
    "divergent": 0.9,
    "concrete": 0.2,
}


def get_mode_temperature(mode: str) -> float:
    """Return the target temperature for a given generation mode.

    Args:
        mode: One of mild, moderate, creative, divergent, concrete.

    Returns:
        Temperature value between 0.0 and 1.0.
    """
    return _MODE_TEMPERATURE_MAP.get(mode, 0.5)


class PromptRenderer:
    """Renders agent-specific Jinja2 prompt templates."""

    def __init__(self, template_dir: str | None = None):
        """Initialize the renderer with a Jinja2 environment.

        Args:
            template_dir: Directory containing .j2 template files. Defaults to
                the project's prompts/ directory relative to this file.
        """
        if template_dir is None:
            # Walk up to project root and then into prompts/
            project_root = Path(__file__).resolve().parents[3]
            template_dir = str(project_root / "prompts")
        self.template_dir = template_dir
        self._env = Environment(
            loader=FileSystemLoader(template_dir),
            trim_blocks=True,
            lstrip_blocks=True,
        )

    def render(
        self,
        agent_id: str,
        mode: str,
        invalid_cases: str,
        elite_ideas: str,
    ) -> str:
        """Render a complete prompt for the specified agent.

        Args:
            agent_id: Agent identifier (e.g. "Agent_01").
            mode: Generation mode (mild, moderate, creative, divergent, concrete).
            invalid_cases: Summary of previously failed/invalid factor ideas.
            elite_ideas: Brief summary of elite factor ideas.

        Returns:
            The fully rendered prompt string.

        Raises:
            TemplateNotFound: If the agent's template file is missing.
        """
        temperature = get_mode_temperature(mode)
        payload = build_prompt_payload(agent_id, mode, invalid_cases, elite_ideas, temperature)

        # Determine template file from agent_id
        from .registry import get_agent_by_id

        agent = get_agent_by_id(agent_id)
        template_name = os.path.basename(agent.template_file)

        template = self._env.get_template(template_name)
        rendered = template.render(**payload)

        # Prepend base system prompt
        system_prompt = compose_system_prompt(mode)
        return f"{system_prompt}\n\n---\n\n{rendered}"
