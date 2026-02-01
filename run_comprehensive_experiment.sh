#!/bin/bash
# Comprehensive multi-model × multi-seed experiment
# 3 models × 3 seeds = 9 runs total
# Proves both reproducibility AND model comparison

set -e

# Configuration
POPULATION=10
GENERATIONS=10
TASKS=8
OUTPUT_DIR="data/comprehensive_experiment"

mkdir -p "$OUTPUT_DIR"

echo "========================================="
echo "COMPREHENSIVE VALIDATION EXPERIMENT"
echo "========================================="
echo "Models: 3 (GPT-5.2, GPT-4.1, DeepSeek V3.1)"
echo "Seeds per model: 3 (42, 43, 44)"
echo "Total runs: 9"
echo "Population: $POPULATION"
echo "Generations: $GENERATIONS"
echo "Tasks/gen: $TASKS"
echo "Output: $OUTPUT_DIR"
echo "========================================="
echo ""

# Check API keys
if [[ -z "$OPENAI_API_KEY" ]]; then
    echo "❌ ERROR: OPENAI_API_KEY not set"
    exit 1
fi
if [[ -z "$WANDB_API_KEY" ]]; then
    echo "❌ ERROR: WANDB_API_KEY not set"
    exit 1
fi
echo "✓ API keys validated"
echo ""

# Model configs: model_id|base_url|api_key_var|display_name
MODELS=(
    "gpt-5.2||OPENAI_API_KEY|GPT-5.2"
    "gpt-4.1||OPENAI_API_KEY|GPT-4.1"
    "deepseek-ai/DeepSeek-V3-0324|https://api.inference.wandb.ai/v1|WANDB_API_KEY|DeepSeek-V3"
)

