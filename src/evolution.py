"""Evolution engine: selection, crossover, mutation, and generation management."""

from __future__ import annotations

import random
from dataclasses import replace

from .genome import (
    MEMORY_WEIGHTINGS,
    REASONING_STYLES,
    SYSTEM_PROMPT_FRAGMENTS,
    AgentGenome,
)


def aggregate_fitness(results: list[float]) -> float:
    """Aggregate per-task fitness scores into a single generation fitness."""
    if not results:
        return 0.0
    return sum(results) / len(results)


def select_survivors(
    population: list[AgentGenome],
    fitness_scores: dict[str, float],
    survival_rate: float = 0.3,
    elite_count: int = 2,
) -> tuple[list[AgentGenome], list[AgentGenome]]:
    """
    Select survivors from population based on fitness.

    Returns (elites, breeding_pool).
    Elites survive unchanged. Breeding pool used for reproduction.
    """
    ranked = sorted(population, key=lambda g: fitness_scores.get(g.genome_id, 0.0), reverse=True)

    n_survive = max(elite_count, int(len(population) * survival_rate))
    elites = ranked[:elite_count]
    breeding_pool = ranked[:n_survive]

    return elites, breeding_pool


def crossover(parent_a: AgentGenome, parent_b: AgentGenome, generation: int) -> AgentGenome:
    """Combine two parent genomes into a child. Each field randomly chosen from one parent."""
    child = AgentGenome.random(generation=generation)

    # For each evolvable trait, pick from one parent
    child.system_prompt = random.choice([parent_a.system_prompt, parent_b.system_prompt])
    child.reasoning_style = random.choice([parent_a.reasoning_style, parent_b.reasoning_style])
    child.memory_window = random.choice([parent_a.memory_window, parent_b.memory_window])
    child.memory_weighting = random.choice(
        [parent_a.memory_weighting, parent_b.memory_weighting]
    )
    child.confidence_bias = random.choice(
        [parent_a.confidence_bias, parent_b.confidence_bias]
    )
    child.risk_tolerance = random.choice([parent_a.risk_tolerance, parent_b.risk_tolerance])
    child.temperature = random.choice([parent_a.temperature, parent_b.temperature])

    child.parent_ids = [parent_a.genome_id, parent_b.genome_id]
    child.generation = generation

    return child


def mutate(genome: AgentGenome, mutation_rate: float = 0.3) -> AgentGenome:
    """Apply random mutations to a genome. Each trait has mutation_rate chance of changing."""
    g = AgentGenome.from_dict(genome.to_dict())  # copy

    if random.random() < mutation_rate:
        g.system_prompt = random.choice(SYSTEM_PROMPT_FRAGMENTS)

    if random.random() < mutation_rate:
        g.reasoning_style = random.choice(REASONING_STYLES)

    if random.random() < mutation_rate:
        g.memory_window = max(1, g.memory_window + random.randint(-2, 2))

    if random.random() < mutation_rate:
        g.memory_weighting = random.choice(MEMORY_WEIGHTINGS)

    if random.random() < mutation_rate:
        g.confidence_bias = round(
            max(-0.15, min(0.15, g.confidence_bias + random.uniform(-0.05, 0.05))), 2
        )

    if random.random() < mutation_rate:
        g.risk_tolerance = round(
            max(0.0, min(1.0, g.risk_tolerance + random.uniform(-0.15, 0.15))), 2
        )

    if random.random() < mutation_rate:
        g.temperature = round(
            max(0.1, min(1.5, g.temperature + random.uniform(-0.2, 0.2))), 2
        )

    return g


def produce_next_generation(
    population: list[AgentGenome],
    fitness_scores: dict[str, float],
    target_size: int = 10,
    survival_rate: float = 0.3,
    elite_count: int = 2,
    mutation_rate: float = 0.3,
) -> list[AgentGenome]:
    """
    Full evolution step: selection -> crossover -> mutation -> next generation.
    """
    current_gen = max(g.generation for g in population) if population else 0
    next_gen = current_gen + 1

    elites, breeding_pool = select_survivors(
        population, fitness_scores, survival_rate, elite_count
    )

    # Elites survive unchanged but get new IDs for tracking
    next_population: list[AgentGenome] = []
    for elite in elites:
        survivor = AgentGenome.from_dict(elite.to_dict())
        survivor.genome_id = AgentGenome().genome_id  # new ID
        survivor.generation = next_gen
        survivor.parent_ids = [elite.genome_id]
        survivor.fitness_history = list(elite.fitness_history)
        next_population.append(survivor)

    # Fill remaining slots with offspring
    while len(next_population) < target_size:
        parent_a = random.choice(breeding_pool)
        parent_b = random.choice(breeding_pool)
        # avoid self-crossover when possible
        if len(breeding_pool) > 1:
            while parent_b.genome_id == parent_a.genome_id:
                parent_b = random.choice(breeding_pool)

        child = crossover(parent_a, parent_b, next_gen)
        child = mutate(child, mutation_rate)
        next_population.append(child)

    return next_population
