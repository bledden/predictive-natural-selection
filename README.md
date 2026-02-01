# Predictive Natural Selection

**Evolving LLM agent strategies through natural selection on predictive fitness.**

> WeaveHacks 3 Submission — Best Self-Improving Agent

## What It Does

LLM agents have hidden behavioral DNA: their system prompts, reasoning strategies, confidence biases, and temperature settings. Predictive Natural Selection treats these as a **genome** and evolves populations of agents through real natural selection — survival of the most calibrated.

Each generation, agents compete on prediction tasks (trivia, estimation, probability). Fitness is scored on **calibration** (does the agent know what it knows?) and **task accuracy**. The fittest agents reproduce; their genomes cross over and mutate. Weaker strategies go extinct.

### Key Result

Over 20 generations with 20 agents competing on 12 tasks per generation:

| Metric | Gen 0 | Gen 19 | Change |
|--------|-------|--------|--------|
| Raw LLM Calibration | 76.0% | 75.6% | Flat |
| **Evolved Calibration** | **76.0%** | **81.5%** | **+5.5%** |
| Best Individual Fitness | — | 0.832 | — |
| Dominant Strategy | Mixed | Elimination (50%) | Convergent |

The raw LLM calibration stays flat — the base model doesn't change. But the evolved calibration climbs because natural selection discovers that specific confidence biases and reasoning strategies produce better-calibrated predictions. The system literally breeds better self-awareness into agents.

## Architecture

```
┌─────────────────────────────────────────────────────┐
│                  Web Dashboard (Next.js)             │
│  Live Evolution · Fitness Curves · Phylogenetic Tree │
│  Calibration Charts · Trait Distribution · Explorer  │
└────────────────────────┬────────────────────────────┘
                         │ REST + SSE
┌────────────────────────┴────────────────────────────┐
│                  FastAPI Backend                     │
│  Static data endpoints · Live SSE evolution stream   │
└────────────────────────┬────────────────────────────┘
                         │
┌────────────────────────┴────────────────────────────┐
│               Evolution Engine (Python)              │
│                                                      │
│  AgentGenome ──► Evaluator ──► Fitness Scoring       │
│       ▲              │              │                │
│       │         LLM Inference       │                │
│       │        (OpenAI-compat)      │                │
│       │              │              ▼                │
│       └── Crossover + Mutation ◄── Selection         │
│                                                      │
│  W&B Weave: traces every LLM call + evolution step   │
│  Redis: population store + lineage tracking          │
└─────────────────────────────────────────────────────┘
```

### Agent Genome

Each agent carries a genome with evolvable traits:

- **system_prompt** — mutated via LLM-powered rewriting
- **reasoning_style** — chain-of-thought, step-by-step, analogical, debate-self, first-principles, elimination
- **confidence_bias** — adjustment applied to raw confidence estimates
- **temperature** — LLM sampling temperature
- **risk_tolerance** — aggressiveness on uncertain predictions
- **memory_window** / **memory_weighting** — (structural, reserved for future evolution)

### Evolution Mechanics

- **Selection**: Top 30% of population selected as parents
- **Elitism**: Top 2 individuals pass through unchanged
- **Crossover**: Random gene mixing between parent pairs
- **Mutation**: 30% mutation rate per gene, with LLM-assisted prompt mutation
- **Fitness**: 60% prediction calibration + 40% task accuracy

### Fitness Scoring

Fitness measures how well an agent *knows what it knows*:

```
raw_calibration = 1 - |predicted_confidence - outcome|
adjusted_confidence = clamp(predicted_confidence + confidence_bias, 0, 1)
prediction_accuracy = 1 - |adjusted_confidence - outcome|
fitness = 0.6 × prediction_accuracy + 0.4 × task_score
```

The confidence bias gene allows evolution to discover systematic corrections to the LLM's miscalibration — a form of learned self-awareness.

## Quick Start

### Prerequisites

- Python 3.11+
- Node.js 18+
- Redis (for population persistence)
- An OpenAI-compatible API key

