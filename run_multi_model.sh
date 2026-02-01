#!/bin/bash
# Run evolution on multiple models to compare their evolutionary ceilings
# Usage: ./run_multi_model.sh [population] [generations] [tasks]

set -e

POPULATION=${1:-20}
GENERATIONS=${2:-20}
TASKS=${3:-12}
SEED=42  # Use same seed for fair comparison
OUTPUT_DIR="data/multi_model_runs"

mkdir -p "$OUTPUT_DIR"

echo "========================================="
echo "Multi-Model Comparison Experiment"
echo "========================================="
echo "Population: $POPULATION"
echo "Generations: $GENERATIONS"
echo "Tasks per generation: $TASKS"
echo "Seed: $SEED (same for all models)"
echo "Output directory: $OUTPUT_DIR"
echo "========================================="
echo ""

# Model configurations
# Format: "model_id|base_url|display_name"
# Using latest available models as of Feb 2026
MODELS=(
    "gpt-5.2|https://api.openai.com/v1|GPT-5.2"
    "gpt-4.1|https://api.openai.com/v1|GPT-4.1"
    "deepseek-ai/DeepSeek-V3-0324|https://api.inference.wandb.ai/v1|DeepSeek V3.1"
)

# Check required API keys
echo "Checking API keys..."
if [[ -z "$WANDB_API_KEY" ]]; then
    echo "❌ ERROR: WANDB_API_KEY not set (needed for DeepSeek)"
    exit 1
fi
if [[ -z "$OPENAI_API_KEY" ]]; then
    echo "⚠️  WARNING: OPENAI_API_KEY not set (GPT-4o-mini will be skipped)"
    MODELS=("${MODELS[@]/gpt-4o-mini*/}")
fi
if [[ -z "$ANTHROPIC_API_KEY" ]]; then
    echo "⚠️  WARNING: ANTHROPIC_API_KEY not set (Claude will be skipped)"
    MODELS=("${MODELS[@]/claude*/}")
fi
echo "✓ API keys validated"
echo ""

for model_spec in "${MODELS[@]}"; do
    if [[ -z "$model_spec" ]]; then
        continue
    fi

    IFS='|' read -r model_id base_url display_name <<< "$model_spec"
    safe_name=$(echo "$display_name" | tr ' ' '_' | tr '[:upper:]' '[:lower:]')

    echo "Starting evolution for: $display_name"
    echo "  Model: $model_id"
    echo "  API: $base_url"

    # Determine API key based on provider
    if [[ "$base_url" == *"wandb"* ]]; then
        API_KEY="$WANDB_API_KEY"
    elif [[ "$base_url" == *"openai"* ]]; then
        API_KEY="$OPENAI_API_KEY"
    elif [[ "$base_url" == *"anthropic"* ]]; then
        API_KEY="$ANTHROPIC_API_KEY"
        # Anthropic SDK needs different env var
        export ANTHROPIC_API_KEY="$API_KEY"
    fi

    # Run evolution
    MODEL_NAME="$model_id" \
    OPENAI_BASE_URL="$base_url" \
    OPENAI_API_KEY="$API_KEY" \
    evolve run \
        --population $POPULATION \
        --generations $GENERATIONS \
        --tasks $TASKS \
        --seed $SEED \
        --no-weave \
        --output-dir "$OUTPUT_DIR/$safe_name" \
        > "$OUTPUT_DIR/${safe_name}.log" 2>&1 &

    echo $! > "$OUTPUT_DIR/${safe_name}.pid"
    echo "  → Started (PID: $(cat $OUTPUT_DIR/${safe_name}.pid))"
    echo ""

    # Small delay between models
    sleep 5
done

echo "All model runs started in background."
echo "Monitor progress with: tail -f $OUTPUT_DIR/*.log"
echo ""

# Wait for all runs to complete
echo "Waiting for all runs to complete..."
wait

echo ""
echo "========================================="
echo "All runs complete!"
echo "========================================="
echo ""
echo "Analyzing results..."

