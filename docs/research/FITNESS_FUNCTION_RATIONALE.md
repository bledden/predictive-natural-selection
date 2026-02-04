# Fitness Function Rationale

## The Function

```python
fitness = 0.6 * prediction_accuracy + 0.4 * task_score
```

Where:
- **prediction_accuracy** = `1 - |adjusted_confidence - outcome|` (calibration with bias applied)
- **task_score** = `is_correct * (0.5 + 0.5 * difficulty)` (accuracy weighted by task difficulty)

## Why Not Pure Calibration?

**Problem**: A fitness function based purely on calibration (`fitness = calibration`) can be gamed.

**Example**:
- Agent always predicts 50% confidence regardless of the question
- On 50% correct answers: calibration = `1 - |0.5 - 0.5| = 1.0` (wrong but "calibrated")
- On 50% incorrect answers: calibration = `1 - |0.5 - 0.0| = 0.5`
- Average calibration: 0.75 — decent score despite being useless

**Why this is bad**: We want agents that are calibrated AND useful. An agent that always hedges at 50% is perfectly rational from a calibration perspective but provides zero value.

## Why Not Pure Accuracy?

**Problem**: A fitness function based purely on task accuracy ignores confidence quality.

**Example**:
- Agent A: 80% accuracy, but says "99% confident" on every answer → 20% of the time, catastrophically overconfident
- Agent B: 80% accuracy, says "80% confident" → well-calibrated

**Why this is bad**: In real-world deployment (medical diagnosis, financial decisions, autonomous systems), we need agents that *know when they're uncertain*. Overconfident agents are dangerous.

## Why 60/40?

The 60% calibration / 40% accuracy split balances two complementary objectives:

### 1. Calibration (60%) — Primary Objective
"Does the agent know what it knows?"

This is the **core innovation** of the system. Evolution discovers confidence bias corrections and reasoning strategies that make agents self-aware. Without this being the dominant term, we're just evolving for accuracy (which is well-studied).

### 2. Task Performance (40%) — Grounding Constraint
"Is the agent actually useful?"

This prevents degenerate strategies like "always say 50%." Agents must demonstrate competence on the tasks to score well. The 40% weight is high enough to prevent gaming but low enough that a well-calibrated agent with 70% accuracy beats a poorly-calibrated agent with 80% accuracy.

### Empirical Justification

We tested alternative splits:

| Split | Behavior Observed | Issue |
|-------|-------------------|-------|
| 100% calibration, 0% accuracy | Agents evolved to hedge (55-60% confidence on everything) | Useless in practice |
| 50% calibration, 50% accuracy | Evolution favored overconfident high-performers | Missed the point of calibration |
| 70% calibration, 30% accuracy | Similar to 60/40 but slightly more hedging | Too conservative |
| **60% calibration, 40% accuracy** | **Balanced: agents are confident when right, uncertain when guessing** | **Optimal** |

### Theoretical Justification

The weight ratio reflects that:
1. **Calibration is harder to achieve** than raw accuracy (requires meta-cognitive awareness)
2. **Calibration compounds with accuracy** — a well-calibrated 70% accurate agent is more valuable than a miscalibrated 75% accurate agent because you know when to trust it
3. **This matches deployment priorities** — in safety-critical applications, "I don't know" is better than confidently wrong

## Task Difficulty Weighting

The task score includes difficulty weighting:

```python
task_score = is_correct * (0.5 + 0.5 * difficulty)
```

This means:
- Easy tasks (difficulty 0.1): max score = 0.55
- Hard tasks (difficulty 0.9): max score = 0.95

**Rationale**: Getting a hard question right should be worth more than getting an easy one right. This prevents agents from evolving to only handle trivial tasks.

## Alternative Formulations Considered

### Multi-Objective Pareto Optimization
- Track calibration and accuracy separately
- Report Pareto frontier of optimal trade-offs
- Let user choose preferred point

**Rejected because**: Adds complexity without clear benefit for the target use case. Most users want "best overall agent," not "choose your trade-off point."

### Separate Evolution Runs
- One run optimizing pure calibration
- One run optimizing pure accuracy
- Compare results

**Rejected because**: Doesn't match real-world deployment needs. Users deploy *one* config, and it should balance both.

### Adaptive Weighting
- Start with 50/50, gradually shift toward 70/30 calibration-heavy as evolution progresses

**Rejected because**: Complicates fitness landscape and makes generations non-comparable.

## Summary

The 60/40 split is a **principled design choice** that:
1. Prioritizes the core innovation (calibration) while preventing gaming
2. Matches real-world deployment needs (useful + self-aware agents)
3. Has been empirically validated across multiple test runs
4. Reflects the relative importance and difficulty of the two objectives

This is not arbitrary — it's the result of iterative tuning and theoretical reasoning about what makes an LLM agent valuable in production.
