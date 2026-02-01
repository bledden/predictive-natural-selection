"""Main entry point: CLI for running evolutionary simulations."""

from __future__ import annotations

import asyncio
import json
import os
import sys
from pathlib import Path

import typer
from rich.console import Console

app = typer.Typer(name="evolve", help="Predictive Natural Selection — evolve LLM agent strategies")
console = Console()


@app.command()
def run(
    population: int = typer.Option(10, "--population", "-p", help="Population size"),
    generations: int = typer.Option(15, "--generations", "-g", help="Number of generations"),
    tasks: int = typer.Option(8, "--tasks", "-t", help="Tasks per generation"),
    concurrency: int = typer.Option(10, "--concurrency", "-c", help="Max concurrent LLM calls"),
    mutation_rate: float = typer.Option(0.3, "--mutation-rate", "-m", help="Mutation rate (0-1)"),
    seed: int = typer.Option(42, "--seed", "-s", help="Random seed for task selection and reproducibility"),
    model: str = typer.Option("gpt-4o-mini", "--model", envvar="MODEL_NAME", help="LLM model name"),
    base_url: str = typer.Option(None, "--base-url", envvar="OPENAI_BASE_URL", help="OpenAI-compatible API base URL"),
    api_key: str = typer.Option(None, "--api-key", envvar="OPENAI_API_KEY", help="API key (or set env var)"),
    redis_url: str = typer.Option("redis://localhost:6379/0", "--redis-url", envvar="REDIS_URL"),
    weave_project: str = typer.Option("predictive-natural-selection", "--weave-project"),
    no_weave: bool = typer.Option(False, "--no-weave", help="Disable Weave tracing"),
    output_dir: str = typer.Option("data", "--output-dir", "-o", help="Output directory for plots"),
):
    """Run a full evolutionary simulation.

    The seed parameter controls task selection and train/test split for reproducibility.
    Running with the same seed will produce comparable results across runs.

    Supports any OpenAI-compatible API. Examples:
      # OpenAI
      evolve run --model gpt-4o-mini

      # Gemini
      evolve run --model gemini-2.5-flash-lite --base-url https://generativelanguage.googleapis.com/v1beta/openai/ --api-key $GEMINI_API_KEY

      # Local ollama
      evolve run --model llama3.3 --base-url http://localhost:11434/v1 --api-key ollama

      # OpenRouter
      evolve run --model google/gemini-2.5-flash-lite --base-url https://openrouter.ai/api/v1 --api-key $OPENROUTER_API_KEY
    """
    asyncio.run(_run_async(
        population_size=population,
        num_generations=generations,
        tasks_per_gen=tasks,
        concurrency=concurrency,
        mutation_rate=mutation_rate,
        model=model,
        base_url=base_url,
        api_key=api_key,
        redis_url=redis_url,
        weave_project=weave_project,
        no_weave=no_weave,
        output_dir=output_dir,
    ))


