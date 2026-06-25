"""Configuration management for CogAlpha."""

from __future__ import annotations

import os
from pathlib import Path
from typing import Any

import yaml
from pydantic import BaseModel, Field


class LLMConfig(BaseModel):
    """Generic LLM provider configuration."""
    api_key: str = "${API_KEY}"
    base_url: str = ""
    model: str = ""
    max_concurrent_requests: int = 5
    max_tokens: int = 2048
    timeout: int = 60
    temperature: float = 0.7


class APIConfig(BaseModel):
    provider: str = "mock"
    openai: LLMConfig = Field(default_factory=lambda: LLMConfig(
        api_key="${OPENAI_API_KEY}", base_url="https://api.openai.com/v1", model="gpt-4o-mini"
    ))
    deepseek: LLMConfig = Field(default_factory=lambda: LLMConfig(
        api_key="${DEEPSEEK_API_KEY}", base_url="https://api.deepseek.com/v1", model="deepseek-chat"
    ))
    qwen: LLMConfig = Field(default_factory=lambda: LLMConfig(
        api_key="${QWEN_API_KEY}", base_url="https://dashscope.aliyuncs.com/compatible-mode/v1", model="qwen-max"
    ))


class DataConfig(BaseModel):
    path: str = "./data/synthetic_ohlcv.parquet"
    train_start: str = "2011-01-01"
    train_end: str = "2019-12-31"
    test_start: str = "2020-01-01"
    test_end: str = "2025-12-31"
    symbols: list[str] = Field(default_factory=lambda: ["A", "B", "C"])


class EvolutionConfig(BaseModel):
    initial_population_size: int = 8
    parent_pool_size: int = 4
    offspring_multiplier: int = 3
    sub_cycle_generations: int = 8
    total_generations: int = 4
    mutation_rate: float = 0.4
    crossover_rate: float = 0.3
    injection_interval: int = 2
    elite_preserve_num: int = 2


class AgentConfig(BaseModel):
    total_agents: int = 21
    generation_mode_probability: list[float] = Field(default_factory=lambda: [0.2] * 5)
    temperature_range_per_mode: dict[str, list[float]] = Field(default_factory=lambda: {
        "mild": [0.1, 0.3], "moderate": [0.3, 0.5], "creative": [0.5, 0.7],
        "divergent": [0.7, 0.9], "concrete": [0.5, 0.7],
    })
    max_retry_on_error: int = 3


class PathsConfig(BaseModel):
    prompt_templates: str = "./prompts/"
    output_factors: str = "./results/elite_factors/"
    final_library: str = "./results/final_factor_library/"
    logs: str = "./logs/"


class LoggingConfig(BaseModel):
    level: str = "INFO"
    suppress_api_keys: bool = True


class Config(BaseModel):
    api: APIConfig = Field(default_factory=APIConfig)
    data: DataConfig = Field(default_factory=DataConfig)
    evolution: EvolutionConfig = Field(default_factory=EvolutionConfig)
    agent_config: AgentConfig = Field(default_factory=AgentConfig)
    paths: PathsConfig = Field(default_factory=PathsConfig)
    logging: LoggingConfig = Field(default_factory=LoggingConfig)

    def _redact(self, obj: Any) -> Any:
        if isinstance(obj, dict):
            return {k: "***REDACTED***" if "api_key" in k else self._redact(v) for k, v in obj.items()}
        elif isinstance(obj, list):
            return [self._redact(item) for item in obj]
        return obj

    def __str__(self) -> str:
        return f"Config({self._redact(self.model_dump())})"

    __repr__ = __str__


def _resolve_env_vars(obj: Any) -> Any:
    if isinstance(obj, dict):
        return {k: _resolve_env_vars(v) for k, v in obj.items()}
    elif isinstance(obj, list):
        return [_resolve_env_vars(item) for item in obj]
    elif isinstance(obj, str) and obj.startswith("${") and obj.endswith("}"):
        return os.environ.get(obj[2:-1], obj)
    return obj


def load_config(path: str | Path) -> Config:
    path = Path(path)
    if not path.exists():
        raise FileNotFoundError(f"Config file not found: {path}")
    with open(path, "r", encoding="utf-8") as f:
        return Config.model_validate(_resolve_env_vars(yaml.safe_load(f) or {}))
