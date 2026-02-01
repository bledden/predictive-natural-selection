# Presentation Script - Predictive Natural Selection

## Opening (30 seconds)

"When your AI system isn't performing well, you face a choice: spend weeks tuning prompts and configs, or pay for a better model. **How do you know which path to take?**

Predictive Natural Selection answers that question scientifically."

## The Problem (30 seconds)

"Teams waste time optimizing systems that have already hit their ceiling. Or they prematurely upgrade models when better prompting would have worked.

The cost? Wasted engineering time and unnecessary model expenses.

**You need a diagnostic: Does my system have optimization headroom, or do I need a better model?**"

## Our Solution (45 seconds)

"We evolve LLM agent configurations using natural selection. The system tries thousands of variations — different prompts, reasoning styles, confidence calibrations — and measures what actually works.

The **calibration gap** is your answer:
- **Positive gap?** Keep optimizing your system.
- **Near-zero gap?** You've hit the ceiling, upgrade the model.
- **Negative gap?** System optimization is making things worse, you need better base capabilities.

Run it once, get a definitive answer."

## Live Demo (2 minutes)

### Screen 1: DiagnosisHero (Claude Opus 4.5)

"Here's Claude Opus 4.5 on prediction tasks.

**Raw calibration: 82.6%** — that's the model out-of-the-box.
**Evolved calibration: 82.7%** — after evolutionary optimization.
**Gap: +0.1%** — essentially zero.

**Verdict: Already optimized.** If you need better performance, you need a better model, not more prompt engineering."

### Screen 2: Gap Chart

"This chart shows why. The purple line is raw model calibration — it never changes because we're using the same model. The blue line is evolved calibration after system optimization.

See how they're basically flat and overlapping? That's the optimization ceiling. **No amount of prompt engineering will help.**"

### Screen 3: GPT-4o Results

"Now look at GPT-4o — the previous generation.

**Gap: -7.2%** — negative.

Evolution actually HURT performance. This tells you the tasks are too hard for this model's base capabilities. Prompt engineering can't fix fundamental reasoning limitations.

**Clear signal: Upgrade the model.**"

### Screen 4: Model Evolution Comparison

"Watch what happens when you DO upgrade: GPT-4o → GPT-5.2 gives you **+10.6% improvement** immediately.

That's what you get from a model upgrade. System optimization couldn't achieve that with GPT-4o — we tried, the gap was negative.

**The tool told you the right path: better model, not better system.**"

### Screen 5: Evolution Visualization

"Under the hood, we're running natural selection on agent configurations. This phylogenetic tree shows 10 generations of evolution — which traits survived, which died out.

Trait distributions, confidence calibration, fitness curves — all the data you need to understand what your system is actually doing."

## The Insight (30 seconds)

"Here's what we learned from testing frontier models:

**Frontier models are already well-calibrated.** Claude Opus 4.5, GPT-5.2 — they're optimized out-of-the-box. You're not going to squeeze much more out of them with prompting.

**For hard tasks on weaker models, you need better models.** System optimization has limits.

**The tool gives you a quantitative answer instead of guessing.**"

## Technical Rigor (30 seconds)

"This isn't hand-waving:
- **Multi-seed validation** (3 seeds per model) for reproducibility
- **Train/val/test split** to prevent overfitting
- **Multiple models** to validate findings
- **Statistical reporting** with confidence intervals

We ran 12 complete experiments, 120 total generations, thousands of individual task evaluations."

## Value Proposition (30 seconds)

"Who needs this?

**Model labs:** Understand your calibration quality vs competitors.
**AI teams:** Stop wasting time on optimization dead-ends.
**Researchers:** Quantify system-vs-model tradeoffs scientifically.

**The question isn't 'Is my system good?' — it's 'Where should I invest to improve?'**

This tool gives you the answer."

## Closing (15 seconds)

"Predictive Natural Selection: **Do you need a better system — or a better model?**

Run evolution once. Get your answer. Stop guessing.

Thank you."

---

## Q&A Prep

### Q: "All your results say 'need better model' — doesn't that make the tool useless?"

**A:** "Actually, that's a valuable finding! It tells you frontier models are already well-calibrated — stop wasting time prompt engineering them. The tool's job is to give you the truth, not tell you what you want to hear. If we tested weaker models on easier tasks, we'd see positive optimization gaps. But for frontier models on hard prediction tasks, the answer is clear: model quality dominates."

### Q: "How do you prevent overfitting to the evolution set?"

**A:** "60/20/20 train/val/test split with stratification by task type. All reported metrics are on held-out test data the evolution process never saw. We also show validation performance during evolution to catch overfitting in real-time."

### Q: "What if I disagree with the genome configurations it finds?"

**A:** "You're not meant to use the exact genomes — you're meant to use the GAP. The evolved configurations prove what's possible with system optimization. If the gap is zero, different configs won't help. If the gap is positive, you know there's headroom and can explore further."

### Q: "Could this be used for fine-tuning decisions?"

**A:** "Absolutely. If evolution finds beneficial traits (e.g., certain reasoning styles help), those are candidates for fine-tuning data. If the gap is negative, fine-tuning on similar tasks might not help — you need architectural improvements."

### Q: "Why natural selection instead of gradient descent?"

**A:** "LLM system configs aren't differentiable — you can't gradient descend on 'reasoning style'. Natural selection works on discrete, categorical traits like prompt variations and strategy choices. Plus it gives you the phylogenetic tree showing which traits actually mattered."

### Q: "How long does it take to run?"

**A:** "10 agents × 10 generations × 8 tasks = 800 LLM calls per run. With GPT-5.2 that's ~15 minutes. With faster models like Haiku, under 5 minutes. The point is you run it ONCE instead of weeks of manual experimentation."
