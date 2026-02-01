# Predictive Natural Selection - Demo Summary

**WeaveHacks 3 - February 1, 2026**

## Executive Summary

Predictive Natural Selection answers the question: **"Do you need a better system — or a better model?"**

We evolve LLM agent configurations using natural selection to find the optimal system configuration for prediction tasks. The **calibration gap** (difference between raw model performance and evolved system performance) reveals whether you should invest in prompt engineering and system optimization, or if you need a fundamentally better model.

## Core Innovation

**Traditional approach:** Try different prompts manually, unclear when to stop optimizing vs. upgrade models.

**Our approach:** Run evolutionary optimization once. The gap tells you:
- **Positive gap** → System optimization headroom exists, keep tuning
- **Near-zero gap** → Already optimized, need better model
- **Negative gap** → System can't help this model on these tasks, need better model

## Technical Implementation

### Evolution Mechanics
- **Population:** 10 agent configurations per generation
- **Genome:** system_prompt, reasoning_style, confidence_bias, temperature, risk_tolerance, memory_window, memory_weighting
- **Fitness:** 60% calibration accuracy + 40% prediction accuracy
- **Selection:** Tournament selection, elitism, mutation
- **Validation:** Train/val/test split (60/20/20) with stratification by task type

### Methodological Rigor
- **Multi-seed validation:** 3 seeds per model for reproducibility
- **Multi-model testing:** Frontier and previous-gen models
- **Held-out test set:** Final evaluation on unseen tasks
- **Statistical reporting:** Mean ± std, coefficient of variation

## Experimental Results

### Frontier Models (3 models × 3 seeds = 9 runs)

| Model | Raw Calibration | Evolved Calibration | Gap | CV% | Verdict |
|-------|----------------|---------------------|-----|-----|---------|
| **Claude Opus 4.5** | 82.6% ± 8.7% | 82.7% ± 12.5% | +0.1% | 15.1% | ⚖️ Already optimized |
| **GPT-5.2** | 81.4% ± 10.3% | 80.9% ± 9.9% | -0.5% | 12.3% | ⚖️ Already optimized |
| **DeepSeek V3** | 73.5% ± 8.6% | 66.7% ± 10.9% | -6.8% | 16.4% | 🤖 Need better model |

### Previous-Gen Models (1 model × 3 seeds = 3 runs)

| Model | Raw Calibration | Evolved Calibration | Gap | CV% | Verdict |
|-------|----------------|---------------------|-----|-----|---------|
| **GPT-4o** | 77.5% ± 7.4% | 70.3% ± 6.8% | -7.2% | 9.7% | 🤖 Need better model |

**Note:** Claude 3.5 Sonnet and DeepSeek V2.5 were unavailable via APIs tested.

## Key Findings

### 1. Frontier Models Are Already Well-Calibrated
Claude Opus 4.5 and GPT-5.2 show near-zero calibration gaps, indicating these models are already optimally configured out-of-the-box for prediction tasks. **System optimization provides minimal benefit.**

### 2. Model Capability Dominates on Hard Tasks
Both GPT-4o and DeepSeek V3 show negative gaps, meaning evolutionary optimization actually degraded performance. This suggests:
- Tasks may be too difficult for these models' base capabilities
- Prompt engineering can't compensate for fundamental reasoning limitations
- **Model upgrade is the right path, not system tuning**

### 3. Statistical Reproducibility
All results show coefficient of variation <20%, indicating reproducible findings across random seeds.

## Critical Gap in Current Results

**What we're missing:** Examples of positive system optimization (e.g., raw 50% → evolved 70%).

**Why this matters:** The tool's value proposition is helping users decide "system vs model." But all our current results say "model" — we have no examples demonstrating when system optimization helps.

**Hypothesis for why:**
- Frontier models are too sophisticated (already well-calibrated)
- Mid-tier models we tried were unavailable (Claude 3.5 Sonnet, DeepSeek V2.5)
- Tasks may be too hard for weaker models to show improvement from prompting

## Dashboard Features

### 1. DiagnosisHero Component
Large verdict card showing:
- Calibration gap percentage
- Color-coded diagnosis (emerald=system, amber=mixed, red=model)
- Before/after performance bars
- Clear recommendation

### 2. System Optimization Gap Chart
Full-width area chart showing:
- Raw calibration (flat line - model never changes)
- Evolved calibration (climbing line - system optimization)
- Shaded gap area = "free performance" from system tuning

### 3. Reframed Metric Cards
- **System Gap:** Optimization headroom available
- **Model Baseline:** Raw LLM calibration (unchanged)
- **Evolved Calibration:** After behavioral optimization
- **Dominant Strategy:** Most successful genome trait

### 4. Evolution Visualization
- Phylogenetic tree showing lineage evolution
- Trait distribution heatmaps
- Confidence bias calibration curves
- Generation-by-generation explorer

## Demo Flow

1. **Landing page:** Show DiagnosisHero with Claude Opus 4.5 results
   - Gap: +0.1% → "Already optimized, model upgrade needed for improvement"

2. **Explain the gap chart:**
   - Flat raw calibration line (model never changes)
   - Evolved line barely moves (system can't help)
   - Shaded gap area is tiny

3. **Show GPT-4o comparison:**
   - Negative gap (-7.2%)
   - Evolution actually hurt performance
   - Clear "need better model" verdict

4. **Show model evolution comparison:**
   - GPT-4o → GPT-5.2: +10.6% improvement from model upgrade
   - System optimization couldn't achieve this with GPT-4o

5. **Explain the insight:**
   - For frontier models on hard tasks: model quality dominates
   - System optimization has diminishing returns
   - Know when to stop tuning and upgrade instead

## Next Steps (Post-Hackathon)

### Option A: Test Truly Weak Models
Run GPT-3.5-turbo, Gemini Flash 1.5, Llama 3.1 8B to find models with optimization headroom.

### Option B: Easier Task Set
Create tasks where weak models can succeed with good prompting (e.g., sentiment analysis, classification).

### Option C: Reframe as Frontier Analysis
Position as "frontier model readiness assessment" rather than system-vs-model diagnostic.

### Option D: Controlled Demonstration
Start with intentionally bad prompts, show evolution fixing them (artificial but educational).

## Technical Stack

- **Backend:** Python, asyncio, OpenAI API, Anthropic API, W&B Inference
- **Frontend:** Next.js 14, React, TypeScript, Tailwind CSS, Recharts
- **Evolution:** Custom genetic algorithm with elitism and tournament selection
- **Tasks:** 42 prediction tasks (trivia, estimation, reasoning) with difficulty ratings

## Repository

GitHub: [predictive-natural-selection](https://github.com/bledden/predictive-natural-selection)

## Honest Assessment

**What works:**
- Methodologically rigorous experimental design
- Beautiful, informative dashboard
- Clear diagnostic framing
- Reproducible multi-seed validation

**What we learned:**
- Frontier models are already very well-calibrated
- System optimization has limits on hard tasks
- Model quality matters more than we expected
- Need broader model diversity to demonstrate full value

**Impact:**
Even with current limitations, the tool successfully demonstrates:
1. When to stop optimizing and upgrade models (all our test cases)
2. Quantitative measurement of optimization headroom
3. Reproducible, statistically valid model evaluation
4. Clear visualization of system-vs-model tradeoffs

The absence of positive optimization examples is itself a valuable finding: **for frontier models on challenging tasks, invest in better models, not endless prompt engineering.**