# Run comparison analysis
python3 - <<'PYTHON'
import json
import glob
from pathlib import Path

output_dir = Path("data/multi_model_runs")
run_dirs = sorted([d for d in output_dir.iterdir() if d.is_dir()])

if not run_dirs:
    print("ERROR: No run directories found!")
    exit(1)

print("\n" + "=" * 80)
print("MULTI-MODEL COMPARISON RESULTS")
print("=" * 80)
print("")

results = []

for run_dir in run_dirs:
    run_file = run_dir / "evolution_run.json"
    if not run_file.exists():
        print(f"⚠️  Skipping {run_dir.name} - no results file")
        continue

    with open(run_file) as f:
        data = json.load(f)

    stats = data.get("generation_stats", [])
    test_results = data.get("test_results", {})

    if not stats:
        continue

    first, last = stats[0], stats[-1]

    model_name = run_dir.name.replace("_", " ").title()

    # Collect metrics
    result = {
        "model": model_name,
        "raw_cal_start": first.get("avg_raw_calibration", 0),
        "raw_cal_end": last.get("avg_raw_calibration", 0),
        "evolved_cal_start": first["avg_prediction_accuracy"],
        "evolved_cal_end": last["avg_prediction_accuracy"],
        "train_gap": last["avg_prediction_accuracy"] - last.get("avg_raw_calibration", 0),
        "test_cal": test_results.get("avg_prediction_accuracy", 0) if test_results else 0,
        "test_gap": (test_results.get("avg_prediction_accuracy", 0) -
                     test_results.get("avg_raw_calibration", 0)) if test_results else 0,
        "fitness_gain": last["avg_fitness"] - first["avg_fitness"],
    }
    results.append(result)

# Sort by test gap (descending)
results.sort(key=lambda x: x["test_gap"], reverse=True)

# Print table
print(f"{'Model':<25} {'Raw Cal':<12} {'Evolved Cal':<12} {'Gap':<8} {'Test Gap':<10} {'Verdict'}")
print("-" * 95)

for r in results:
    verdict = "🔧 System" if r["test_gap"] > 0.04 else "🤖 Model" if r["test_gap"] < 0.02 else "⚖️  Mixed"

    print(f"{r['model']:<25} "
          f"{r['raw_cal_end']:>6.1%} →      "
          f"{r['evolved_cal_end']:>6.1%} →      "
          f"{r['train_gap']:>+5.1%}    "
          f"{r['test_gap']:>+5.1%}      "
          f"{verdict}")

print("")
print("Legend:")
print("  🔧 System (>4% gap)  → Your system config is the bottleneck")
print("  🤖 Model (<2% gap)   → This model is already well-optimized, needs upgrade")
print("  ⚖️  Mixed (2-4% gap)  → Both system tuning and model upgrade would help")
print("")

# Key insights
best_gap = max(r["test_gap"] for r in results)
worst_gap = min(r["test_gap"] for r in results)
gap_range = best_gap - worst_gap

print("=" * 80)
print("KEY INSIGHTS")
print("=" * 80)
print(f"• Largest optimization gap:  {best_gap:>+5.1%} ({[r['model'] for r in results if r['test_gap'] == best_gap][0]})")
print(f"• Smallest optimization gap: {worst_gap:>+5.1%} ({[r['model'] for r in results if r['test_gap'] == worst_gap][0]})")
print(f"• Range across models:       {gap_range:>5.1%}")
print("")

if gap_range > 0.03:
    print("✓ System optimization impact varies significantly by model")
    print("  → Some models benefit more from config tuning than others")
else:
    print("✓ System optimization impact is consistent across models")
    print("  → All models have similar headroom for config improvement")

print("\n" + "=" * 80)
print(f"✅ Compared {len(results)} models")
print("=" * 80)
print(f"\nDetailed results in: {output_dir}/")
PYTHON

echo ""
echo "Multi-model comparison complete!"
echo "Results saved in: $OUTPUT_DIR/"
