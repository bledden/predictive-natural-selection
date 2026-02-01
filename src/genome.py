"""AgentGenome: the evolving DNA of each LLM agent."""

from __future__ import annotations

import random
import uuid
from dataclasses import dataclass, field
from typing import Any

REASONING_STYLES = [
    "chain-of-thought",
    "step-by-step",
    "analogical",
    "debate-self",
    "first-principles",
    "elimination",
]

MEMORY_WEIGHTINGS = ["recency", "relevance", "success-rate"]

SYSTEM_PROMPT_FRAGMENTS = [
    "You are a careful, methodical thinker who checks each step.",
    "You are a bold, intuitive reasoner who trusts your first instinct.",
    "You think by analogy — relate new problems to ones you know.",
    "You argue with yourself, considering multiple viewpoints before deciding.",
    "You break every problem down to its fundamental principles.",
    "You reason by eliminating wrong answers first.",
    "You are a calibrated predictor who honestly assesses uncertainty.",
    "You are a pattern-matcher who looks for structural similarity.",
    "You think probabilistically, always estimating likelihoods.",
    "You are a devil's advocate who stress-tests your own reasoning.",
]


@dataclass
class AgentGenome:
    genome_id: str = field(default_factory=lambda: uuid.uuid4().hex[:8])
    system_prompt: str = ""
    reasoning_style: str = "chain-of-thought"
    memory_window: int = 5
    memory_weighting: str = "recency"
    confidence_bias: float = 0.0  # -0.3 to +0.3, adjusts reported confidence
    risk_tolerance: float = 0.5  # 0.0 to 1.0
    temperature: float = 0.7  # LLM temperature
    generation: int = 0
    parent_ids: list[str] = field(default_factory=list)
    fitness_history: list[float] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "genome_id": self.genome_id,
            "system_prompt": self.system_prompt,
            "reasoning_style": self.reasoning_style,
            "memory_window": self.memory_window,
            "memory_weighting": self.memory_weighting,
            "confidence_bias": self.confidence_bias,
            "risk_tolerance": self.risk_tolerance,
            "temperature": self.temperature,
            "generation": self.generation,
            "parent_ids": self.parent_ids,
            "fitness_history": self.fitness_history,
        }

    @classmethod
    def from_dict(cls, d: dict[str, Any]) -> AgentGenome:
        return cls(**{k: v for k, v in d.items() if k in cls.__dataclass_fields__})

    @classmethod
    def random(cls, generation: int = 0) -> AgentGenome:
        return cls(
            system_prompt=random.choice(SYSTEM_PROMPT_FRAGMENTS),
            reasoning_style=random.choice(REASONING_STYLES),
            memory_window=random.randint(1, 10),
            memory_weighting=random.choice(MEMORY_WEIGHTINGS),
            confidence_bias=round(random.uniform(-0.3, 0.3), 2),
            risk_tolerance=round(random.uniform(0.1, 0.9), 2),
            temperature=round(random.uniform(0.3, 1.2), 2),
            generation=generation,
        )

    def build_system_message(self) -> str:
        return (
            f"{self.system_prompt}\n\n"
            f"Reasoning approach: {self.reasoning_style}.\n"
            f"Consider the last {self.memory_window} results when relevant.\n"
            f"Prioritize information by: {self.memory_weighting}.\n"
        )
