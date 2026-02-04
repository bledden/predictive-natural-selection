# Predictive Natural Selection

**Evolving LLM agent configurations through natural selection to measure system optimization headroom.**

## The Question

When your AI system underperforms, should you optimize the system (prompts, reasoning strategies, configuration) or upgrade to a better model?

Predictive Natural Selection answers this empirically. It evolves populations of agent configurations using natural selection, then measures the **calibration gap** between raw model performance and evolved system performance. The gap tells you where to invest.

## How It Works

1. **Create a population** of agent configurations (genomes), each with a system prompt, reasoning style, confidence bias, temperature, and risk tolerance
2. **Evaluate each agent** on prediction tasks — trivia, estimation, reasoning — measuring how well they know what they know (calibration)
3. **Select the fittest**, breed them (crossover), mutate some traits, repeat
4. **Measure the gap** between raw model calibration and evolved calibration on a held-out test set

```
Calibration Gap = Evolved Performance - Raw Model Performance

  Positive gap  →  System optimization has headroom, keep tuning
  Near-zero gap →  Already optimized, model upgrade needed
  Negative gap  →  Overfitting — evolution memorized training tasks
```

## Current Findings

We ran 12 experiments across 4 models (3 seeds each):

| Model | Training Gap | Test Gap | Verdict |
|-------|-------------|----------|---------|
| Claude Opus 4.5 | +2.6% | +1.9% | Already optimized |
| GPT-5.2 | +3.6% | -1.4% | Already optimized |
| DeepSeek V3 | +6.2% | -17.8% | Overfitting |
| GPT-4o | +0.2% | -24.0% | Overfitting |

**Key finding:** Evolution consistently improves calibration on training tasks (+2-6%), but these improvements don't generalize to held-out test tasks. This is the core open research question — how to evolve generalizable agent behaviors rather than task-memorized ones.

### What This Means

- Frontier models (Claude Opus 4.5, GPT-5.2) are already well-calibrated out-of-the-box
- Evolution works during training but overfits, especially on weaker models
- The train/test gap is itself a useful diagnostic — it reveals overfitting risk
- Solving the generalization problem is the path to making this tool genuinely useful

## Quick Start

### Prerequisites

- Python 3.11+
- Node.js 18+
- Redis (for population persistence)
- An OpenAI-compatible API key

### Setup

```bash
git clone https://github.com/bledden/predictive-natural-selection.git
cd predictive-natural-selection

# Python backend
python -m venv .venv
source .venv/bin/activate
pip install -e .

# Frontend
cd frontend && npm install && cd ..

# Configure
cp .env.example .env
# Edit .env with your API keys
```

### Run Evolution (CLI)

```bash
# Quick run
evolve run --model gpt-4o --population 10 --generations 10 --tasks 8

# With W&B Weave tracing
evolve run --model gpt-4o --weave-project my-project

# With different providers
evolve run --model deepseek-ai/DeepSeek-V3-0324 \
  --base-url https://api.inference.wandb.ai/v1 \
  --api-key $WANDB_API_KEY

# Generate static visualizations
evolve visualize
```

### Run Dashboard

```bash
# Terminal 1: API server
uvicorn src.api:app --port 8002

# Terminal 2: Frontend
cd frontend && npm run dev

# Open http://localhost:3000
```

The dashboard includes:
- **Live Evolution** — start runs from the browser, watch fitness climb in real-time via SSE
- **Multi-Model Comparison** — switch between experiment results, compare verdicts
- **Fitness Curves** — avg/best/worst fitness across generations
- **Calibration Charts** — raw vs evolved calibration with gap visualization
- **Phylogenetic Tree** — full ancestry visualization showing which traits survived
- **Trait Distribution** — reasoning strategy populations over time
- **Generation Explorer** — drill into any generation, inspect individual genomes

## Architecture

```
┌──────────────────────────────────────────────────────┐
│                  Web Dashboard (Next.js)               │
│  Live Evolution · Model Comparison · Phylogenetic Tree │
│  Calibration Charts · Trait Distribution · Explorer    │
└─────────────────────────┬──────────────────────────────┘
                          │ REST + SSE
┌─────────────────────────┴──────────────────────────────┐
│                  FastAPI Backend                         │
│  Static endpoints · Live SSE stream · Model switching   │
└─────────────────────────┬──────────────────────────────┘
                          │
┌─────────────────────────┴──────────────────────────────┐
│               Evolution Engine (Python)                  │
│                                                          │
│  AgentGenome ──► Evaluator ──► Fitness Scoring           │
│       ▲              │              │                    │
│       │         LLM Inference       │                    │
│       │        (OpenAI-compat)      │                    │
│       │              │              ▼                    │
│       └── Crossover + Mutation ◄── Selection             │
│                                                          │
│  W&B Weave: traces every LLM call + evolution step       │
│  Redis: population store + lineage tracking              │
└──────────────────────────────────────────────────────────┘
```

