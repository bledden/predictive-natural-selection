#!/bin/bash
# Run multiple evolution trials with different seeds for statistical validation
# Usage: ./run_multi_seed.sh [num_seeds] [population] [generations] [tasks]

set -e

NUM_SEEDS=${1:-5}
POPULATION=${2:-20}
GENERATIONS=${3:-20}
TASKS=${4:-12}
OUTPUT_DIR="data/multi_seed_runs"

mkdir -p "$OUTPUT_DIR"

echo "========================================="
echo "Multi-Seed Evolution Experiment"
echo "========================================="
echo "Seeds: $NUM_SEEDS"
echo "Population: $POPULATION"
echo "Generations: $GENERATIONS"
echo "Tasks per generation: $TASKS"
echo "Output directory: $OUTPUT_DIR"
echo "========================================="
echo ""

# Seeds to use (42-46 for 5 runs)
SEEDS=(42 43 44 45 46 47 48 49 50 51)

for i in $(seq 0 $((NUM_SEEDS-1))); do
    SEED=${SEEDS[$i]}
    echo "Starting run $((i+1))/$NUM_SEEDS with seed=$SEED..."

    # Run in background with output to file
    evolve run \
        --population $POPULATION \
        --generations $GENERATIONS \
        --tasks $TASKS \
        --seed $SEED \
        --no-weave \
        --output-dir "$OUTPUT_DIR/seed_$SEED" \
        > "$OUTPUT_DIR/seed_$SEED.log" 2>&1 &

    # Store PID
    echo $! > "$OUTPUT_DIR/seed_$SEED.pid"

    echo "  → Run $((i+1)) started (PID: $(cat $OUTPUT_DIR/seed_$SEED.pid))"

    # Small delay to avoid hammering Redis/API
    sleep 2
done

echo ""
echo "All runs started in background."
echo "Monitor progress with: tail -f $OUTPUT_DIR/seed_*.log"
echo ""
echo "To check if runs are complete:"
echo "  ls $OUTPUT_DIR/*/evolution_run.json | wc -l"
echo "  (should be $NUM_SEEDS when all complete)"
echo ""

# Wait for all background jobs
echo "Waiting for all runs to complete..."
wait

echo ""
echo "========================================="
echo "All runs complete!"
echo "========================================="
echo ""
echo "Analyzing results..."

# Run analysis script
python3 - <<'PYTHON'
import json
import glob
import numpy as np
from pathlib import Path

output_dir = Path("data/multi_seed_runs")
run_files = sorted(output_dir.glob("seed_*/evolution_run.json"))

if not run_files:
    print("ERROR: No evolution_run.json files found!")
    exit(1)

print(f"\nFound {len(run_files)} completed runs\n")
print("=" * 80)
print("MULTI-SEED RESULTS SUMMARY")
print("=" * 80)

# Collect metrics from each run
metrics = {
    "training_calibration_gain": [],
    "test_calibration_gain": [],
    "training_final_calibration": [],
    "test_final_calibration": [],
    "fitness_improvement": [],
    "test_best_fitness": [],
}

for run_file in run_files:
    with open(run_file) as f:
        data = json.load(f)

    stats = data.get("generation_stats", [])
    test_results = data.get("test_results", {})

    if not stats:
        continue

    first, last = stats[0], stats[-1]

    # Training metrics
    training_gain = last["avg_prediction_accuracy"] - first["avg_prediction_accuracy"]
    metrics["training_calibration_gain"].append(training_gain)
    metrics["training_final_calibration"].append(last["avg_prediction_accuracy"])
    metrics["fitness_improvement"].append(last["avg_fitness"] - first["avg_fitness"])

    # Test metrics
    if test_results:
        # Approximate test gain (assumes similar starting point)
        test_gain = test_results.get("avg_prediction_accuracy", 0) - first["avg_prediction_accuracy"]
        metrics["test_calibration_gain"].append(test_gain)
        metrics["test_final_calibration"].append(test_results.get("avg_prediction_accuracy", 0))
        metrics["test_best_fitness"].append(test_results.get("best_fitness", 0))

# Print summary statistics
print("\n📊 TRAINING SET PERFORMANCE (Used During Evolution)")
print("-" * 80)
print(f"Calibration Gain:     {np.mean(metrics['training_calibration_gain']):.1%} ± {np.std(metrics['training_calibration_gain']):.1%}")
print(f"Final Calibration:    {np.mean(metrics['training_final_calibration']):.1%} ± {np.std(metrics['training_final_calibration']):.1%}")
print(f"Fitness Improvement:  {np.mean(metrics['fitness_improvement']):.3f} ± {np.std(metrics['fitness_improvement']):.3f}")

if metrics["test_calibration_gain"]:
    print("\n🎯 TEST SET PERFORMANCE (Held-Out, Never Seen)")
    print("-" * 80)
    print(f"Calibration Gain:     {np.mean(metrics['test_calibration_gain']):.1%} ± {np.std(metrics['test_calibration_gain']):.1%}")
    print(f"Final Calibration:    {np.mean(metrics['test_final_calibration']):.1%} ± {np.std(metrics['test_final_calibration']):.1%}")
    print(f"Best Fitness:         {np.mean(metrics['test_best_fitness']):.3f} ± {np.std(metrics['test_best_fitness']):.3f}")

    # Check for overfitting
    train_gain = np.mean(metrics['training_calibration_gain'])
    test_gain = np.mean(metrics['test_calibration_gain'])
    generalization_gap = train_gain - test_gain

    print(f"\n📉 Generalization Gap: {generalization_gap:.1%}")
    if generalization_gap > 0.02:
        print("   ⚠️  WARNING: Significant overfitting detected (>2% gap)")
    else:
        print("   ✓ Good generalization (gap <2%)")

print("\n" + "=" * 80)
print(f"✅ Completed {len(run_files)} independent trials")
print("=" * 80)
print(f"\nDetailed results saved in: {output_dir}/")
PYTHON

echo ""
echo "Multi-seed experiment complete!"
echo "Results saved in: $OUTPUT_DIR/"
