# Predictive Natural Selection — Context for Analysis

## Project Summary

Predictive Natural Selection is a system that evolves LLM agent behaviors through genuine natural selection to answer one question: **"Do you need a better system — or a better model?"**

A population of LLM agents with different configurations (system prompts, reasoning strategies, confidence biases, temperature settings) compete on prediction tasks. Agents that are well-calibrated — meaning they accurately know what they know and don't know — survive and reproduce. Poorly calibrated agents go extinct. Over generations, the population converges on behavioral configurations that extract maximum performance from the underlying model without changing the model itself.

The key finding: raw LLM calibration stays flat (~76%) across all generations because the model never changes. But evolved calibration climbs to ~82% through behavioral optimization alone. That +5.5% gap is **free performance** hidden in system configuration. If evolution can't improve things further, you need a better model.

---

## The Core Insight

Most teams that deploy LLM agents never know whether poor performance comes from the model or from how they've configured it. Fine-tuning is expensive. Model upgrades are disruptive. But what if the problem was just a bad system prompt, wrong temperature, or miscalibrated confidence?

This system uses evolutionary pressure as a diagnostic tool:
- **Large gap between raw and evolved calibration** → Your system configuration is leaving performance on the table. You don't need a better model — you need better configuration. The system provides the exact configuration to use.
- **Small gap** → Your system is already near-optimal for this model. Further improvement requires a better model or fine-tuning.

The output is a **prescription**: the specific system prompt, reasoning strategy, confidence bias correction, temperature, and risk tolerance that evolution converged on, complete with confidence intervals and a copyable config block.

---

## How It Works

### Agent Genome

Each agent's "DNA" is a structured configuration called an `AgentGenome`:

| Trait | Type | Range | Description |
|-------|------|-------|-------------|
| `system_prompt` | string | 10 templates | The instruction prompt shaping agent behavior |
| `reasoning_style` | enum | 6 strategies | How the agent approaches problems |
| `confidence_bias` | float | -0.3 to +0.3 | Systematic adjustment to the LLM's raw confidence output |
| `temperature` | float | 0.1 to 1.5 | LLM sampling temperature |
| `risk_tolerance` | float | 0.0 to 1.0 | Willingness to commit to uncertain predictions |
| `memory_window` | int | 1 to 10 | How many past results to consider |
| `memory_weighting` | string | 3 options | How to weight past results (recency, relevance, success-rate) |
| `generation` | int | — | Which generation created this genome |
| `parent_ids` | list | — | Ancestry tracking for phylogenetic visualization |

**Reasoning Strategies** (the 6 options that compete for survival):
1. **Chain-of-thought** — methodical, step-by-step reasoning
2. **Step-by-step** — explicit decomposition into steps
3. **Analogical** — relate problems to known solutions
4. **Debate-self** — consider multiple viewpoints and argue both sides
5. **First-principles** — break down to fundamental truths
6. **Elimination** — reason by removing incorrect options

### Evaluation Tasks

45 fixed tasks across three categories, each with a known ground truth and difficulty rating (0.1 to 0.9):

- **Trivia** (15 tasks): Factual questions ranging from easy ("Chemical symbol for gold?" → Au, difficulty 0.1) to tricky ("What color is a polar bear's skin?" → Black, difficulty 0.7)
- **Estimation** (12 tasks): Fermi-style problems from straightforward ("Bones in the adult human body?" → 206, difficulty 0.3) to hard ("Piano tuners in Chicago?" → ~200, difficulty 0.9)
- **Reasoning** (15 tasks): Logic puzzles and cognitive traps ("Bat + ball cost $1.10, bat costs $1 more than ball, what does the ball cost?" → $0.05, difficulty 0.5)

Tasks are fixed across all generations using a seed, so fitness scores are directly comparable. Each generation evaluates every agent on a random subset of 8-12 tasks.

### Fitness Scoring

For each agent on each task:

1. Agent receives the task and must predict: its answer, and its confidence (0-100%) that the answer is correct
2. The system compares against ground truth to determine if the answer is correct
3. Fitness is computed as:

```
raw_calibration = 1.0 - |predicted_confidence - actual_outcome|
adjusted_confidence = clamp(predicted_confidence + confidence_bias, 0, 1)
prediction_accuracy = 1.0 - |adjusted_confidence - actual_outcome|
task_score = is_correct * (0.5 + 0.5 * task_difficulty)

fitness = 0.6 * prediction_accuracy + 0.4 * task_score
```

The 60/40 split means calibration matters more than raw accuracy. An agent that says "I'm 30% confident" and gets it wrong (calibration = 0.70) scores better than one that says "I'm 90% confident" and gets it wrong (calibration = 0.10).

