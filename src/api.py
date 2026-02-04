"""FastAPI backend: serves evolution run data to the Next.js dashboard."""

from __future__ import annotations

import asyncio
import json
import os
from dataclasses import asdict
from pathlib import Path

from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse

from .validation import (
    compute_historical_validation,
    run_live_ab_test,
    run_generalization_test,
)

app = FastAPI(title="Predictive Natural Selection API", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:3001", "http://127.0.0.1:3000", "http://127.0.0.1:3001"],
    allow_methods=["GET", "POST"],
    allow_headers=["*"],
)

DATA_DIR = Path(__file__).resolve().parent.parent / "data"

# Track live run state
_live_run_active = False
_live_run_generation = -1
_live_run_total = 0

# Available experiment datasets
EXPERIMENTS = {
    "claude_opus_4_5": {
        "name": "Claude Opus 4.5",
        "path": "comprehensive_experiment/claude_opus_4_5_seed42",
        "category": "frontier",
    },
    "gpt_5_2": {
        "name": "GPT-5.2",
        "path": "comprehensive_experiment/gpt_5_2_seed42",
        "category": "frontier",
    },
    "deepseek_v3": {
        "name": "DeepSeek V3",
        "path": "comprehensive_experiment/deepseek_v3_seed42",
        "category": "frontier",
    },
    "gpt_4o": {
        "name": "GPT-4o",
        "path": "previous_gen_experiment/gpt_4o_seed42",
        "category": "previous_gen",
    },
}

# Currently active experiment (default)
_active_experiment = "claude_opus_4_5"


def _load_run() -> dict:
    path = DATA_DIR / "evolution_run.json"
    if not path.exists():
        raise HTTPException(status_code=404, detail="No evolution run data found. Run the simulation first.")
    with open(path) as f:
        return json.load(f)


@app.get("/api/run")
def get_run_summary():
    """High-level run summary: generation stats and metadata."""
    data = _load_run()
    stats = data.get("generation_stats", [])
    genomes = data.get("all_genomes", [])
    test_results = data.get("test_results", {})

    if not stats:
        return {"status": "empty"}

    first, last = stats[0], stats[-1]

    # count strategies in final generation
    final_gen = last["generation"]
    final_genomes = [g for g in genomes if g["generation"] == final_gen]
    style_counts = {}
    for g in final_genomes:
        s = g["reasoning_style"]
        style_counts[s] = style_counts.get(s, 0) + 1

    initial_styles = set(g["reasoning_style"] for g in genomes if g["generation"] == 0)
    final_styles = set(g["reasoning_style"] for g in final_genomes)

    summary = {
        "total_generations": last["generation"] + 1,
        "population_size": last["population_size"],
        "initial_avg_fitness": first["avg_fitness"],
        "final_avg_fitness": last["avg_fitness"],
        "fitness_improvement": last["avg_fitness"] - first["avg_fitness"],
        "best_fitness": last["best_fitness"],
        "initial_raw_calibration": first.get("avg_raw_calibration", first["avg_prediction_accuracy"]),
        "final_raw_calibration": last.get("avg_raw_calibration", last["avg_prediction_accuracy"]),
        "initial_evolved_calibration": first["avg_prediction_accuracy"],
        "final_evolved_calibration": last["avg_prediction_accuracy"],
        "initial_task_accuracy": first["avg_task_accuracy"],
        "final_task_accuracy": last["avg_task_accuracy"],
        "dominant_strategy": last["dominant_reasoning"],
        "strategy_counts": style_counts,
        "extinct_strategies": list(initial_styles - final_styles),
    }

    # Add test set results if available
    if test_results:
        summary["test_set"] = {
            "n_tasks": test_results.get("n_tasks", 0),
            "raw_calibration": test_results.get("avg_raw_calibration", 0),
            "evolved_calibration": test_results.get("avg_prediction_accuracy", 0),
            "task_accuracy": test_results.get("avg_task_accuracy", 0),
            "best_fitness": test_results.get("best_fitness", 0),
            "avg_fitness": test_results.get("avg_fitness", 0),
        }

    return summary


@app.get("/api/generations")
def get_generation_stats():
    """Per-generation stats for charting."""
    data = _load_run()
    return data.get("generation_stats", [])