### Setup

```bash
# Clone and install
git clone <repo-url>
cd predictive-natural-selection
pip install -e .

# Configure environment
cp .env.example .env
# Edit .env with your API key and model settings

# Install frontend
cd frontend
npm install
cd ..
```

### Run Evolution (CLI)

```bash
# Quick run: 6 agents, 5 generations, 6 tasks
evolve run --population 6 --generations 5 --tasks 6

# Extended run: 20 agents, 20 generations, 12 tasks
evolve run --population 20 --generations 20 --tasks 12

# Without W&B Weave tracing
evolve run --no-weave --population 10 --generations 10 --tasks 8

# Generate visualizations
evolve visualize
```

### Run Dashboard

```bash
# Terminal 1: Start API server
uvicorn src.api:app --host 0.0.0.0 --port 8002

# Terminal 2: Start frontend
cd frontend
npm run dev -- --port 3001

# Open http://localhost:3001
```

The dashboard shows:
- **Live Evolution** — start a new run from the browser with configurable parameters, watch fitness climb in real-time via SSE
- **Metric Cards** — fitness, calibration, task accuracy, dominant strategy
- **Fitness Curves** — avg/best/worst fitness across generations
- **Calibration Chart** — raw vs evolved calibration with evolution gain area
- **Trait Distribution** — reasoning strategy population over time
- **Confidence Bias Evolution** — how confidence corrections evolve
- **Phylogenetic Tree** — full ancestry visualization with strategy coloring
- **Generation Explorer** — drill into any generation, inspect genomes, view per-task results

## Provider Compatibility

Works with any OpenAI-compatible API:

| Provider | Config |
|----------|--------|
| **W&B Inference** | `OPENAI_BASE_URL=https://api.inference.wandb.ai/v1` `MODEL_NAME=deepseek-ai/DeepSeek-V3-0324` |
| **OpenAI** | Leave `OPENAI_BASE_URL` empty, `MODEL_NAME=gpt-4o-mini` |
| **Ollama** | `OPENAI_BASE_URL=http://localhost:11434/v1` `MODEL_NAME=llama3.3` |
| **OpenRouter** | `OPENAI_BASE_URL=https://openrouter.ai/api/v1` `MODEL_NAME=google/gemini-2.5-flash-lite` |

## Tech Stack

**Backend**: Python, FastAPI, Redis, OpenAI SDK, W&B Weave, NetworkX, Matplotlib, Typer, Rich

**Frontend**: Next.js 16, React 19, TypeScript, Tailwind CSS 4, shadcn/ui, Recharts, SWR

## W&B Weave Integration

Every LLM call and evolution step is traced through W&B Weave:
- Individual agent evaluations with input/output
- Fitness scoring breakdowns
- Generation-level aggregations
- Full lineage tracking

This provides complete observability into *why* certain strategies survive and others go extinct.

## Project Structure

```
src/
  main.py              # CLI entry point (Typer)
  api.py               # FastAPI backend + SSE live evolution
  orchestrator.py      # Generation loop orchestration
  evolution.py         # Selection, crossover, mutation
  genome.py            # AgentGenome dataclass
  evaluator.py         # LLM evaluation + fitness scoring
  tasks.py             # Task generation (trivia, estimation, probability)
  population_store.py  # Redis persistence
  visualization.py     # Matplotlib charts
  weave_integration.py # W&B Weave decorators

frontend/
  src/app/page.tsx     # Dashboard layout
  src/lib/api.ts       # SWR data fetching
  src/lib/types.ts     # TypeScript interfaces
  src/components/dashboard/
    live-evolution.tsx  # SSE-powered live run
    metric-cards.tsx    # Summary metrics with sparklines
    fitness-chart.tsx   # Fitness curves (Recharts)
    calibration-chart.tsx
    trait-distribution-chart.tsx
    confidence-bias-chart.tsx
    phylogenetic-tree.tsx  # SVG ancestry tree
    generation-explorer.tsx  # Per-generation genome inspector
```

## License

MIT
