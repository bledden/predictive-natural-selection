"""W&B Weave observability integration for tracing agent predictions and evolution."""

from __future__ import annotations

import os
from typing import Any

_weave_available = False
_weave_initialized = False

try:
    import weave
    _weave_available = True
except ImportError:
    weave = None


def init_weave(project_name: str = "predictive-natural-selection") -> bool:
    """Initialize Weave. Returns True if successfully initialized."""
    global _weave_initialized
    if not _weave_available:
        return False
    if _weave_initialized:
        return True

    try:
        weave.init(project_name)
        _weave_initialized = True
        return True
    except Exception:
        return False


def trace_agent_prediction(
    genome_id: str,
    generation: int,
    task_id: str,
    task_prompt: str,
    predicted_confidence: float,
    predicted_answer: str,
    ground_truth: str,
    is_correct: bool,
    prediction_accuracy: float,
    fitness: float,
    genome_traits: dict[str, Any] | None = None,
) -> None:
    """Log a single agent prediction+attempt cycle to Weave."""
    if not _weave_initialized or weave is None:
        return

    @weave.op()
    def agent_prediction_cycle(
        genome_id: str,
        generation: int,
        task_id: str,
        task_prompt: str,
        predicted_confidence: float,
        predicted_answer: str,
        ground_truth: str,
        is_correct: bool,
        prediction_accuracy: float,
        fitness: float,
        genome_traits: dict | None = None,
    ) -> dict:
        return {
            "genome_id": genome_id,
            "generation": generation,
            "task_id": task_id,
            "predicted_confidence": predicted_confidence,
            "predicted_answer": predicted_answer,
            "ground_truth": ground_truth,
            "is_correct": is_correct,
            "prediction_accuracy": prediction_accuracy,
            "fitness": fitness,
            "genome_traits": genome_traits or {},
        }

    try:
        agent_prediction_cycle(
            genome_id=genome_id,
            generation=generation,
            task_id=task_id,
            task_prompt=task_prompt,
            predicted_confidence=predicted_confidence,
            predicted_answer=predicted_answer,
            ground_truth=ground_truth,
            is_correct=is_correct,
            prediction_accuracy=prediction_accuracy,
            fitness=fitness,
            genome_traits=genome_traits,
        )
    except Exception:
        pass  # don't let tracing failures break the evolution


def trace_generation_summary(
    generation: int,
    population_size: int,
    avg_fitness: float,
    best_fitness: float,
    avg_prediction_accuracy: float,
    avg_task_accuracy: float,
    dominant_reasoning: str,
    dominant_memory: str,
) -> None:
    """Log generation-level summary to Weave."""
    if not _weave_initialized or weave is None:
        return

    @weave.op()
    def generation_summary(
        generation: int,
        population_size: int,
        avg_fitness: float,
        best_fitness: float,
        avg_prediction_accuracy: float,
        avg_task_accuracy: float,
        dominant_reasoning: str,
        dominant_memory: str,
    ) -> dict:
        return {
            "generation": generation,
            "population_size": population_size,
            "avg_fitness": avg_fitness,
            "best_fitness": best_fitness,
            "avg_prediction_accuracy": avg_prediction_accuracy,
            "avg_task_accuracy": avg_task_accuracy,
            "dominant_reasoning": dominant_reasoning,
            "dominant_memory": dominant_memory,
        }

    try:
        generation_summary(
            generation=generation,
            population_size=population_size,
            avg_fitness=avg_fitness,
            best_fitness=best_fitness,
            avg_prediction_accuracy=avg_prediction_accuracy,
            avg_task_accuracy=avg_task_accuracy,
            dominant_reasoning=dominant_reasoning,
            dominant_memory=dominant_memory,
        )
    except Exception:
        pass


def trace_evolution_complete(
    total_generations: int,
    initial_avg_fitness: float,
    final_avg_fitness: float,
    improvement: float,
    dominant_strategy: str,
    extinct_strategies: list[str],
) -> None:
    """Log the final evolution summary to Weave."""
    if not _weave_initialized or weave is None:
        return

    @weave.op()
    def evolution_complete(
        total_generations: int,
        initial_avg_fitness: float,
        final_avg_fitness: float,
        improvement: float,
        dominant_strategy: str,
        extinct_strategies: list[str],
    ) -> dict:
        return {
            "total_generations": total_generations,
            "initial_avg_fitness": initial_avg_fitness,
            "final_avg_fitness": final_avg_fitness,
            "improvement": improvement,
            "dominant_strategy": dominant_strategy,
            "extinct_strategies": extinct_strategies,
        }

    try:
        evolution_complete(
            total_generations=total_generations,
            initial_avg_fitness=initial_avg_fitness,
            final_avg_fitness=final_avg_fitness,
            improvement=improvement,
            dominant_strategy=dominant_strategy,
            extinct_strategies=extinct_strategies,
        )
    except Exception:
        pass
