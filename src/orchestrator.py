"""Orchestrator: runs the full evolutionary loop across generations."""

from __future__ import annotations

import asyncio
import time
from dataclasses import dataclass, field
from typing import Any

from rich.console import Console
from rich.table import Table

from .evaluator import EvalResult, run_generation_tasks
from .evolution import aggregate_fitness, produce_next_generation
from .genome import AgentGenome
from .population_store import PopulationStore
from .tasks import get_rotating_task_batch, get_train_val_test_split
from .weave_integration import trace_agent_prediction

console = Console()


@dataclass
class GenerationStats:
    generation: int
    population_size: int
    avg_fitness: float
    best_fitness: float
    worst_fitness: float
    avg_raw_calibration: float  # LLM's own confidence vs outcome, no bias
    avg_prediction_accuracy: float  # with confidence_bias applied
    avg_task_accuracy: float
    dominant_reasoning: str
    dominant_memory: str
    elapsed_seconds: float


@dataclass
class EvolutionRun:
    run_id: str = ""
    generation_stats: list[GenerationStats] = field(default_factory=list)
    all_genomes: list[dict[str, Any]] = field(default_factory=list)
    all_results: list[dict[str, Any]] = field(default_factory=list)
    test_results: dict[str, Any] = field(default_factory=dict)  # Final test set evaluation


def _compute_gen_stats(
    gen: int,
    population: list[AgentGenome],
    results: dict[str, list[EvalResult]],
    fitness_scores: dict[str, float],
    elapsed: float,
) -> GenerationStats:
    fitnesses = list(fitness_scores.values())
    all_eval_results = [r for rs in results.values() for r in rs]

    # count dominant traits
    reasoning_counts: dict[str, int] = {}
    memory_counts: dict[str, int] = {}
    for g in population:
        reasoning_counts[g.reasoning_style] = reasoning_counts.get(g.reasoning_style, 0) + 1
        memory_counts[g.memory_weighting] = memory_counts.get(g.memory_weighting, 0) + 1

    return GenerationStats(
        generation=gen,
        population_size=len(population),
        avg_fitness=sum(fitnesses) / len(fitnesses) if fitnesses else 0,
        best_fitness=max(fitnesses) if fitnesses else 0,
        worst_fitness=min(fitnesses) if fitnesses else 0,
        avg_raw_calibration=(
            sum(r.raw_calibration for r in all_eval_results) / len(all_eval_results)
            if all_eval_results
            else 0
        ),
        avg_prediction_accuracy=(
            sum(r.prediction_accuracy for r in all_eval_results) / len(all_eval_results)
            if all_eval_results
            else 0
        ),
        avg_task_accuracy=(
            sum(1 for r in all_eval_results if r.is_correct) / len(all_eval_results)
            if all_eval_results
            else 0
        ),
        dominant_reasoning=max(reasoning_counts, key=reasoning_counts.get) if reasoning_counts else "unknown",
        dominant_memory=max(memory_counts, key=memory_counts.get) if memory_counts else "unknown",
        elapsed_seconds=elapsed,
    )


def _print_gen_stats(stats: GenerationStats) -> None:
    table = Table(title=f"Generation {stats.generation}")
    table.add_column("Metric", style="cyan")
    table.add_column("Value", style="green")

    table.add_row("Population", str(stats.population_size))
    table.add_row("Avg Fitness", f"{stats.avg_fitness:.3f}")
    table.add_row("Best Fitness", f"{stats.best_fitness:.3f}")
    table.add_row("Worst Fitness", f"{stats.worst_fitness:.3f}")
    table.add_row("Raw Calibration", f"{stats.avg_raw_calibration:.1%}")
    table.add_row("Adjusted Calibration", f"{stats.avg_prediction_accuracy:.1%}")
    table.add_row("Task Accuracy", f"{stats.avg_task_accuracy:.1%}")
    table.add_row("Dominant Reasoning", stats.dominant_reasoning)
    table.add_row("Dominant Memory", stats.dominant_memory)
    table.add_row("Time", f"{stats.elapsed_seconds:.1f}s")

    console.print(table)


async def evaluate_on_test_set(
    population: list[AgentGenome],
    run_seed: int = 42,
    concurrency: int = 10,
) -> dict[str, Any]:
    """Evaluate final population on held-out test set.

    This provides an unbiased estimate of generalization performance.
    Test tasks were NEVER seen during evolution.
    """
    # Get test tasks (never seen during training)
    _, _, test_tasks = get_train_val_test_split(run_seed)

    console.print(f"  Test set size: {len(test_tasks)} tasks")

    # Evaluate all agents on test tasks
    results = await run_generation_tasks(population, test_tasks, concurrency=concurrency)

    # Compute aggregate metrics
    all_eval_results = [r for rs in results.values() for r in rs]
    fitness_scores = {
        genome.genome_id: aggregate_fitness([r.fitness for r in results.get(genome.genome_id, [])])
        for genome in population
    }

    return {
        "n_tasks": len(test_tasks),
        "n_agents": len(population),
        "avg_raw_calibration": (
            sum(r.raw_calibration for r in all_eval_results) / len(all_eval_results)
            if all_eval_results else 0
        ),
        "avg_prediction_accuracy": (
            sum(r.prediction_accuracy for r in all_eval_results) / len(all_eval_results)
            if all_eval_results else 0
        ),
        "avg_task_accuracy": (
            sum(1 for r in all_eval_results if r.is_correct) / len(all_eval_results)
            if all_eval_results else 0
        ),
        "best_fitness": max(fitness_scores.values()) if fitness_scores else 0,
        "avg_fitness": sum(fitness_scores.values()) / len(fitness_scores) if fitness_scores else 0,
    }