### Agent Genome

Each agent carries a genome with evolvable traits:

- **system_prompt** — mutated via LLM-powered rewriting
- **reasoning_style** — chain-of-thought, step-by-step, analogical, debate-self, first-principles, elimination
- **confidence_bias** — systematic correction to raw confidence estimates
- **temperature** — LLM sampling temperature
- **risk_tolerance** — aggressiveness on uncertain predictions
- **memory_window / memory_weighting** — structural, reserved for future evolution

### Fitness Function

```
prediction_accuracy = 1 - |adjusted_confidence - outcome|
fitness = 0.6 × prediction_accuracy + 0.4 × task_accuracy
```

60% calibration, 40% accuracy. Rationale in [docs/research/FITNESS_FUNCTION_RATIONALE.md](docs/research/FITNESS_FUNCTION_RATIONALE.md).

### Methodological Safeguards

- **Train/val/test split** (60/20/20) with stratification by task type
- **Multi-seed validation** (3 seeds per model) for reproducibility
- **Held-out test evaluation** — final metrics on tasks evolution never saw
- **Statistical reporting** — mean, std, coefficient of variation

## Open Research Questions

### 1. Overfitting (Primary)
Evolution improves training calibration but doesn't generalize. Potential approaches:
- Larger, more diverse task sets
- Regularization (penalize genome complexity, limit mutation magnitude)
- Validation-based early stopping
- Cross-validation across task subsets during evolution
- Evolve on task *types* rather than specific tasks

### 2. Task Design
Current tasks (42 total: trivia, estimation, reasoning) may be too narrow. Need:
- More task types (classification, sentiment, extraction, coding)
- Real-world tasks from actual use cases
- Dynamic task generation to prevent memorization

### 3. Genome Expressiveness
Current genome may be too limited to capture meaningful behavioral variation:
- Add few-shot examples as evolvable traits
- Evolve tool usage strategies
- Multi-turn conversation genomes
- Ensemble genomes (multiple agents collaborating)

### 4. Fitness Function
Current 60/40 calibration/accuracy split is arbitrary:
- Explore different weightings
- Add diversity pressure to prevent premature convergence
- Multi-objective evolution (Pareto frontiers)

## Provider Compatibility

Works with any OpenAI-compatible API:

| Provider | Example |
|----------|---------|
| **OpenAI** | `--model gpt-4o` |
| **W&B Inference** | `--model deepseek-ai/DeepSeek-V3-0324 --base-url https://api.inference.wandb.ai/v1` |
| **Ollama** | `--model llama3.3 --base-url http://localhost:11434/v1` |
| **OpenRouter** | `--model google/gemini-2.5-flash-lite --base-url https://openrouter.ai/api/v1` |

## Project Structure

```
src/
  main.py              # CLI entry point (Typer)
  api.py               # FastAPI backend + SSE + model switching
  orchestrator.py      # Generation loop orchestration
  evolution.py         # Selection, crossover, mutation
  genome.py            # AgentGenome dataclass
  evaluator.py         # LLM evaluation + fitness scoring
  tasks.py             # Task generation + train/val/test split
  population_store.py  # Redis persistence
  visualization.py     # Matplotlib charts
  weave_integration.py # W&B Weave tracing
  validation.py        # Historical + live + generalization validation

frontend/
  src/app/page.tsx
  src/components/dashboard/
    diagnosis-hero.tsx       # Main verdict display
    model-comparison.tsx     # Multi-model comparison + switching
    live-evolution.tsx       # SSE-powered live runs
    metric-cards.tsx         # Summary metrics
    gap-chart.tsx            # Calibration gap visualization
    fitness-chart.tsx        # Fitness curves
    calibration-chart.tsx    # Raw vs evolved calibration
    trait-distribution-chart.tsx
    confidence-bias-chart.tsx
    phylogenetic-tree.tsx    # SVG ancestry tree
    generation-explorer.tsx  # Per-generation inspector
    prescription.tsx         # Configuration recommendations

data/
  comprehensive_experiment/  # 9 frontier model runs
  previous_gen_experiment/   # 3 previous-gen model runs

docs/
  research/                  # Methodology, issues, rationale
  hackathon/                 # Original WeaveHacks 3 materials
```

## Tech Stack

**Backend**: Python 3.11+, FastAPI, Redis, OpenAI SDK, W&B Weave, NetworkX, Matplotlib, Typer, Rich

**Frontend**: Next.js 16, React 19, TypeScript, Tailwind CSS 4, shadcn/ui, Recharts, SWR

## Origin

Built at [WeaveHacks 3](https://weavehacks.com) (January 31 - February 1, 2026). Now an open source research project.

## License

MIT