@app.get("/api/genomes")
def get_all_genomes():
    """All genomes across all generations."""
    data = _load_run()
    return data.get("all_genomes", [])


@app.get("/api/genomes/{generation}")
def get_genomes_by_generation(generation: int):
    """Genomes for a specific generation."""
    data = _load_run()
    genomes = [g for g in data.get("all_genomes", []) if g["generation"] == generation]
    if not genomes:
        raise HTTPException(status_code=404, detail=f"No genomes found for generation {generation}")
    return genomes


@app.get("/api/results")
def get_all_results():
    """All individual eval results (agent x task)."""
    data = _load_run()
    return data.get("all_results", [])


@app.get("/api/results/{generation}")
def get_results_by_generation(generation: int):
    """Eval results for a specific generation."""
    data = _load_run()
    results = [r for r in data.get("all_results", []) if r["generation"] == generation]
    return results


@app.get("/api/lineage/{genome_id}")
def get_lineage(genome_id: str):
    """Trace lineage of a specific genome back to generation 0."""
    data = _load_run()
    genomes = {g["genome_id"]: g for g in data.get("all_genomes", [])}

    if genome_id not in genomes:
        raise HTTPException(status_code=404, detail=f"Genome {genome_id} not found")

    lineage = []
    visited = set()
    queue = [genome_id]

    while queue:
        gid = queue.pop(0)
        if gid in visited or gid not in genomes:
            continue
        visited.add(gid)
        g = genomes[gid]
        lineage.append(g)
        queue.extend(g.get("parent_ids", []))

    lineage.sort(key=lambda g: g["generation"])
    return lineage


@app.get("/api/phylogeny")
def get_phylogeny():
    """Full phylogenetic tree as nodes + edges for frontend rendering."""
    data = _load_run()
    genomes = data.get("all_genomes", [])
    genome_ids = {g["genome_id"] for g in genomes}

    nodes = [
        {
            "id": g["genome_id"],
            "generation": g["generation"],
            "reasoning_style": g["reasoning_style"],
            "confidence_bias": g["confidence_bias"],
            "temperature": g["temperature"],
            "system_prompt": g["system_prompt"][:60],
        }
        for g in genomes
    ]

    edges = []
    for g in genomes:
        for pid in g.get("parent_ids", []):
            if pid in genome_ids:
                edges.append({"source": pid, "target": g["genome_id"]})

    return {"nodes": nodes, "edges": edges}