async def _run_async(
    population_size: int,
    num_generations: int,
    tasks_per_gen: int,
    concurrency: int,
    mutation_rate: float,
    model: str,
    base_url: str | None,
    api_key: str | None,
    redis_url: str,
    weave_project: str,
    no_weave: bool,
    output_dir: str,
):
    from .evaluator import configure_client
    from .orchestrator import run_evolution
    from .population_store import PopulationStore
    from .visualization import generate_all_plots, generate_summary
    from .weave_integration import init_weave, trace_evolution_complete, trace_generation_summary

    # configure LLM client
    configure_client(model=model, base_url=base_url, api_key=api_key)
    console.print(f"[green]Model:[/green] {model}")
    if base_url:
        console.print(f"[green]API Base:[/green] {base_url}")

    # init Weave
    weave_enabled = False
    if not no_weave:
        weave_enabled = init_weave(weave_project)
        if weave_enabled:
            console.print("[green]Weave tracing enabled[/green]")
        else:
            console.print("[yellow]Weave not available — running without tracing[/yellow]")

    # init Redis store
    store = PopulationStore(redis_url)
    try:
        # verify Redis connection
        await store.r.ping()
        console.print(f"[green]Connected to Redis at {redis_url}[/green]")
    except Exception as e:
        console.print(f"[red]Failed to connect to Redis: {e}[/red]")
        console.print("[yellow]Make sure Redis is running: brew services start redis[/yellow]")
        sys.exit(1)

    try:
        # run evolution
        evolution_run = await run_evolution(
            store=store,
            population_size=population_size,
            num_generations=num_generations,
            tasks_per_generation=tasks_per_gen,
            concurrency=concurrency,
            mutation_rate=mutation_rate,
            weave_enabled=weave_enabled,
            run_seed=seed,
        )

        # log to Weave
        if weave_enabled and evolution_run.generation_stats:
            for stats in evolution_run.generation_stats:
                trace_generation_summary(
                    generation=stats.generation,
                    population_size=stats.population_size,
                    avg_fitness=stats.avg_fitness,
                    best_fitness=stats.best_fitness,
                    avg_prediction_accuracy=stats.avg_prediction_accuracy,
                    avg_task_accuracy=stats.avg_task_accuracy,
                    dominant_reasoning=stats.dominant_reasoning,
                    dominant_memory=stats.dominant_memory,
                )

            first = evolution_run.generation_stats[0]
            last = evolution_run.generation_stats[-1]
            # find extinct strategies
            initial_styles = set(
                g["reasoning_style"] for g in evolution_run.all_genomes if g["generation"] == 0
            )
            final_styles = set(
                g["reasoning_style"]
                for g in evolution_run.all_genomes
                if g["generation"] == last.generation
            )
            trace_evolution_complete(
                total_generations=last.generation + 1,
                initial_avg_fitness=first.avg_fitness,
                final_avg_fitness=last.avg_fitness,
                improvement=last.avg_fitness - first.avg_fitness,
                dominant_strategy=last.dominant_reasoning,
                extinct_strategies=list(initial_styles - final_styles),
            )

        # generate visualizations
        console.print("\n[bold cyan]Generating visualizations...[/bold cyan]")
        paths = generate_all_plots(evolution_run, output_dir)
        for p in paths:
            console.print(f"  [green]Saved:[/green] {p}")

        # generate and print summary
        summary = generate_summary(evolution_run)
        console.print(f"\n{summary}")

        # save run data as JSON
        run_data_path = f"{output_dir}/evolution_run.json"
        Path(output_dir).mkdir(parents=True, exist_ok=True)
        with open(run_data_path, "w") as f:
            json.dump({
                "generation_stats": [
                    {
                        "generation": s.generation,
                        "population_size": s.population_size,
                        "avg_fitness": s.avg_fitness,
                        "best_fitness": s.best_fitness,
                        "worst_fitness": s.worst_fitness,
                        "avg_raw_calibration": s.avg_raw_calibration,
                        "avg_prediction_accuracy": s.avg_prediction_accuracy,
                        "avg_task_accuracy": s.avg_task_accuracy,
                        "dominant_reasoning": s.dominant_reasoning,
                        "dominant_memory": s.dominant_memory,
                        "elapsed_seconds": s.elapsed_seconds,
                    }
                    for s in evolution_run.generation_stats
                ],
                "all_genomes": evolution_run.all_genomes,
                "all_results": evolution_run.all_results,
                "test_results": evolution_run.test_results,
            }, f, indent=2)
        console.print(f"\n[green]Run data saved to {run_data_path}[/green]")

        # Print test set summary
        if evolution_run.test_results:
            console.print(f"\n[bold cyan]═══ Test Set Performance (Held-Out Data) ═══[/bold cyan]")
            console.print(f"  Tasks evaluated: {evolution_run.test_results.get('n_tasks', 0)}")
            console.print(f"  Raw calibration: {evolution_run.test_results.get('avg_raw_calibration', 0):.1%}")
            console.print(f"  Evolved calibration: {evolution_run.test_results.get('avg_prediction_accuracy', 0):.1%}")
            console.print(f"  Task accuracy: {evolution_run.test_results.get('avg_task_accuracy', 0):.1%}")
            console.print(f"  Best fitness: {evolution_run.test_results.get('best_fitness', 0):.3f}")

    finally:
        await store.close()


@app.command()
def visualize(
    data_path: str = typer.Argument("data/evolution_run.json", help="Path to evolution run JSON"),
    output_dir: str = typer.Option("data", "--output-dir", "-o"),
):
    """Regenerate visualizations from a saved evolution run."""
    from .orchestrator import EvolutionRun, GenerationStats
    from .visualization import generate_all_plots, generate_summary

    with open(data_path) as f:
        data = json.load(f)

    run = EvolutionRun()
    run.all_genomes = data.get("all_genomes", [])
    run.generation_stats = []
    for s in data.get("generation_stats", []):
        # backfill avg_raw_calibration for older runs that don't have it
        if "avg_raw_calibration" not in s:
            s["avg_raw_calibration"] = s.get("avg_prediction_accuracy", 0.0)
        run.generation_stats.append(GenerationStats(**s))
    run.all_results = data.get("all_results", [])

    paths = generate_all_plots(run, output_dir)
    for p in paths:
        console.print(f"  [green]Saved:[/green] {p}")

    summary = generate_summary(run)
    console.print(f"\n{summary}")


if __name__ == "__main__":
    app()