The `confidence_bias` gene is the key innovation: evolution discovers systematic corrections to the LLM's miscalibration. If the model is consistently overconfident by ~15%, evolution converges on a confidence_bias of approximately -0.15, producing better-calibrated outputs without changing the model.

### Evolutionary Algorithm

Each generation:

1. **Evaluate**: All agents run on all tasks concurrently (asyncio with semaphore for rate limiting)
2. **Select**: Top 30% of agents by aggregated fitness survive as the breeding pool
3. **Elite preservation**: Top 2 agents pass unchanged to the next generation
4. **Crossover**: Random pairs from the breeding pool produce children. Each gene is independently inherited from one parent
5. **Mutation**: 30% chance per gene to mutate. Mutations are bounded and realistic:
   - `system_prompt`: random selection from 10 templates
   - `reasoning_style`: random selection from 6 strategies
   - `confidence_bias`: ±0.1, bounded to [-0.3, +0.3]
   - `temperature`: ±0.2, bounded to [0.1, 1.5]
   - `risk_tolerance`: ±0.15, bounded to [0.0, 1.0]
   - `memory_window`: ±2, bounded to [1, 10]
6. **Fill population**: Continue crossover + mutation until population reaches target size

Typical run: 20 agents, 20 generations, 12 tasks per generation = ~4,800 LLM calls. With concurrency, completes in 5-10 minutes.

---

## Architecture

### Backend (Python)

```
src/
├── main.py              # Typer CLI: `evolve run`, `evolve visualize`
├── api.py               # FastAPI backend with CORS, SSE live evolution
├── orchestrator.py      # Generation loop: evaluate → select → reproduce
├── evolution.py         # Selection, crossover, mutation operators
├── genome.py            # AgentGenome dataclass + random initialization
├── evaluator.py         # LLM evaluation + fitness scoring
├── tasks.py             # 45 fixed tasks (trivia, estimation, reasoning)
├── population_store.py  # Redis persistence for genomes and fitness
├── visualization.py     # Matplotlib chart generation
└── weave_integration.py # W&B Weave observability decorators
```

**API Endpoints:**
| Endpoint | Description |
|----------|-------------|
| `GET /api/run` | Run summary: generations, population size, calibration gain, extinct strategies |
| `GET /api/generations` | Per-generation stats: avg/best/worst fitness, calibration, strategy distribution |
| `GET /api/genomes` | All genomes across all generations |
| `GET /api/results/{gen}` | Per-task evaluation results for a generation |
| `GET /api/phylogeny` | Full family tree as nodes + edges |
| `GET /api/prescription` | Actionable configuration recommendation with converged traits |
| `GET /api/live/run` | SSE stream for real-time evolution (start → generation events → complete) |

**LLM Backend:** DeepSeek V3.1 via W&B Inference API (OpenAI-compatible). Configurable to use any OpenAI-compatible endpoint (OpenAI, Anthropic, Gemini, Ollama, OpenRouter).

### Frontend (Next.js 16 + TypeScript)

```
frontend/src/
├── app/page.tsx                              # Main dashboard layout
├── lib/api.ts                                # SWR data fetching hooks
├── lib/types.ts                              # TypeScript interfaces
└── components/dashboard/
    ├── diagnosis-hero.tsx                     # Large verdict card: gap %, recommendation
    ├── prescription.tsx                       # Actionable config: traits, prompt, JSON export
    ├── metric-cards.tsx                       # System Gap, Model Baseline, System Optimized, Dominant Strategy
    ├── gap-chart.tsx                          # Raw vs evolved calibration with shaded gap area
    ├── calibration-chart.tsx                  # System vs Model performance over generations
    ├── fitness-chart.tsx                      # Avg/best/worst fitness evolution
    ├── trait-distribution-chart.tsx           # Reasoning strategy population over time
    ├── confidence-bias-chart.tsx              # Confidence bias convergence
    ├── phylogenetic-tree.tsx                  # SVG family tree of agent lineages
    ├── generation-explorer.tsx                # Per-generation genome and result inspector
    ├── live-evolution.tsx                     # Run new experiments with real-time SSE streaming
    ├── header.tsx                             # "Do you need a better system — or a better model?"
    └── footer.tsx
```

**Tech stack:** Next.js 16, React 19, TypeScript, Tailwind CSS 4, shadcn/ui, Recharts, SWR.

---

## Dashboard Flow (Top to Bottom)

The dashboard is designed as a diagnostic narrative:

1. **Diagnosis Hero** — The headline finding: "+5.5% from system optimization alone" with a color-coded verdict (green = system optimization available, amber = moderate gains, red = model upgrade needed). Links to the prescription below.

2. **Metric Cards** — Four summary cards: System Gap (the key number), Model Baseline (raw LLM calibration, unchanged), System Optimized (evolved calibration), Dominant Strategy (what reasoning approach survived).

