# Better Prompts or a Better Model? Evolutionary Experiments Across Six LLMs

*Blake Ledden | February 2026*

---

When your AI system underperforms, should you optimize the system — prompts, reasoning strategies, temperature, confidence calibration — or just upgrade to a better model?

I built [Predictive Natural Selection](https://github.com/bledden/predictive-natural-selection) to answer this empirically. It evolves populations of LLM agent configurations through natural selection, then measures whether evolved configurations outperform the raw model on held-out test tasks. The gap between evolved and raw performance tells you where to invest.

I ran 60 experiments across six models spanning 3.8B to 671B parameters, 10 seeds each, to find the threshold where system optimization stops being worth it.

## The Setup

Each experiment evolves a population of 10 agent "genomes" over 15 generations. A genome encodes:

- **System prompt** (mutated via LLM-powered rewriting)
- **Reasoning strategy** (chain-of-thought, step-by-step, analogical, debate-self, first-principles, elimination)
- **Confidence bias** (systematic calibration adjustment, bounded to +/-0.15)
- **Temperature** and **risk tolerance**

Fitness is scored with **Brier score** — a proper scoring rule where the optimal strategy is honest confidence reporting. This prevents evolution from gaming calibration through systematic bias, which was a problem I had to diagnose and fix during development (more on that below).

Tasks rotate each generation (seeded deterministically) so evolution can't memorize specific questions. A stratified 60/20/20 train/validation/test split ensures final metrics come from tasks evolution never saw.

All six models used the same 42 built-in tasks, same evolution parameters, same methodology. The only variable is the model.

## The Models

| Model | Parameters | Category | Provider |
|-------|-----------|----------|----------|
| Microsoft Phi-4 Mini | 3.8B | Small | W&B Inference |
| Meta Llama 3.1 8B | 8B | Small | W&B Inference |
| Qwen 2.5 14B | 14B | Small-Medium | W&B Inference |
| OpenAI GPT-OSS 20B | 20B MoE | Medium | W&B Inference |
| Meta Llama 3.3 70B | 70B | Large | W&B Inference |
| DeepSeek V3.1 | 671B MoE | Frontier | W&B Inference |

## Results

The metric that matters is the **test gap**: evolved calibration minus raw calibration on held-out tasks. Positive means evolution helped. Negative means the raw model was already better.

| Model | Params | Mean Gap | Median | Std | t-stat | p(gap>0) | Cohen's d |
|-------|--------|----------|--------|-----|--------|----------|-----------|
| Phi-4 Mini | 3.8B | **+4.5%** | +4.2% | 2.4% | 5.85** | 10/10 | 1.85 |
| Llama 3.1 | 8B | **+2.4%** | +2.2% | 2.8% | 2.66* | 7/10 | 0.84 |
| Qwen 2.5 | 14B | +0.7% | +0.6% | 1.8% | 1.29 | 8/10 | 0.41 |
| GPT-OSS | 20B MoE | -0.1% | +0.1% | 4.3% | -0.05 | 6/10 | -0.01 |
| Llama 3.3 | 70B | +1.9% | +1.1% | 3.2% | 1.86 | 9/10 | 0.59 |
| DeepSeek V3.1 | 671B MoE | **-0.1%** | +0.1% | 0.6% | -0.36 | 6/10 | -0.11 |

\* p < 0.05, \*\* p < 0.001 (two-tailed t-test, df=9)

## What This Actually Shows

**Two statistically significant results:**

**Phi-4 Mini (3.8B) genuinely benefits from system optimization.** Every single seed (10/10) produced a positive test gap. Mean improvement of +4.5% with a Cohen's d of 1.85 — a large effect. Evolution found configurations that made this small model measurably more calibrated than its raw output on tasks it had never seen during training.

**DeepSeek V3.1 (671B) does not benefit.** Mean gap of -0.1% with the tightest variance of any model (+/-0.6%). Evolution can't improve what's already near-optimal. The signal is effectively zero.

**Llama 3.1 8B sits at the boundary.** Statistically significant (t=2.66, p<0.05) but with higher variance — three seeds went negative. The effect is real but less reliable than Phi-4.

**Everything from 14B up is inconclusive.** Qwen 2.5 (14B), GPT-OSS (20B), and Llama 3.3 (70B) all have test gaps that don't reach significance. The means are small and the standard deviations are large relative to the effect.

## The Honest Interpretation

It would be satisfying to draw a clean curve — "below X billion parameters, optimize your system; above X, upgrade your model." The data doesn't support that clean of a story.

What it does support:

1. **Very small models (< 8B) have real optimization headroom.** Phi-4 at 3.8B is the clearest case. If you're deploying a small model due to cost or latency constraints, investing in prompt engineering and system configuration will produce measurable gains.

2. **Frontier models are already near-optimal for calibration.** DeepSeek V3.1 at 671B shows this clearly — the variance is so tight that we can confidently say evolution adds nothing. Don't waste time optimizing prompts for calibration on frontier models.

3. **The middle is noisy.** Between 14B and 70B, the effect is inconsistent across seeds. This doesn't mean optimization never helps at these scales — it means 10 seeds and 42 tasks aren't enough to reliably detect what may be a small effect. The signal-to-noise ratio degrades as the true effect shrinks.

4. **The Llama 3.3 70B results are interesting but not conclusive.** 9/10 seeds positive, mean of +1.9%, but the standard deviation (3.2%) keeps it from significance. This model might genuinely benefit from system optimization, or it might have more variable calibration that creates noisy gaps. More seeds would clarify.

## What the Evolved Agents Actually Learned

For models where evolution helped, what traits did natural selection converge on?

**Phi-4 Mini** showed no single dominant strategy — winning configurations split across debate-self, chain-of-thought, first-principles, analogical, and elimination. This suggests the model benefits from *any* structured reasoning, and the specific strategy matters less than having one at all.

**Llama 3.1 8B** converged more strongly on chain-of-thought and elimination strategies across seeds, with debate-self and step-by-step as secondary winners.

**DeepSeek V3.1**, where evolution didn't help, showed no convergence — strategies were scattered across first-principles, analogical, step-by-step, chain-of-thought, and elimination. When the model is already well-calibrated, no reasoning strategy provides a consistent edge.

## The Overfitting Problem (And Why Methodology Matters)

Before these results were possible, I had to fix a fundamental problem. Early experiments used a linear calibration metric (`1 - |predicted - outcome|`) and the same 8 tasks every generation. The results looked promising during training but fell apart on test:

| Model | Training Gap | Test Gap |
|-------|-------------|----------|
| DeepSeek V3 | +6.2% | -17.8% |
| GPT-4o | +0.2% | -24.0% |

Evolution was gaming `confidence_bias` — learning to systematically shift confidence in a direction that improved the linear metric on the specific training tasks, then failing catastrophically on new tasks.

Four fixes:

1. **Brier score** (`1 - (predicted - outcome)^2`) — a proper scoring rule where the mathematically optimal strategy is honest confidence reporting. You can't game it with systematic bias.
2. **Task rotation** — different training tasks each generation, seeded deterministically. Evolution can't memorize specific questions.
3. **Tighter confidence_bias bounds** — reduced from +/-0.3 to +/-0.15, and mutation step from +/-0.1 to +/-0.05.
4. **Larger task batches** — 15 tasks per generation instead of 8.

After fixes, test gap dropped from -17.8% to -0.7%. The methodology now measures real generalization.

This is worth emphasizing: **if you're evaluating prompt optimization or agent tuning with fixed evaluation sets and improper scoring rules, your improvements may be illusory.** The system will find and exploit the gap between your metric and the thing you actually care about.

## Limitations

**42 tasks is small.** The test split is only ~9 tasks per type. This creates high variance in test metrics, which is why the middle models are inconclusive. A larger, more diverse task bank would sharpen the picture.

**One task domain.** All tasks are trivia, estimation, and reasoning. Models may show different optimization headroom on other domains — code generation, summarization, multi-turn dialogue. The framework supports custom task files (`--tasks-file`) for this reason.

**Parameter count isn't the only variable.** These models differ in architecture (dense vs MoE), training data, instruction tuning quality, and base capabilities. The trend correlates with size but we can't isolate size as the cause. A controlled comparison would need multiple checkpoints of the same model at different scales.

**15 generations may be insufficient.** Evolution might need more generations to find optimal configurations for larger models where the search space is less constrained. Though the tight DeepSeek variance suggests more generations wouldn't change that particular result.

**Calibration isn't everything.** A model could benefit from system optimization on accuracy while showing no improvement on calibration. This study specifically measures calibration headroom.

## Practical Takeaways

**If you're running a small model (< 8B params):** Invest in system optimization. Structured reasoning prompts, calibrated confidence estimates, and evolved configurations produce real gains. The ROI is positive.

**If you're running a frontier model:** Don't bother optimizing for calibration. The model is already near-optimal. Spend that effort on better task decomposition, tool use, or retrieval instead — areas where system design still matters regardless of model capability.

**If you're running a mid-size model (14B-70B):** Test empirically before committing. The effect may exist but it's inconsistent. Run your own evaluation with your specific tasks before deciding whether to optimize or upgrade.

**If you're building eval pipelines:** Use proper scoring rules. Use rotating task sets. Always hold out a test set that your optimization process never sees. If your training metrics improve but your test metrics don't, you have an overfitting problem, not a system optimization success.

## Reproducing This

All code, data, and experiment scripts are open source:

```bash
git clone https://github.com/bledden/predictive-natural-selection.git
cd predictive-natural-selection
pip install -e .

# Run the full comparison (requires W&B API key or any OpenAI-compatible API)
python scripts/run_model_comparison.py

# Or test a single model
python scripts/run_model_comparison.py --model phi4_mini --seeds 42

# Run with your own tasks
evolve run --model meta-llama/Llama-3.1-8B-Instruct --tasks-file my_tasks.json
```

60 experiments, 10 seeds per model. Raw data in `data/model_comparison/`. Every claim in this post can be verified from the JSON output files.

---

*Built at [WeaveHacks 3](https://weavehacks.com). Models served via [W&B Inference](https://wandb.ai/site/inference).*
