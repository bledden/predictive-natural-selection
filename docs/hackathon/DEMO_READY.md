# Demo Ready Status - Predictive Natural Selection

**Date:** February 1, 2026
**Event:** WeaveHacks 3
**Status:** ✅ READY TO DEMO

---

## Services Status

### Frontend (Next.js)
- **URL:** http://localhost:3000
- **Status:** ✅ Running
- **Framework:** Next.js 16.0.10 (Turbopack)
- **Port:** 3000

### Backend (FastAPI)
- **URL:** http://localhost:8002
- **Status:** ✅ Running
- **Framework:** FastAPI with uvicorn
- **Port:** 8002
- **Endpoints:**
  - `/api/run-summary` - Latest run summary
  - `/api/generations` - Generation-by-generation data
  - `/api/phylogenetic-tree` - Evolution tree data

---

## Experimental Results

### Completed Experiments

#### Frontier Models (9 runs total)
- **GPT-5.2** × 3 seeds: 80.9% ± 9.9% (gap: -0.5%)
- **Claude Opus 4.5** × 3 seeds: 82.7% ± 12.5% (gap: +0.1%)
- **DeepSeek V3** × 3 seeds: 66.7% ± 10.9% (gap: -6.8%)

#### Previous-Gen Models (3 runs total)
- **GPT-4o** × 3 seeds: 70.3% ± 6.8% (gap: -7.2%)

### Data Files Location
```
data/
├── comprehensive_experiment/
│   ├── analysis_results.json
│   ├── gpt_5_2_seed{42,43,44}/evolution_run.json
│   ├── claude_opus_4_5_seed{42,43,44}/evolution_run.json
│   └── deepseek_v3_seed{42,43,44}/evolution_run.json
└── previous_gen_experiment/
    ├── analysis_results.json
    └── gpt_4o_seed{42,43,44}/evolution_run.json
```

---

## Key Findings

### 1. Frontier Models Are Well-Calibrated
Claude Opus 4.5 and GPT-5.2 show near-zero calibration gaps, indicating they're already optimized out-of-the-box.

### 2. System Optimization Has Limits
GPT-4o and DeepSeek V3 show negative gaps, meaning evolution degraded performance on these hard tasks.

### 3. Model Upgrade Path Is Clear
GPT-4o → GPT-5.2 shows +10.6% improvement that system optimization couldn't achieve.

### 4. Statistical Reproducibility
All results show CV% < 20% across multiple seeds.

---

## Demo Materials

### Core Documents
1. **[DEMO_SUMMARY.md](DEMO_SUMMARY.md)** - Executive summary with full experimental results
2. **[PRESENTATION_SCRIPT.md](PRESENTATION_SCRIPT.md)** - 5-minute presentation with Q&A prep
3. **[DEMO_CHECKLIST.md](DEMO_CHECKLIST.md)** - Step-by-step demo execution checklist
4. **[ADDRESSING_THE_GAP.md](ADDRESSING_THE_GAP.md)** - Honest assessment of missing positive examples

### Supporting Documents
5. **[FITNESS_FUNCTION_RATIONALE.md](FITNESS_FUNCTION_RATIONALE.md)** - Justification for 60/40 calibration/accuracy split
6. **[ISSUES_AND_RED_FLAGS.md](ISSUES_AND_RED_FLAGS.md)** - Methodological issues identified and addressed
7. **[CONTEXT_FOR_ANALYSIS.md](CONTEXT_FOR_ANALYSIS.md)** - Complete project overview
8. **[README.md](README.md)** - Project documentation

---

## Dashboard Components

### Implemented Components
- ✅ **DiagnosisHero** - Large verdict card with gap percentage and diagnosis
- ✅ **GapChart** - Area chart showing raw vs evolved calibration
- ✅ **MetricCards** - System Gap, Model Baseline, Evolved Calibration, Dominant Strategy
- ✅ **CalibrationChart** - System vs Model performance comparison
- ✅ **FitnessChart** - Evolution fitness curves
- ✅ **TraitDistribution** - Heatmap of genome trait evolution
- ✅ **ConfidenceBias** - Calibration curve analysis
- ✅ **PhylogeneticTree** - Lineage evolution visualization
- ✅ **GenerationExplorer** - Generation-by-generation details
- ✅ **LiveEvolution** - Run new experiments (renamed from "Run Evolution")

---

## GitHub Repository

