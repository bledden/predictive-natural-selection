#!/bin/bash

#############################################
# Previous-Generation Models Experiment
# Tests: GPT-4o, Claude Sonnet 3.5, Claude Sonnet 4.5, DeepSeek-V2.5
# Purpose: Show system optimization value for older models
#############################################

set -e

POPULATION=10
GENERATIONS=10
TASKS=8
SEEDS=(42 43 44)
OUTPUT_BASE="data/previous_gen_experiment"

echo "========================================="
echo "PREVIOUS-GENERATION MODELS EXPERIMENT"
echo "========================================="
echo "Models: 2 (GPT-4o, DeepSeek-V2.5)"
echo "Seeds per model: ${#SEEDS[@]} (${SEEDS[@]})"
echo "Total runs: $((4 * ${#SEEDS[@]}))"
echo "Population: $POPULATION"
echo "Generations: $GENERATIONS"
echo "Tasks/gen: $TASKS"
echo "Output: $OUTPUT_BASE"
echo "========================================="
echo ""

# Check API keys
if [ -z "$OPENAI_API_KEY" ]; then
    echo "ERROR: OPENAI_API_KEY not set"
    exit 1
fi

if [ -z "$ANTHROPIC_API_KEY" ]; then
    echo "ERROR: ANTHROPIC_API_KEY not set"
    exit 1
fi

if [ -z "$WANDB_API_KEY" ]; then
    echo "ERROR: WANDB_API_KEY not set (needed for DeepSeek)"
    exit 1
fi

echo "✓ API keys validated"
echo ""

# Model configurations: "model_id|base_url|api_key_var|display_name"
MODELS=(
    "gpt-4o||OPENAI_API_KEY|GPT-4o"
    "deepseek-ai/DeepSeek-V2.5|https://api.inference.wandb.ai/v1|WANDB_API_KEY|DeepSeek-V2.5"
)

run_count=0
total_runs=$((${#MODELS[@]} * ${#SEEDS[@]}))

# Run each model sequentially (to avoid rate limits)
for model_spec in "${MODELS[@]}"; do
    IFS='|' read -r model base_url api_key_var display_name <<< "$model_spec"

    echo ""
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo "MODEL: $display_name"
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

    for seed in "${SEEDS[@]}"; do
        run_count=$((run_count + 1))

        # Create safe run name (replace dots and hyphens)
        safe_name=$(echo "$display_name" | tr '.' '_' | tr '-' '_' | tr '[:upper:]' '[:lower:]')
        run_name="${safe_name}_seed${seed}"
        run_dir="${OUTPUT_BASE}/${run_name}"
        log_file="${OUTPUT_BASE}/${run_name}.log"

        echo ""
        echo "[$run_count/$total_runs] Running: $display_name (seed=$seed)"
        echo "  → Output: $run_dir"
        echo "  → Log: $log_file"

        # Set API key for this run
        if [ -z "$base_url" ]; then
            unset OPENAI_BASE_URL
        else
            export OPENAI_BASE_URL="$base_url"
        fi

        export OPENAI_API_KEY="${!api_key_var}"

        # Run evolution
        .venv/bin/python -m src.main run \
            --model "$model" \
            ${base_url:+--base-url "$base_url"} \
            --population $POPULATION \
            --generations $GENERATIONS \
            --tasks $TASKS \
            --seed $seed \
            --no-weave \
            --output-dir "$run_dir" \
            2>&1 | tee "$log_file"

        echo "  ✓ Completed: $display_name seed=$seed"

        # Brief pause between runs
        sleep 3
    done
done

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "ALL RUNS COMPLETE!"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "Analyzing results..."

# Run analysis
.venv/bin/python analyze_previous_gen_results.py

echo ""
echo "✓ Experiment complete!"
