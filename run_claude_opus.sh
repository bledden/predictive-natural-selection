#!/bin/bash

#############################################
# Sequential Claude Opus 4.5 Runs
# Runs three seeds to match GPT-5.2 and DeepSeek
#############################################

set -e

POPULATION=10
GENERATIONS=10
TASKS=8
SEEDS=(42 43 44)
OUTPUT_BASE="data/comprehensive_experiment"

# Claude Opus 4.5
MODEL="claude-opus-4-5-20251101"

echo "========================================="
echo "CLAUDE OPUS 4.5 RUNS"
echo "========================================="
echo "Model: Claude Opus 4.5"
echo "Seeds: ${SEEDS[@]}"
echo "Population: $POPULATION"
echo "Generations: $GENERATIONS"
echo "Tasks/gen: $TASKS"
echo "Output: $OUTPUT_BASE"
echo "========================================="
echo ""

# Check API key
if [ -z "$ANTHROPIC_API_KEY" ]; then
    echo "ERROR: ANTHROPIC_API_KEY not set"
    exit 1
fi
echo "✓ API key validated"
echo ""

# Run each seed sequentially
for seed in "${SEEDS[@]}"; do
    run_name="claude_opus_4_5_seed${seed}"
    run_dir="${OUTPUT_BASE}/${run_name}"
    log_file="${OUTPUT_BASE}/${run_name}.log"

    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo "Running: Claude Opus 4.5 (seed=$seed)"
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

    # Set environment for this run
    export OPENAI_API_KEY="$ANTHROPIC_API_KEY"
    export OPENAI_BASE_URL="https://api.anthropic.com/v1"

    # Run evolution (synchronously)
    .venv/bin/python -m src.main run \
        --model "$MODEL" \
        --base-url "https://api.anthropic.com/v1" \
        --api-key "$ANTHROPIC_API_KEY" \
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

    # Brief pause between runs
    sleep 5
done

echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "ALL CLAUDE OPUS 4.5 RUNS COMPLETE!"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