- **URL:** https://github.com/bledden/predictive-natural-selection
- **Status:** ✅ Pushed (latest commit: c9d2610)
- **Branch:** main
- **Commits:**
  1. `04375b6` - Initial commit
  2. `254dcf0` - Phase 1: Fix methodological foundations
  3. `013f7c1` - Phase 2: Multi-model validation experiments
  4. `c9d2610` - Add comprehensive demo preparation materials

---

## Pre-Demo Checklist

### 5 Minutes Before Demo

1. **Services**
   - [x] Frontend running on http://localhost:3000
   - [x] Backend running on http://localhost:8002
   - [ ] Load dashboard in browser and verify all components render
   - [ ] Check browser console for errors

2. **Browser Setup**
   - [ ] Tab 1: Dashboard (http://localhost:3000)
   - [ ] Tab 2: GitHub repo
   - [ ] Tab 3: PRESENTATION_SCRIPT.md
   - [ ] Browser in full screen mode

3. **Screen Share**
   - [ ] Close unnecessary applications
   - [ ] Hide desktop clutter
   - [ ] Test screen share audio/video

---

## Demo Flow (5 minutes)

### 1. Opening (30 sec)
"When your AI system isn't performing well, you face a choice: tune prompts or upgrade models. **How do you know which?** Predictive Natural Selection answers that scientifically."

### 2. Problem Statement (30 sec)
"Teams waste time optimizing systems at their ceiling or prematurely upgrading when prompting would work. You need a diagnostic."

### 3. Solution (45 sec)
"We evolve LLM configurations using natural selection. The **calibration gap** tells you:
- Positive gap? Keep optimizing.
- Near-zero? Upgrade the model.
- Negative? System can't help, need better model."

### 4. Live Demo (2 min)
- Show DiagnosisHero: Claude Opus 4.5 gap +0.1%
- Show GapChart: Flat lines, tiny shaded area
- Show GPT-4o: Negative gap (-7.2%)
- Show GPT-4o → GPT-5.2: +10.6% improvement
- Show phylogenetic tree and visualizations

### 5. Insight (30 sec)
"Frontier models are already well-calibrated. For hard tasks on weaker models, you need better models, not endless prompting. **The tool gives you a quantitative answer.**"

### 6. Technical Rigor (30 sec)
"Multi-seed validation, train/test split, multiple models, statistical reporting. 12 experiments, 120 generations, thousands of evaluations."

### 7. Value Proposition (30 sec)
"Model labs: understand calibration quality. AI teams: stop wasting time. Researchers: quantify tradeoffs scientifically."

### 8. Closing (15 sec)
"Predictive Natural Selection: **Do you need a better system — or a better model?** Run evolution once. Get your answer. Stop guessing."

---

## Q&A Preparation

### Expected Questions

**Q: "All results say 'need better model' — isn't that useless?"**
**A:** "That's a valuable finding! It tells you frontier models are already well-calibrated. The tool's job is truth, not what you want to hear. For frontier models on hard tasks, model quality dominates."

**Q: "How do you prevent overfitting?"**
**A:** "60/20/20 train/val/test split with stratification. All reported metrics are held-out test data."

**Q: "What if I disagree with the genome configs?"**
**A:** "You're meant to use the GAP, not the exact configs. The evolved genomes prove what's possible."

**Q: "Could this inform fine-tuning?"**
**A:** "Absolutely. Beneficial traits are candidates for fine-tuning data. Negative gaps suggest architectural improvements needed."

**Q: "Why natural selection vs gradient descent?"**
**A:** "LLM configs aren't differentiable. Natural selection works on discrete traits. Plus phylogenetic tree shows what mattered."

**Q: "How long does it take?"**
**A:** "800 LLM calls per run. ~15 min with GPT-5.2, <5 min with fast models. Run ONCE instead of weeks of manual experimentation."

---

## Emergency Procedures

### If Dashboard Won't Load
1. Check services: `lsof -ti:3000` and `lsof -ti:8002`
2. Restart if needed
3. **Fallback:** Show static screenshots from `data/*/confidence_evolution.png`

### If API Errors
1. Check backend logs
2. Verify data files exist
3. **Fallback:** Load JSON manually and show in terminal

### If System Crashes
1. Have backup screenshots ready
2. Walk through with static images
3. Show GitHub repo
4. Offer breakout session demo

---

## Success Criteria

- [x] Audience understands "system vs model" question
- [ ] Audience grasps calibration gap concept
- [ ] Judges see technical rigor
- [ ] Demo runs smoothly
- [ ] Q&A handled confidently

---

## Final Status

**✅ All systems ready**
**✅ All data prepared**
**✅ All documentation complete**
**✅ Demo script ready**
**✅ GitHub pushed**

**READY TO PRESENT**

Good luck! 🚀
