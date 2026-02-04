# v0 Prompt: Predictive Natural Selection Dashboard

## What This Is

A real-time dashboard for a genetic algorithm that evolves LLM agent strategies through natural selection. Agents compete on prediction tasks. Successful predictors reproduce with mutations; poor predictors die. The dashboard visualizes the evolutionary dynamics.

## Data API

The frontend fetches from a FastAPI backend at `http://localhost:8000`. All endpoints return JSON.

### GET /api/run — Run Summary
```json
{
  "total_generations": 20,
  "population_size": 20,
  "initial_avg_fitness": 0.693,
  "final_avg_fitness": 0.751,
  "fitness_improvement": 0.059,
  "best_fitness": 0.833,
  "initial_raw_calibration": 0.762,
  "final_raw_calibration": 0.761,
  "initial_evolved_calibration": 0.744,
  "final_evolved_calibration": 0.835,
  "initial_task_accuracy": 0.817,
  "final_task_accuracy": 0.829,
  "dominant_strategy": "step-by-step",
  "strategy_counts": {"step-by-step": 8, "chain-of-thought": 3, "elimination": 4, "debate-self": 3, "first-principles": 2},
  "extinct_strategies": []
}
```

### GET /api/generations — Per-Generation Stats (array)
```json
[
  {
    "generation": 0,
    "population_size": 20,
    "avg_fitness": 0.693,
    "best_fitness": 0.756,
    "worst_fitness": 0.589,
    "avg_raw_calibration": 0.762,
    "avg_prediction_accuracy": 0.744,
    "avg_task_accuracy": 0.817,
    "dominant_reasoning": "debate-self",
    "dominant_memory": "relevance",
    "elapsed_seconds": 26.8
  }
]
```

### GET /api/genomes — All Genomes (array)
```json
[
  {
    "genome_id": "a1b2c3d4",
    "system_prompt": "You are a careful, methodical thinker...",
    "reasoning_style": "chain-of-thought",
    "memory_window": 5,
    "memory_weighting": "recency",
    "confidence_bias": 0.12,
    "risk_tolerance": 0.65,
    "temperature": 0.8,
    "generation": 3,
    "parent_ids": ["e5f6g7h8", "i9j0k1l2"],
    "fitness_history": []
  }
]
```

### GET /api/phylogeny — Phylogenetic Tree Graph
```json
{
  "nodes": [
    {"id": "a1b2c3d4", "generation": 0, "reasoning_style": "chain-of-thought", "confidence_bias": 0.12, "temperature": 0.8, "system_prompt": "You are a careful..."}
  ],
  "edges": [
    {"source": "e5f6g7h8", "target": "a1b2c3d4"}
  ]
}
```

### GET /api/results/{generation} — Eval Results for One Generation
```json
[
  {
    "generation": 5,
    "genome_id": "a1b2c3d4",
    "task_id": "trivia_001",
    "predicted_confidence": 0.85,
    "predicted_answer": "1",
    "ground_truth": "1",
    "is_correct": true,
    "raw_calibration": 0.85,
    "prediction_accuracy": 0.92,
    "fitness": 0.82
  }
]
```

## Page Layout

Build a single-page Next.js dashboard with dark theme (black/slate background, vibrant accents). Use Recharts for charts and shadcn/ui components.

### Header
- Title: "Predictive Natural Selection" in bold
- Subtitle: "Evolving LLM Agent Strategies Through Natural Selection"
- Small "Powered by W&B Weave" badge in top right

### Row 1: Key Metrics (4 stat cards)
1. **Fitness** — final avg fitness with +/- improvement badge, small sparkline
2. **Evolved Calibration** — final value with improvement from initial, show raw vs evolved
3. **Task Accuracy** — final percentage
4. **Dominant Strategy** — name + count (e.g., "step-by-step (8/20)")

### Row 2: Main Charts (2 columns)
**Left: Fitness Curves** (line chart)
- 3 lines: average (blue), best (green), worst (red with low opacity)
- Shaded band between worst and best
- X: Generation, Y: Fitness (0-1)

**Right: Calibration & Accuracy** (line chart)
- 3 lines: Raw LLM Calibration (teal, dashed), Evolved Calibration (purple, solid), Task Accuracy (orange)
- Shaded area between raw and evolved calibration labeled "Evolution Gain"
- X: Generation, Y: Accuracy (0-1)

### Row 3: Evolution Dynamics (2 columns)
**Left: Trait Distribution** (stacked area or stacked bar chart)
- Each reasoning style is a different color
- Colors: chain-of-thought=#e74c3c, step-by-step=#3498db, analogical=#2ecc71, debate-self=#f39c12, first-principles=#9b59b6, elimination=#1abc9c
- X: Generation, Y: Proportion (0-1)

**Right: Confidence Bias Evolution** (line chart with std dev band)
- Red line for average confidence bias over generations
- Shaded band for standard deviation
- Horizontal dashed line at y=0 (neutral)
- X: Generation, Y: Confidence Bias

### Row 4: Phylogenetic Tree (full width)
- Interactive tree/graph visualization
- Nodes positioned by generation (x-axis) and spread vertically
- Nodes colored by reasoning style (same colors as trait distribution)
- Edges from parent to child
- Hover on node shows: genome ID, reasoning style, confidence bias, temperature, system prompt snippet
- Use a force-directed or tree layout (d3-force or similar)

### Row 5: Generation Explorer (full width)
- Slider or step control to select a generation (0 to N)
- Table showing all agents in that generation:
  - Genome ID (truncated), Reasoning Style (colored badge), Confidence Bias, Temperature, Fitness, Task Accuracy
- Click an agent row to expand and show their individual task results from `/api/results/{generation}`

### Footer
- "WeaveHacks 3 — Best Self-Improving Agent"
- Link to W&B Weave traces

## Design Notes
- Dark theme: bg-slate-950, cards bg-slate-900, borders slate-800
- Accent colors: Emerald for positive metrics, Red for negative, Purple for calibration
- Use the reasoning style colors consistently everywhere
- Smooth animations on chart transitions
- Responsive but optimized for demo/presentation (wide screen)
- No authentication needed
- All data is fetched client-side from the API on page load