3. **Prescription** — The actionable output:
   - Recommended settings with population-converged values and standard deviations
   - The highest-fitness agent's system prompt (copyable)
   - Export configuration as JSON (copyable)
   - "What to avoid" — strategies that went extinct or near-extinct

4. **Gap Chart** — Full-width visualization showing the flat raw calibration line vs the climbing evolved calibration line, with the gap between them shaded as "free performance."

5. **System vs Model Performance** — Side-by-side charts showing calibration and fitness trajectories over generations.

6. **How Evolution Optimized the System** — Trait distribution (which strategies survived) and confidence bias convergence (how the population learned to correct for model overconfidence).

7. **Run New Experiment** — Interactive controls to run a new evolution with custom population size, generation count, and task count. Real-time streaming of results.

8. **Evolutionary Lineage** — Phylogenetic tree showing parent-child relationships and strategy coloring.

9. **Generation Explorer** — Detailed per-generation data: individual genomes, per-task results, fitness breakdowns.

---

## Key Results (From Actual Evolution Run)

| Metric | Value |
|--------|-------|
| Population size | 20 agents |
| Generations | 20 |
| Tasks per generation | 12 |
| Total LLM calls | ~4,800 |
| Raw LLM calibration (start) | 76.0% |
| Raw LLM calibration (end) | 76.0% (unchanged — same model) |
| Evolved calibration (start) | 76.0% |
| Evolved calibration (end) | 81.5% |
| **System optimization gap** | **+5.5%** |
| Initial avg fitness | ~0.55 |
| Final avg fitness | ~0.68 |
| Fitness improvement | +23.6% |
| Dominant surviving strategy | Chain-of-thought |
| Extinct strategies | Varied by run |

The raw calibration line staying flat is the proof that the model itself doesn't change. All improvement comes from behavioral evolution: better system prompts, optimized confidence corrections, converged temperature and risk settings.

---

## The Prescription System

The `/api/prescription` endpoint analyzes the final generation's population and produces:

1. **Converged traits**: Mean and standard deviation of each genome trait across the surviving population. Low std = high confidence in the recommendation.
2. **Best genome**: The single highest-fitness agent's complete configuration, including its system prompt.
3. **Confidence bias correction**: If evolution converged on confidence_bias = -0.15, the model is systematically overconfident by ~15%. The prescription advises applying a -15% correction to all confidence outputs.
4. **Strategy recommendations**: Which reasoning style dominated, which went extinct, which are near-extinct.
5. **Copyable configuration**: A JSON block with all recommended settings that can be directly applied to a production LLM agent.

---

## Target Audience

1. **Developers building LLM agent systems** who want to tune behavior without fine-tuning. Run evolution as a diagnostic, get a prescription, apply the optimized config.
2. **Eval and benchmarking teams** who want to understand whether poor calibration is a model problem or a configuration problem before investing in fine-tuning.
3. **Researchers studying emergent agent behaviors** — which reasoning strategies survive selection pressure? What does population convergence reveal about optimal LLM usage patterns?

---

## Technical Details

- **Language**: Python 3.11+ (backend), TypeScript (frontend)
- **Dependencies**: FastAPI, uvicorn, Redis, OpenAI SDK, W&B Weave, networkx, matplotlib, numpy, pydantic, rich, typer
- **Frontend**: Next.js 16, React 19, Tailwind CSS 4, shadcn/ui, Recharts, SWR
- **Ports**: Frontend on 3001, API on 8002
- **Data persistence**: Evolution results saved to `data/evolution_run.json`. Redis used for live population management.
- **Observability**: W&B Weave decorators trace every LLM call, fitness evaluation, and generation step.

---

## Hackathon Context

- **Event**: WeaveHacks 3 (W&B AI Agent Hackathon), January 31 - February 1, 2026
- **Target prize**: Best Self-Improving Agent ($1,000 + TRMNL e-ink frame)
- **Submission deadline**: Sunday February 1, 1:30 PM

---

## What to Analyze

If you are another model analyzing this project, consider:

1. **Is the "system vs model" diagnostic framing compelling?** Does the evolutionary ceiling concept clearly communicate value?
2. **Are there gaps in the dashboard's narrative flow?** Does the top-to-bottom diagnostic → prescription → evidence structure make sense?
3. **Is the prescription actionable enough?** Would a developer know exactly what to change in their system after reading it?
4. **What additional analysis could be derived from the evolution data?** (e.g., task-type-specific recommendations, failure mode clustering, strategy-task affinity matrices)
5. **How could this system be extended?** (e.g., LoRA adapter evolution, multi-model comparison runs, automated fine-tuning data generation)
6. **Is the fitness function well-designed?** Does the 60% calibration / 40% accuracy split produce meaningful selection pressure?
7. **Are there presentation improvements for the hackathon demo?** What would make the judges immediately understand the value?