async def run_evolution(
    store: PopulationStore,
    population_size: int = 10,
    num_generations: int = 15,
    tasks_per_generation: int = 15,
    concurrency: int = 10,
    mutation_rate: float = 0.3,
    survival_rate: float = 0.3,
    elite_count: int = 2,
    weave_enabled: bool = False,
    run_seed: int = 42,
) -> EvolutionRun:
    """Run a full evolutionary loop.

    Args:
        run_seed: Random seed for task selection and train/test split (default 42)
    """
    run = EvolutionRun()

    await store.clear_all()
    console.print(f"\n[bold magenta]Starting Evolution[/bold magenta]")
    console.print(f"Population: {population_size} | Generations: {num_generations} | Tasks/gen: {tasks_per_generation} | Seed: {run_seed}\n")

    # ── Generation 0: random population ────────────────────────
    population = [AgentGenome.random(generation=0) for _ in range(population_size)]
    for g in population:
        await store.save_genome(g)
        run.all_genomes.append(g.to_dict())

    # ── Evolution loop ─────────────────────────────────────────
    for gen in range(num_generations):
        t0 = time.time()
        console.print(f"\n[bold cyan]── Generation {gen} ──[/bold cyan]")

        # TRAINING tasks only — rotated per generation to prevent overfitting
        tasks = get_rotating_task_batch(n=tasks_per_generation, generation=gen, run_seed=run_seed)

        # run all agents on all tasks
        results = await run_generation_tasks(population, tasks, concurrency=concurrency)

        # compute per-agent fitness
        fitness_scores: dict[str, float] = {}
        for genome in population:
            agent_results = results.get(genome.genome_id, [])
            per_task_fitness = [r.fitness for r in agent_results]
            fitness = aggregate_fitness(per_task_fitness)
            fitness_scores[genome.genome_id] = fitness
            await store.record_fitness(genome.genome_id, gen, fitness)

            # store individual results and trace to Weave
            task_lookup = {t.task_id: t for t in tasks}
            for r in agent_results:
                run.all_results.append({
                    "generation": gen,
                    "genome_id": r.genome_id,
                    "task_id": r.task_id,
                    "predicted_confidence": r.predicted_confidence,
                    "predicted_answer": r.predicted_answer,
                    "ground_truth": r.ground_truth,
                    "is_correct": r.is_correct,
                    "raw_calibration": r.raw_calibration,
                    "prediction_accuracy": r.prediction_accuracy,
                    "fitness": r.fitness,
                })
                if weave_enabled:
                    task_obj = task_lookup.get(r.task_id)
                    trace_agent_prediction(
                        genome_id=r.genome_id,
                        generation=gen,
                        task_id=r.task_id,
                        task_prompt=task_obj.prompt if task_obj else "",
                        predicted_confidence=r.predicted_confidence,
                        predicted_answer=r.predicted_answer,
                        ground_truth=r.ground_truth,
                        is_correct=r.is_correct,
                        prediction_accuracy=r.prediction_accuracy,
                        fitness=r.fitness,
                        genome_traits=genome.to_dict(),
                    )

        elapsed = time.time() - t0

        # compute and display stats
        stats = _compute_gen_stats(gen, population, results, fitness_scores, elapsed)
        run.generation_stats.append(stats)
        _print_gen_stats(stats)

        # evolve (skip on last generation)
        if gen < num_generations - 1:
            population = produce_next_generation(
                population,
                fitness_scores,
                target_size=population_size,
                survival_rate=survival_rate,
                elite_count=elite_count,
                mutation_rate=mutation_rate,
            )
            for g in population:
                await store.save_genome(g)
                await store.record_lineage(g.genome_id, g.parent_ids)
                run.all_genomes.append(g.to_dict())

        await store.set_current_generation(gen)

    console.print(f"\n[bold green]Evolution complete![/bold green]")

    # ── Final Test Set Evaluation ──────────────────────────────
    console.print(f"\n[bold yellow]Evaluating on held-out test set...[/bold yellow]")
    test_results = await evaluate_on_test_set(population, run_seed=run_seed, concurrency=concurrency)
    run.test_results = test_results

    console.print(f"\n[bold cyan]Test Set Results:[/bold cyan]")
    console.print(f"  Raw Calibration: {test_results['avg_raw_calibration']:.1%}")
    console.print(f"  Evolved Calibration: {test_results['avg_prediction_accuracy']:.1%}")
    console.print(f"  Task Accuracy: {test_results['avg_task_accuracy']:.1%}")
    console.print(f"  Best Individual Fitness: {test_results['best_fitness']:.3f}")

    return run
