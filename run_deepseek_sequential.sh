#!/bin/bash

#############################################
# Sequential DeepSeek Runs
# Runs one seed at a time to avoid rate limits
#############################################

set -e

POPULATION=10
GENERATIONS=10
TASKS=8
SEEDS=(42 43 44)
OUTPUT_BASE="data/comprehensive_experiment"

# DeepSeek via W&B Inference API
MODEL="deepseek-ai/DeepSeek-V3-0324"
BASE_URL="https://api.inference.wandb.ai/v1"

echo "========================================="
echo "SEQUENTIAL DEEPSEEK RUNS"
echo "========================================="
echo "Model: DeepSeek V3.1"
echo "Seeds: ${SEEDS[@]}"
echo "Population: $POPULATION"
echo "Generations: $GENERATIONS"
echo "Tasks/gen: $TASKS"
echo "Output: $OUTPUT_BASE"
echo "========================================="
echo ""

# Check API key
if [ -z "$WANDB_API_KEY" ]; then
    echo "ERROR: WANDB_API_KEY not set"
    exit 1
fi
echo "✓ API key validated"
echo ""

# Run each seed sequentially
for seed in "${SEEDS[@]}"; do
    run_name="deepseek_v3_seed${seed}"
    run_dir="${OUTPUT_BASE}/${run_name}"
    log_file="${OUTPUT_BASE}/${run_name}.log"

    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo "Running: DeepSeek V3 (seed=$seed)"
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

    # Set environment for this run
    export OPENAI_API_KEY="$WANDB_API_KEY"
    export OPENAI_BASE_URL="$BASE_URL"

    # Run evolution (synchronously)
    .venv/bin/python -m src.main run \
        --model "$MODEL" \
        --base-url "$BASE_URL" \
        --population $POPULATION \
        --generations $GENERATIONS \
        --tasks $TASKS \
        --seed $seed \
        --no-weave \
        --output-dir "$run_dir" \
        2>&1 | tee "$log_file"

    echo ""
    echo "✓ Completed: seed=$seed"
    echo ""

    # Brief pause between runs to be safe
    sleep 5
done

echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "ALL DEEPSEEK RUNS COMPLETE!"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
