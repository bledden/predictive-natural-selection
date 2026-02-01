#!/usr/bin/env python3
"""
Analyze comprehensive multi-model × multi-seed experiment results
"""

import json
from pathlib import Path
from statistics import mean, stdev
from typing import Dict, List

def load_run(run_dir: Path) -> Dict:
    """Load evolution_run.json from a run directory"""
    json_path = run_dir / "evolution_run.json"
    with open(json_path) as f:
        return json.load(f)

def analyze_model(model_name: str, seeds: List[int], base_dir: Path) -> Dict:
    """Analyze results for one model across multiple seeds"""
    runs = []
    for seed in seeds:
        run_name = f"{model_name}_seed{seed}"
        run_dir = base_dir / run_name
        if run_dir.exists():
            run_data = load_run(run_dir)
            runs.append(run_data)

    if not runs:
        return None

    # Extract test set metrics
    test_metrics = []
    for run in runs:
        if "test_results" in run and run["test_results"]:
            test_metrics.append({
                "raw_calibration": run["test_results"]["avg_raw_calibration"],
                "evolved_calibration": run["test_results"]["avg_prediction_accuracy"],
                "accuracy": run["test_results"]["avg_prediction_accuracy"],
                "fitness": run["test_results"]["best_fitness"],
            })

    if not test_metrics:
        return None

    # Compute statistics
    raw_cals = [m["raw_calibration"] for m in test_metrics]
    evolved_cals = [m["evolved_calibration"] for m in test_metrics]
    accuracies = [m["accuracy"] for m in test_metrics]
    fitnesses = [m["fitness"] for m in test_metrics]

    gap = mean(evolved_cals) - mean(raw_cals)

    return {
        "model": model_name,
        "n_runs": len(test_metrics),
        "raw_calibration": {
            "mean": mean(raw_cals),
            "std": stdev(raw_cals) if len(raw_cals) > 1 else 0,
        },
        "evolved_calibration": {
            "mean": mean(evolved_cals),
            "std": stdev(evolved_cals) if len(evolved_cals) > 1 else 0,
        },
        "accuracy": {
            "mean": mean(accuracies),
            "std": stdev(accuracies) if len(accuracies) > 1 else 0,
        },
        "fitness": {
            "mean": mean(fitnesses),
            "std": stdev(fitnesses) if len(fitnesses) > 1 else 0,
        },
        "calibration_gap": gap,
        "cv_percent": (stdev(evolved_cals) / mean(evolved_cals) * 100) if len(evolved_cals) > 1 and mean(evolved_cals) > 0 else 0,
    }

def get_verdict(gap: float, threshold: float = 0.05) -> str:
    """Determine if optimization gap is significant"""
    if gap > threshold:
        return "🔧 SYSTEM"
    elif gap < -threshold:
        return "🤖 MODEL"
    else:
        return "⚖️  MIXED"

def main():
    base_dir = Path("data/comprehensive_experiment")
    seeds = [42, 43, 44]

    # Model name mapping (dir_prefix -> display_name)
    models = {
        "gpt_5_2": "GPT-5.2",
        "claude_opus_4_5": "Claude Opus 4.5",
        "deepseek_v3": "DeepSeek V3",
    }

    print("="*70)
    print("COMPREHENSIVE VALIDATION EXPERIMENT RESULTS")
    print("="*70)
    print(f"Models: {len(models)} (GPT-5.2, Claude Opus 4.5, DeepSeek V3)")
    print(f"Seeds per model: {len(seeds)} ({', '.join(map(str, seeds))})")
    print(f"Total runs: {len(models) * len(seeds)}")
    print("="*70)
    print()

    # Analyze each model
    results = {}
    for model_key, model_name in models.items():
        result = analyze_model(model_key, seeds, base_dir)
        if result:
            results[model_name] = result

    # Display results
    print("## TEST SET PERFORMANCE (Held-Out Data)")
    print()
    print(f"{'Model':<20} {'Raw Cal':<15} {'Evolved Cal':<15} {'Accuracy':<15} {'Gap':<10} {'CV%':<8} {'Verdict'}")
    print("-" * 110)

    for model_name, res in results.items():
        verdict = get_verdict(res["calibration_gap"])
        print(f"{model_name:<20} "
              f"{res['raw_calibration']['mean']*100:5.1f}±{res['raw_calibration']['std']*100:4.1f}%     "
              f"{res['evolved_calibration']['mean']*100:5.1f}±{res['evolved_calibration']['std']*100:4.1f}%     "
              f"{res['accuracy']['mean']*100:5.1f}±{res['accuracy']['std']*100:4.1f}%     "
              f"{res['calibration_gap']*100:+5.1f}%    "
              f"{res['cv_percent']:5.1f}%   "
              f"{verdict}")

    print()
    print("=" * 110)
    print()

    # Interpretation
    print("## STATISTICAL VALIDATION")
    print()
    for model_name, res in results.items():
        reproducible = "✅ Reproducible" if res["cv_percent"] < 10 else "⚠️  High variance"
        print(f"**{model_name}**: {reproducible} (CV={res['cv_percent']:.1f}%, {res['n_runs']}/{len(seeds)} runs)")

    print()
    print("=" * 110)
    print()

    print("## CROSS-MODEL COMPARISON")
    print()
    print("**Key Question: Do you need a better system — or a better model?**")
    print()

    # Sort by calibration gap
    sorted_models = sorted(results.items(), key=lambda x: x[1]["calibration_gap"], reverse=True)

    for model_name, res in sorted_models:
        verdict = get_verdict(res["calibration_gap"])
        gap_pct = res["calibration_gap"] * 100

        if "SYSTEM" in verdict:
            msg = f"has {gap_pct:+.1f}% optimization headroom → focus on system tuning"
        elif "MODEL" in verdict:
            msg = f"shows {gap_pct:+.1f}% performance → already well-calibrated, need better model"
        else:
            msg = f"has minimal gap ({gap_pct:+.1f}%) → system and model are balanced"

        print(f"{verdict} **{model_name}**: {msg}")

    print()
    print("=" * 110)
    print()

    # Save results
    output_file = base_dir / "analysis_results.json"
    with open(output_file, "w") as f:
        json.dump(results, f, indent=2)

    print(f"✅ Detailed results saved to: {output_file}")

if __name__ == "__main__":
    main()