@app.get("/api/prescription")
def get_prescription():
    """Actionable configuration prescription derived from evolution results."""
    data = _load_run()
    stats = data.get("generation_stats", [])
    genomes = data.get("all_genomes", [])
    results = data.get("all_results", [])

    if not stats or not genomes:
        raise HTTPException(status_code=404, detail="No evolution data available")

    first, last = stats[0], stats[-1]
    final_gen = last["generation"]
    final_genomes = [g for g in genomes if g["generation"] == final_gen]

    # Find the best genome by fitness in the final generation
    genome_fitness: dict[str, float] = {}
    for r in results:
        if r["generation"] == final_gen:
            gid = r["genome_id"]
            genome_fitness.setdefault(gid, [])
            genome_fitness[gid].append(r["fitness"])
    genome_avg_fitness = {gid: sum(fs) / len(fs) for gid, fs in genome_fitness.items() if fs}
    best_id = max(genome_avg_fitness, key=genome_avg_fitness.get) if genome_avg_fitness else None
    best_genome = next((g for g in final_genomes if g["genome_id"] == best_id), None) if best_id else None

    # Compute converged trait statistics from final population
    import statistics
    conf_biases = [g["confidence_bias"] for g in final_genomes]
    temperatures = [g["temperature"] for g in final_genomes]
    risk_tolerances = [g["risk_tolerance"] for g in final_genomes]

    style_counts: dict[str, int] = {}
    for g in final_genomes:
        s = g["reasoning_style"]
        style_counts[s] = style_counts.get(s, 0) + 1
    dominant_style = max(style_counts, key=style_counts.get)
    dominant_pct = style_counts[dominant_style] / len(final_genomes)

    # Extinct strategies
    initial_styles = set(g["reasoning_style"] for g in genomes if g["generation"] == 0)
    final_styles = set(g["reasoning_style"] for g in final_genomes)
    extinct = list(initial_styles - final_styles)

    # Weakest strategies (present but rare, <10% of population)
    weak = [s for s, c in style_counts.items() if c / len(final_genomes) < 0.10 and s != dominant_style]

    # Gap analysis
    raw_cal = last.get("avg_raw_calibration", last["avg_prediction_accuracy"])
    evolved_cal = last["avg_prediction_accuracy"]
    gap = evolved_cal - raw_cal

    return {
        "gap": gap,
        "gap_pct": round(gap * 100, 1),
        "raw_calibration": round(raw_cal * 100, 1),
        "evolved_calibration": round(evolved_cal * 100, 1),
        "best_genome": {
            "genome_id": best_genome["genome_id"] if best_genome else None,
            "fitness": round(genome_avg_fitness.get(best_id, 0), 4) if best_id else None,
            "reasoning_style": best_genome["reasoning_style"] if best_genome else None,
            "system_prompt": best_genome["system_prompt"] if best_genome else None,
            "confidence_bias": best_genome["confidence_bias"] if best_genome else None,
            "temperature": best_genome["temperature"] if best_genome else None,
            "risk_tolerance": best_genome["risk_tolerance"] if best_genome else None,
        } if best_genome else None,
        "converged_traits": {
            "confidence_bias": {
                "mean": round(statistics.mean(conf_biases), 4),
                "std": round(statistics.stdev(conf_biases), 4) if len(conf_biases) > 1 else 0,
            },
            "temperature": {
                "mean": round(statistics.mean(temperatures), 3),
                "std": round(statistics.stdev(temperatures), 3) if len(temperatures) > 1 else 0,
            },
            "risk_tolerance": {
                "mean": round(statistics.mean(risk_tolerances), 3),
                "std": round(statistics.stdev(risk_tolerances), 3) if len(risk_tolerances) > 1 else 0,
            },
        },
        "dominant_strategy": dominant_style,
        "dominant_strategy_pct": round(dominant_pct * 100, 1),
        "strategy_distribution": {s: c for s, c in sorted(style_counts.items(), key=lambda x: -x[1])},
        "extinct_strategies": extinct,
        "weak_strategies": weak,
        "total_generations": last["generation"] + 1,
        "population_size": len(final_genomes),
        "validation": compute_historical_validation(data),
    }


@app.get("/api/live/status")
def get_live_status():
    """Check if a live evolution run is active."""
    return {
        "active": _live_run_active,
        "current_generation": _live_run_generation,
        "total_generations": _live_run_total,
    }


