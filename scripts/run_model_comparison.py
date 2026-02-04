#!/usr/bin/env python3
"""Run evolutionary experiments across a spectrum of model sizes.

Produces data for the research question:
  "At what model capability level does system optimization stop producing real gains?"

Each model is run with 3 seeds for statistical robustness.
Results are saved to data/model_comparison/<model_slug>_seed<N>/evolution_run.json

Usage:
  python scripts/run_model_comparison.py              # all models
  python scripts/run_model_comparison.py --model phi4  # single model by slug
  python scripts/run_model_comparison.py --resume      # skip completed runs
"""

from __future__ import annotations

import argparse
import asyncio
import json
import os
import sys
import time
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from rich.console import Console
from rich.table import Table

console = Console()

# ── Model spectrum: small → large ───────────────────────────────────────
MODELS = [
    {
        "slug": "phi4_mini",
        "model_id": "microsoft/Phi-4-mini-instruct",
        "params": "3.8B",
        "category": "small",
    },
    {
        "slug": "llama31_8b",
        "model_id": "meta-llama/Llama-3.1-8B-Instruct",
        "params": "8B",
        "category": "small",
    },
    {
        "slug": "qwen25_14b",
        "model_id": "Qwen/Qwen2.5-14B-Instruct",
        "params": "14B",
        "category": "small",
    },
    {
        "slug": "gpt_oss_20b",
        "model_id": "openai/gpt-oss-20b",
        "params": "20B MoE",
        "category": "medium",
    },
    {
        "slug": "llama33_70b",
        "model_id": "meta-llama/Llama-3.3-70B-Instruct",
        "params": "70B",
        "category": "medium",
    },
    {
        "slug": "deepseek_v3_1",
        "model_id": "deepseek-ai/DeepSeek-V3.1",
        "params": "671B MoE",
        "category": "large",
    },
]

SEEDS = [42, 43, 44]
OUTPUT_BASE = Path(__file__).resolve().parent.parent / "data" / "model_comparison"

# Evolution parameters — same for all models for fair comparison
POPULATION = 10
GENERATIONS = 15
TASKS_PER_GEN = 15
CONCURRENCY = 10
MUTATION_RATE = 0.3


async def run_single_experiment(
    model_id: str,
    slug: str,
    seed: int,
    output_dir: Path,
    log_path: Path,
) -> dict | None:
    """Run a single evolution experiment and return summary stats."""
    from src.evaluator import configure_client
    from src.orchestrator import EvolutionRun, run_evolution
    from src.population_store import PopulationStore
    from src.tasks import set_task_pool, ALL_TASKS

    # Reset task pool to built-in defaults (in case a previous run modified it)
    set_task_pool(list(ALL_TASKS))

    # Configure LLM
    api_key = os.environ.get("WANDB_API_KEY", os.environ.get("OPENAI_API_KEY", ""))
    base_url = os.environ.get("OPENAI_BASE_URL", "https://api.inference.wandb.ai/v1")
    configure_client(model=model_id, base_url=base_url, api_key=api_key)

    # Redis store
    store = PopulationStore("redis://localhost:6379/0")
    try:
        await store.r.ping()
    except Exception as e:
        console.print(f"[red]Redis connection failed: {e}[/red]")
        return None

    try:
        await store.clear_all()

        t0 = time.time()
        run = await run_evolution(
            store=store,
            population_size=POPULATION,
            num_generations=GENERATIONS,
            tasks_per_generation=TASKS_PER_GEN,
            concurrency=CONCURRENCY,
            mutation_rate=MUTATION_RATE,
            run_seed=seed,
        )
        elapsed = time.time() - t0

        # Save full run data
        output_dir.mkdir(parents=True, exist_ok=True)
        run_data = {
            "model": model_id,
            "slug": slug,
            "seed": seed,
            "elapsed_seconds": elapsed,
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
                for s in run.generation_stats
            ],
            "all_genomes": run.all_genomes,
            "all_results": run.all_results,
            "test_results": run.test_results,
        }

        with open(output_dir / "evolution_run.json", "w") as f:
            json.dump(run_data, f, indent=2)

        # Extract summary
        first = run.generation_stats[0]
        last = run.generation_stats[-1]
        test = run.test_results or {}

        summary = {
            "model": model_id,
            "slug": slug,
            "seed": seed,
            "elapsed_seconds": round(elapsed, 1),
            "training": {
                "initial_raw_cal": first.avg_raw_calibration,
                "final_raw_cal": last.avg_raw_calibration,
                "initial_evolved_cal": first.avg_prediction_accuracy,
                "final_evolved_cal": last.avg_prediction_accuracy,
                "gap": last.avg_prediction_accuracy - last.avg_raw_calibration,
                "initial_task_acc": first.avg_task_accuracy,
                "final_task_acc": last.avg_task_accuracy,
                "initial_fitness": first.avg_fitness,
                "final_fitness": last.avg_fitness,
            },
            "test": {
                "raw_cal": test.get("avg_raw_calibration", 0),
                "evolved_cal": test.get("avg_prediction_accuracy", 0),
                "gap": test.get("avg_prediction_accuracy", 0) - test.get("avg_raw_calibration", 0),
                "task_acc": test.get("avg_task_accuracy", 0),
                "best_fitness": test.get("best_fitness", 0),
            },
            "dominant_strategy": last.dominant_reasoning,
        }

        with open(output_dir / "summary.json", "w") as f:
            json.dump(summary, f, indent=2)

        return summary

    finally:
        await store.close()