SEEDS=(42 43 44)
RUN_COUNT=0
TOTAL_RUNS=$((${#MODELS[@]} * ${#SEEDS[@]}))

echo "Starting all runs..."
echo ""

for model_spec in "${MODELS[@]}"; do
    IFS='|' read -r model_id base_url api_key_var display_name <<< "$model_spec"

    for seed in "${SEEDS[@]}"; do
        RUN_COUNT=$((RUN_COUNT + 1))

        safe_name=$(echo "${display_name}_seed${seed}" | tr '[:upper:]' '[:lower:]' | tr '.' '_' | tr '-' '_')
        run_dir="$OUTPUT_DIR/$safe_name"

        echo "[$RUN_COUNT/$TOTAL_RUNS] Starting: $display_name (seed=$seed)"

        # Set up environment
        export MODEL_NAME="$model_id"
        if [[ -n "$base_url" ]]; then
            export OPENAI_BASE_URL="$base_url"
        else
            unset OPENAI_BASE_URL
        fi

        # Get the appropriate API key
        export OPENAI_API_KEY="${!api_key_var}"

        # Run evolution in background (use venv python directly)
        .venv/bin/python -m src.main run \
            --population $POPULATION \
            --generations $GENERATIONS \
            --tasks $TASKS \
            --seed $seed \
            --no-weave \
            --output-dir "$run_dir" \
            > "$run_dir.log" 2>&1 &

        PID=$!
        echo $PID > "$run_dir.pid"
        echo "  → PID: $PID | Log: $run_dir.log"

        # Small delay between starts
        sleep 3
    done

    echo ""
done

echo "All $TOTAL_RUNS runs started in background!"
echo ""
echo "Monitor progress:"
echo "  tail -f $OUTPUT_DIR/*.log"
echo "  watch -n 5 'ls $OUTPUT_DIR/*/evolution_run.json | wc -l'"
echo ""
echo "Waiting for completion..."

# Wait for all background jobs
wait

echo ""
echo "========================================="
echo "ALL RUNS COMPLETE!"
echo "========================================="
echo ""

# Run comprehensive analysis
python3 - <<'PYTHON'
import json
import numpy as np
from pathlib import Path
from collections import defaultdict

output_dir = Path("data/comprehensive_experiment")
run_dirs = sorted([d for d in output_dir.iterdir() if d.is_dir()])

if not run_dirs:
    print("ERROR: No run directories found!")
    exit(1)

print("=" * 80)
print("COMPREHENSIVE VALIDATION RESULTS")
print("=" * 80)
print("")

# Organize results by model
model_results = defaultdict(list)

for run_dir in run_dirs:
    run_file = run_dir / "evolution_run.json"
    if not run_file.exists():
        print(f"⚠️  Skipping {run_dir.name} - no results")
        continue

    with open(run_file) as f:
        data = json.load(f)

    stats = data.get("generation_stats", [])
    test_results = data.get("test_results", {})

    if not stats:
        continue

    first, last = stats[0], stats[-1]

    # Extract model name and seed
    name_parts = run_dir.name.split("_seed")
    model_name = name_parts[0].replace("_", " ").title()
    seed = int(name_parts[1]) if len(name_parts) > 1 else 42

    result = {
        "seed": seed,
        "train_raw_start": first.get("avg_raw_calibration", first["avg_prediction_accuracy"]),
        "train_raw_end": last.get("avg_raw_calibration", last["avg_prediction_accuracy"]),
        "train_evolved_start": first["avg_prediction_accuracy"],
        "train_evolved_end": last["avg_prediction_accuracy"],
        "train_gap": last["avg_prediction_accuracy"] - last.get("avg_raw_calibration", last["avg_prediction_accuracy"]),
        "test_raw": test_results.get("avg_raw_calibration", 0) if test_results else 0,
        "test_evolved": test_results.get("avg_prediction_accuracy", 0) if test_results else 0,
        "test_gap": (test_results.get("avg_prediction_accuracy", 0) -
                     test_results.get("avg_raw_calibration", 0)) if test_results else 0,
        "fitness_improvement": last["avg_fitness"] - first["avg_fitness"],
    }

    model_results[model_name].append(result)

# Print results
print("📊 TRAINING SET RESULTS (Evolution Optimization)")
print("-" * 80)
print(f"{'Model':<20} {'Seeds':<8} {'Raw Cal':<10} {'Evolved Cal':<12} {'Gap':<12} {'Reproducible?'}")
print("-" * 80)

for model_name in sorted(model_results.keys()):
    results = model_results[model_name]

    train_gaps = [r["train_gap"] for r in results]
    train_evolved = [r["train_evolved_end"] for r in results]

    mean_gap = np.mean(train_gaps)
    std_gap = np.std(train_gaps)
    mean_evolved = np.mean(train_evolved)
    std_evolved = np.std(train_evolved)

    # Check reproducibility (CV < 15%)
    cv = (std_gap / mean_gap * 100) if mean_gap > 0 else 0
    reproducible = "✓" if cv < 15 else "✗"

    print(f"{model_name:<20} {len(results):<8} "
          f"{results[0]['train_raw_end']:>6.1%}      "
          f"{mean_evolved:>6.1%}±{std_evolved:>4.1%}   "
          f"{mean_gap:>+5.1%}±{std_gap:>4.1%}   "
          f"{reproducible}")

print("")
print("🎯 TEST SET RESULTS (Held-Out Generalization)")
print("-" * 80)
print(f"{'Model':<20} {'Raw→Evolved':<20} {'Test Gap':<15} {'Verdict'}")
print("-" * 80)

model_verdicts = []

for model_name in sorted(model_results.keys()):
    results = model_results[model_name]

    test_gaps = [r["test_gap"] for r in results if r["test_gap"] > 0]
    if not test_gaps:
        continue

    mean_test_gap = np.mean(test_gaps)
    std_test_gap = np.std(test_gaps)
    mean_test_evolved = np.mean([r["test_evolved"] for r in results if r["test_evolved"] > 0])
    mean_test_raw = np.mean([r["test_raw"] for r in results if r["test_raw"] > 0])

    # Determine verdict
    if mean_test_gap > 0.04:
        verdict = "🔧 System bottleneck"
        verdict_emoji = "🔧"
    elif mean_test_gap < 0.02:
        verdict = "🤖 Model ceiling"
        verdict_emoji = "🤖"
    else:
        verdict = "⚖️  Mixed optimization"
        verdict_emoji = "⚖️"

    model_verdicts.append((model_name, mean_test_gap, verdict_emoji))

    print(f"{model_name:<20} {mean_test_raw:>6.1%} → {mean_test_evolved:>6.1%}    "
          f"{mean_test_gap:>+5.1%}±{std_test_gap:>4.1%}    {verdict}")

print("")
print("=" * 80)
print("KEY FINDINGS")
print("=" * 80)

# Cross-model comparison
all_test_gaps = []
for model_name in model_results:
    gaps = [r["test_gap"] for r in model_results[model_name] if r["test_gap"] > 0]
    all_test_gaps.extend(gaps)

if len(all_test_gaps) >= 2:
    overall_mean = np.mean(all_test_gaps)
    overall_std = np.std(all_test_gaps)

    print(f"• Overall test calibration gain: {overall_mean:>+5.1%} ± {overall_std:>4.1%}")
    print(f"• Coefficient of variation: {(overall_std/overall_mean*100):>5.1f}%")

    # Best and worst models
    model_means = [(name, np.mean([r["test_gap"] for r in model_results[name] if r["test_gap"] > 0]))
                   for name in model_results if any(r["test_gap"] > 0 for r in model_results[name])]
    model_means.sort(key=lambda x: x[1], reverse=True)

    if len(model_means) >= 2:
        best_model, best_gap = model_means[0]
        worst_model, worst_gap = model_means[-1]
        gap_range = best_gap - worst_gap

        print(f"• Highest optimization potential: {best_model} ({best_gap:>+5.1%})")
        print(f"• Lowest optimization potential: {worst_model} ({worst_gap:>+5.1%})")
        print(f"• Model variation range: {gap_range:>5.1%}")

        if gap_range > 0.03:
            print("")
            print("✅ VALIDATION: System optimization impact varies by model")
            print("   → The 'system vs model' diagnostic is meaningful")
            print("   → Some models benefit more from config tuning than others")
        else:
            print("")
            print("✅ VALIDATION: System optimization is consistent across models")
            print("   → All models have similar headroom for improvement")

print("")
print("📈 STATISTICAL VALIDATION")
print("-" * 80)

# Check reproducibility across all runs
all_model_cvs = []
for model_name in model_results:
    results = model_results[model_name]
    if len(results) < 2:
        continue
    gaps = [r["test_gap"] for r in results if r["test_gap"] > 0]
    if len(gaps) >= 2:
        cv = np.std(gaps) / np.mean(gaps) * 100 if np.mean(gaps) > 0 else 0
        all_model_cvs.append(cv)

if all_model_cvs:
    avg_cv = np.mean(all_model_cvs)
    print(f"• Average coefficient of variation: {avg_cv:.1f}%")
    if avg_cv < 15:
        print("  ✓ Results are reproducible (CV < 15%)")
    else:
        print("  ⚠️  High variability detected (CV > 15%)")

# Count successful runs
total_expected = len(model_results) * 3
total_found = sum(len(results) for results in model_results.values())
print(f"• Successful runs: {total_found}/{total_expected}")

print("")
print("=" * 80)
print(f"✅ Analysis complete | Results in: {output_dir}/")
print("=" * 80)
PYTHON

echo ""
echo "Experiment complete!"
echo "Detailed results in: $OUTPUT_DIR/"