@app.get("/api/live/run")
async def live_evolution_run(
    population: int = 10,
    generations: int = 8,
    tasks: int = 8,
):
    """Start a live evolution run and stream results as SSE."""
    global _live_run_active, _live_run_generation, _live_run_total

    if _live_run_active:
        raise HTTPException(status_code=409, detail="A live run is already in progress")

    async def event_stream():
        global _live_run_active, _live_run_generation, _live_run_total

        _live_run_active = True
        _live_run_generation = -1
        _live_run_total = generations

        try:
            from .evaluator import configure_client, run_generation_tasks
            from .evolution import aggregate_fitness, produce_next_generation
            from .genome import AgentGenome
            from .population_store import PopulationStore
            from .tasks import get_fixed_task_batch

            # configure LLM from env
            model = os.environ.get("MODEL_NAME", "deepseek-ai/DeepSeek-V3-0324")
            base_url = os.environ.get("OPENAI_BASE_URL", "https://api.inference.wandb.ai/v1")
            api_key = os.environ.get("OPENAI_API_KEY", os.environ.get("WANDB_API_KEY", ""))
            configure_client(model=model, base_url=base_url, api_key=api_key)

            store = PopulationStore("redis://localhost:6379/0")
            await store.clear_all()

            all_stats = []
            all_genomes_list = []
            all_results_list = []

            # initial population
            pop = [AgentGenome.random(generation=0) for _ in range(population)]
            for g in pop:
                await store.save_genome(g)
                all_genomes_list.append(g.to_dict())

            yield f"data: {json.dumps({'type': 'start', 'population': population, 'generations': generations, 'tasks': tasks})}\n\n"

            # Use TRAINING tasks only during evolution
            tasks_batch = get_fixed_task_batch(n=tasks, run_seed=42, split="train")

            for gen in range(generations):
                _live_run_generation = gen

                results = await run_generation_tasks(pop, tasks_batch, concurrency=10)

                fitness_scores: dict[str, float] = {}
                for genome in pop:
                    agent_results = results.get(genome.genome_id, [])
                    per_task = [r.fitness for r in agent_results]
                    fitness = aggregate_fitness(per_task)
                    fitness_scores[genome.genome_id] = fitness
                    await store.record_fitness(genome.genome_id, gen, fitness)

                    for r in agent_results:
                        all_results_list.append({
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

                fitnesses = list(fitness_scores.values())
                all_eval = [r for rs in results.values() for r in rs]

                reasoning_counts: dict[str, int] = {}
                memory_counts: dict[str, int] = {}
                for g in pop:
                    reasoning_counts[g.reasoning_style] = reasoning_counts.get(g.reasoning_style, 0) + 1
                    memory_counts[g.memory_weighting] = memory_counts.get(g.memory_weighting, 0) + 1

                gen_stat = {
                    "generation": gen,
                    "population_size": len(pop),
                    "avg_fitness": sum(fitnesses) / len(fitnesses),
                    "best_fitness": max(fitnesses),
                    "worst_fitness": min(fitnesses),
                    "avg_raw_calibration": sum(r.raw_calibration for r in all_eval) / len(all_eval),
                    "avg_prediction_accuracy": sum(r.prediction_accuracy for r in all_eval) / len(all_eval),
                    "avg_task_accuracy": sum(1 for r in all_eval if r.is_correct) / len(all_eval),
                    "dominant_reasoning": max(reasoning_counts, key=reasoning_counts.get),
                    "dominant_memory": max(memory_counts, key=memory_counts.get),
                    "elapsed_seconds": 0,
                }
                all_stats.append(gen_stat)

                yield f"data: {json.dumps({'type': 'generation', **gen_stat})}\n\n"

                if gen < generations - 1:
                    pop = produce_next_generation(pop, fitness_scores, target_size=population)
                    for g in pop:
                        await store.save_genome(g)
                        await store.record_lineage(g.genome_id, g.parent_ids)
                        all_genomes_list.append(g.to_dict())

                await store.set_current_generation(gen)

            # Evaluate on held-out test set
            from .orchestrator import evaluate_on_test_set
            from .tasks import get_train_val_test_split

            _, _, test_tasks = get_train_val_test_split(run_seed=42)
            test_eval = await evaluate_on_test_set(pop, run_seed=42, concurrency=10)

            yield f"data: {json.dumps({'type': 'test_eval', 'test_results': test_eval})}\n\n"

            # Save to disk so the static endpoints pick it up
            DATA_DIR.mkdir(parents=True, exist_ok=True)
            with open(DATA_DIR / "evolution_run.json", "w") as f:
                json.dump({
                    "generation_stats": all_stats,
                    "all_genomes": all_genomes_list,
                    "all_results": all_results_list,
                    "test_results": test_eval,
                }, f, indent=2)

            yield f"data: {json.dumps({'type': 'complete', 'total_generations': generations, 'test_results': test_eval})}\n\n"

        except Exception as e:
            yield f"data: {json.dumps({'type': 'error', 'message': str(e)})}\n\n"
        finally:
            _live_run_active = False
            _live_run_generation = -1
            await store.close()

    return StreamingResponse(event_stream(), media_type="text/event-stream")


# ============================================================================
# VALIDATION ENDPOINTS
# ============================================================================

@app.get("/api/validate/historical")
def validate_historical():
    """Layer 1: Historical validation from evolution data.

    Shows improvement from generation 0 (random) to generation N (evolved).
    Proves the prescription works because evolution tested these settings.
    """
    data = _load_run()
    validation = compute_historical_validation(data)
    return validation


@app.get("/api/validate/live")
async def validate_live(tasks: int = 10):
    """Layer 2: Live A/B test — naive vs optimized on same tasks.

    Runs both agents side-by-side right now to prove the delta.
    Takes ~10-20 seconds depending on task count.

    Args:
        tasks: Number of tasks to test (default 10)
    """
    data = _load_run()
    prescription = get_prescription()
    validation = await run_live_ab_test(prescription, num_tasks=tasks)
    return validation


@app.get("/api/validate/generalization")
async def validate_generalization(tasks: int = 10):
    """Layer 3: Generalization test on held-out tasks.

    Tests prescription on tasks unseen during evolution.
    Proves the settings generalize, not just overfit to training tasks.

    Args:
        tasks: Number of held-out tasks to test (default 10)
    """
    prescription = get_prescription()
    validation = await run_generalization_test(prescription, num_tasks=tasks)
    return validation


# ============================================================================
# MULTI-EXPERIMENT COMPARISON ENDPOINTS
# ============================================================================

@app.get("/api/experiments")
def list_experiments():
    """List all available experiment datasets."""
    available = []
    for key, info in EXPERIMENTS.items():
        exp_path = DATA_DIR / info["path"] / "evolution_run.json"
        available.append({
            "id": key,
            "name": info["name"],
            "category": info["category"],
            "has_data": exp_path.exists(),
            "active": key == _active_experiment,
        })
    return available


@app.post("/api/experiments/{experiment_id}/activate")
def activate_experiment(experiment_id: str):
    """Switch the dashboard to display a different experiment."""
    global _active_experiment
    if experiment_id not in EXPERIMENTS:
        raise HTTPException(status_code=404, detail=f"Unknown experiment: {experiment_id}")

    info = EXPERIMENTS[experiment_id]
    src = DATA_DIR / info["path"] / "evolution_run.json"
    if not src.exists():
        raise HTTPException(status_code=404, detail=f"No data for {info['name']}")

    # Copy experiment data to the main evolution_run.json
    import shutil
    dst = DATA_DIR / "evolution_run.json"
    shutil.copy2(src, dst)
    _active_experiment = experiment_id

    return {"status": "ok", "active": experiment_id, "name": info["name"]}


@app.get("/api/comparison")
def get_comparison():
    """Compare all available experiments side by side."""
    results = []
    for key, info in EXPERIMENTS.items():
        exp_path = DATA_DIR / info["path"] / "evolution_run.json"
        if not exp_path.exists():
            continue

        with open(exp_path) as f:
            data = json.load(f)

        stats = data.get("generation_stats", [])
        test = data.get("test_results", {})

        if not stats:
            continue

        first, last = stats[0], stats[-1]
        raw_cal = last.get("avg_raw_calibration", last["avg_prediction_accuracy"])
        evolved_cal = last["avg_prediction_accuracy"]
        gap = evolved_cal - raw_cal

        # Test set metrics if available
        test_raw = test.get("avg_raw_calibration", raw_cal)
        test_evolved = test.get("avg_prediction_accuracy", evolved_cal)
        test_gap = test_evolved - test_raw

        # Determine verdict
        if abs(test_gap) < 0.03:
            verdict = "already_optimized"
            verdict_label = "Already Optimized"
        elif test_gap > 0.03:
            verdict = "system_helps"
            verdict_label = "System Optimization Helps"
        else:
            verdict = "need_better_model"
            verdict_label = "Need Better Model"

        results.append({
            "id": key,
            "name": info["name"],
            "category": info["category"],
            "generations": last["generation"] + 1,
            "training": {
                "raw_calibration": round(raw_cal * 100, 1),
                "evolved_calibration": round(evolved_cal * 100, 1),
                "gap_pct": round(gap * 100, 1),
            },
            "test_set": {
                "raw_calibration": round(test_raw * 100, 1),
                "evolved_calibration": round(test_evolved * 100, 1),
                "gap_pct": round(test_gap * 100, 1),
                "task_accuracy": round(test.get("avg_task_accuracy", 0) * 100, 1),
            },
            "fitness": {
                "initial": round(first["avg_fitness"], 4),
                "final": round(last["avg_fitness"], 4),
                "improvement": round(last["avg_fitness"] - first["avg_fitness"], 4),
            },
            "dominant_strategy": last["dominant_reasoning"],
            "verdict": verdict,
            "verdict_label": verdict_label,
        })

    # Sort: frontier first, then by test calibration descending
    results.sort(key=lambda r: (0 if r["category"] == "frontier" else 1, -r["test_set"]["evolved_calibration"]))
    return results