async def run_all_experiments(models: list[dict], resume: bool = False):
    """Run experiments for all models across all seeds."""
    all_summaries: list[dict] = []
    total_runs = len(models) * len(SEEDS)
    completed = 0

    console.print(f"\n[bold cyan]{'='*60}[/bold cyan]")
    console.print(f"[bold cyan]  Multi-Model Comparison Experiment[/bold cyan]")
    console.print(f"[bold cyan]  {len(models)} models x {len(SEEDS)} seeds = {total_runs} runs[/bold cyan]")
    console.print(f"[bold cyan]  {POPULATION} pop, {GENERATIONS} gen, {TASKS_PER_GEN} tasks/gen[/bold cyan]")
    console.print(f"[bold cyan]{'='*60}[/bold cyan]\n")

    for model in models:
        for seed in SEEDS:
            completed += 1
            slug = model["slug"]
            output_dir = OUTPUT_BASE / f"{slug}_seed{seed}"
            log_path = OUTPUT_BASE / f"{slug}_seed{seed}.log"

            # Skip if already completed
            if resume and (output_dir / "summary.json").exists():
                console.print(f"[yellow]Skipping {slug} seed={seed} (already done)[/yellow]")
                with open(output_dir / "summary.json") as f:
                    all_summaries.append(json.load(f))
                continue

            console.print(f"\n[bold green]{'─'*60}[/bold green]")
            console.print(
                f"[bold green]  [{completed}/{total_runs}] {model['model_id']} "
                f"({model['params']}) seed={seed}[/bold green]"
            )
            console.print(f"[bold green]{'─'*60}[/bold green]\n")

            try:
                summary = await run_single_experiment(
                    model_id=model["model_id"],
                    slug=slug,
                    seed=seed,
                    output_dir=output_dir,
                    log_path=log_path,
                )
                if summary:
                    all_summaries.append(summary)
                    test_gap = summary["test"]["gap"]
                    test_acc = summary["test"]["task_acc"]
                    console.print(
                        f"\n[bold]  Result: test gap={test_gap:+.1%}, "
                        f"task acc={test_acc:.0%}, "
                        f"time={summary['elapsed_seconds']}s[/bold]"
                    )
            except Exception as e:
                console.print(f"[red]  FAILED: {e}[/red]")
                import traceback
                traceback.print_exc()

    # Save aggregate results
    if all_summaries:
        OUTPUT_BASE.mkdir(parents=True, exist_ok=True)
        with open(OUTPUT_BASE / "all_results.json", "w") as f:
            json.dump(all_summaries, f, indent=2)

        # Print comparison table
        print_comparison_table(all_summaries)

    return all_summaries


def print_comparison_table(summaries: list[dict]):
    """Print a summary comparison table."""
    # Aggregate by model (mean across seeds)
    from collections import defaultdict
    import statistics

    by_model: dict[str, list[dict]] = defaultdict(list)
    for s in summaries:
        by_model[s["slug"]].append(s)

    table = Table(title="Multi-Model Comparison Results")
    table.add_column("Model", style="cyan")
    table.add_column("Params", style="white")
    table.add_column("Task Acc", style="green")
    table.add_column("Raw Cal", style="yellow")
    table.add_column("Evolved Cal", style="yellow")
    table.add_column("Test Gap", style="bold")
    table.add_column("Verdict", style="bold")

    # Sort by parameter count (match MODELS order)
    model_order = {m["slug"]: i for i, m in enumerate(MODELS)}

    for slug in sorted(by_model.keys(), key=lambda s: model_order.get(s, 999)):
        runs = by_model[slug]
        model_info = next((m for m in MODELS if m["slug"] == slug), None)
        params = model_info["params"] if model_info else "?"

        test_gaps = [r["test"]["gap"] for r in runs]
        test_accs = [r["test"]["task_acc"] for r in runs]
        raw_cals = [r["test"]["raw_cal"] for r in runs]
        evolved_cals = [r["test"]["evolved_cal"] for r in runs]

        mean_gap = statistics.mean(test_gaps)
        mean_acc = statistics.mean(test_accs)
        mean_raw = statistics.mean(raw_cals)
        mean_evolved = statistics.mean(evolved_cals)

        gap_std = statistics.stdev(test_gaps) if len(test_gaps) > 1 else 0

        # Verdict
        if mean_gap > 0.03:
            verdict = "[green]System Helps[/green]"
        elif mean_gap > -0.03:
            verdict = "[yellow]Near-Optimal[/yellow]"
        else:
            verdict = "[red]Upgrade Model[/red]"

        gap_str = f"{mean_gap:+.1%}"
        if gap_std > 0:
            gap_str += f" +/-{gap_std:.1%}"

        table.add_row(
            slug.replace("_", " ").title(),
            params,
            f"{mean_acc:.0%}",
            f"{mean_raw:.1%}",
            f"{mean_evolved:.1%}",
            gap_str,
            verdict,
        )

    console.print("\n")
    console.print(table)


def main():
    parser = argparse.ArgumentParser(description="Run multi-model comparison experiments")
    parser.add_argument("--model", type=str, help="Run only this model slug")
    parser.add_argument("--resume", action="store_true", help="Skip completed runs")
    parser.add_argument("--seeds", type=str, default="42,43,44", help="Comma-separated seeds")
    args = parser.parse_args()

    global SEEDS
    SEEDS = [int(s) for s in args.seeds.split(",")]

    if args.model:
        models = [m for m in MODELS if m["slug"] == args.model]
        if not models:
            slugs = ", ".join(m["slug"] for m in MODELS)
            console.print(f"[red]Unknown model slug: {args.model}. Available: {slugs}[/red]")
            sys.exit(1)
    else:
        models = MODELS

    asyncio.run(run_all_experiments(models, resume=args.resume))


if __name__ == "__main__":
    main()
