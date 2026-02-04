# Demo Checklist - WeaveHacks 3

## Pre-Demo Setup (5 minutes before)

### 1. Verify Services Running
- [ ] Frontend: `lsof -ti:3001` → should show process ID
- [ ] Backend: `lsof -ti:8002` → should show process ID
- [ ] If not running:
  ```bash
  # Backend
  cd /Users/bledden/Documents/weavehacks3/predictive-natural-selection
  .venv/bin/uvicorn src.api:app --reload --port 8002 &

  # Frontend
  cd frontend
  npm run dev &
  ```

### 2. Load Dashboard
- [ ] Open browser to http://localhost:3001
- [ ] Verify DiagnosisHero loads (should show Claude Opus 4.5 results)
- [ ] Scroll through all components to ensure no errors
- [ ] Check browser console for errors (should be clean)

### 3. Prepare Browser Tabs
- [ ] Tab 1: Dashboard (http://localhost:3001)
- [ ] Tab 2: GitHub repo (https://github.com/bledden/predictive-natural-selection)
- [ ] Tab 3: Presentation script (PRESENTATION_SCRIPT.md)

### 4. Test Data Loading
- [ ] Verify data files exist:
  - [ ] `data/comprehensive_experiment/analysis_results.json`
  - [ ] `data/previous_gen_experiment/analysis_results.json`
  - [ ] Multiple `evolution_run.json` files in experiment subdirs

### 5. Screen Share Setup
- [ ] Close unnecessary applications
- [ ] Hide desktop clutter
- [ ] Set browser to full screen (Cmd+Shift+F on Mac)
- [ ] Test screen share audio/video

## Demo Flow Checklist

### Opening (30 sec)
- [ ] State the core question: "Do you need a better system or a better model?"
- [ ] Position as a scientific diagnostic tool

### Problem Statement (30 sec)
- [ ] Explain wasted effort on optimization dead-ends
- [ ] Explain premature model upgrades
- [ ] Establish need for quantitative decision-making

### Solution Overview (45 sec)
- [ ] Explain evolutionary optimization
- [ ] Define calibration gap (positive/zero/negative)
- [ ] Show it gives definitive answers

### Live Demo - Screen 1: DiagnosisHero (30 sec)
- [ ] **Action:** Navigate to http://localhost:3001
- [ ] **Point out:** Large gap number (+0.1%)
- [ ] **Point out:** Color-coded verdict (should be amber/green for "already optimized")
- [ ] **Point out:** Before/after bars showing minimal difference
- [ ] **Say:** "Claude Opus 4.5 is already optimized — system tuning won't help"

### Live Demo - Screen 2: Gap Chart (30 sec)
- [ ] **Action:** Scroll to GapChart component
- [ ] **Point out:** Flat purple line (raw calibration, model never changes)
- [ ] **Point out:** Blue line barely above it (evolved calibration)
- [ ] **Point out:** Shaded gap area is tiny
- [ ] **Say:** "No matter how much we optimize the system, we're hitting the ceiling"

### Live Demo - Screen 3: Metric Cards (20 sec)
- [ ] **Action:** Scroll to metric cards section
- [ ] **Point out:** System Gap card (near-zero)
- [ ] **Point out:** Model Baseline (82.6%)
- [ ] **Point out:** Evolved Calibration (82.7%)
- [ ] **Say:** "The numbers confirm it — minimal headroom for optimization"

### Live Demo - Screen 4: Model Comparison (45 sec)
- [ ] **Action:** Open terminal or comparison script output
- [ ] **Run:** `./compare_frontier_vs_previous_gen.py` (or show pre-saved output)
- [ ] **Point out:** GPT-4o gap: -7.2% (negative!)
- [ ] **Point out:** GPT-4o → GPT-5.2 improvement: +10.6%
- [ ] **Say:** "System optimization HURT GPT-4o. But upgrading to GPT-5.2 gave immediate improvement. The tool told us the right path: better model."

### Live Demo - Screen 5: Evolution Visualization (30 sec)
- [ ] **Action:** Scroll to phylogenetic tree
- [ ] **Point out:** 10 generations of trait evolution
- [ ] **Action:** Scroll to trait distribution heatmaps
- [ ] **Point out:** Which traits dominated
- [ ] **Say:** "Full transparency into what the evolution process discovered"

### The Insight (30 sec)
- [ ] State finding: Frontier models are already well-calibrated
- [ ] State finding: Hard tasks on weak models need model upgrades
- [ ] State value: Quantitative answer instead of guessing

### Technical Rigor (30 sec)
- [ ] Mention: Multi-seed validation (3 seeds)
- [ ] Mention: Train/val/test split (60/20/20)
- [ ] Mention: Multiple models tested
- [ ] Mention: 12 experiments, 120 generations total

### Value Proposition (30 sec)
- [ ] Audience 1: Model labs (understand calibration quality)
- [ ] Audience 2: AI teams (stop wasting time on dead-ends)
- [ ] Audience 3: Researchers (quantify tradeoffs)
- [ ] Core message: Know where to invest to improve

### Closing (15 sec)
- [ ] Restate core question: "Do you need a better system — or a better model?"
- [ ] Tagline: "Run evolution once. Get your answer. Stop guessing."
- [ ] Thank audience

## Post-Demo Q&A Prep

### Expected Questions & Responses

**Q: "All results say 'need better model' — isn't that useless?"**
- [ ] A: "That's a valuable finding! Tells you frontier models are already optimized. Tool's job is truth, not what you want to hear. For frontier models on hard tasks, model quality dominates — that's the insight."

**Q: "How do you prevent overfitting?"**
- [ ] A: "60/20/20 train/val/test split with stratification. All reported metrics are held-out test data the evolution never saw."

**Q: "What if I disagree with the genome configs?"**
- [ ] A: "You're not meant to copy the exact configs — use the GAP. It proves what's possible. If gap is zero, different configs won't help."

**Q: "Could this inform fine-tuning?"**
- [ ] A: "Absolutely. Positive gaps show beneficial traits → candidates for fine-tuning data. Negative gaps suggest architectural improvements needed, not fine-tuning."

**Q: "Why natural selection vs gradient descent?"**
- [ ] A: "LLM configs aren't differentiable — can't gradient descend on 'reasoning style'. Natural selection works on discrete traits. Plus gives you phylogenetic tree showing what mattered."

**Q: "How long does it take?"**
- [ ] A: "10 agents × 10 gens × 8 tasks = 800 LLM calls. ~15 min with GPT-5.2, <5 min with fast models. Run ONCE instead of weeks of manual experimentation."

## Emergency Procedures

### If Dashboard Won't Load
1. Check both servers running: `lsof -ti:3001` and `lsof -ti:8002`
2. Restart backend: `cd /path && .venv/bin/uvicorn src.api:app --port 8002 &`
3. Restart frontend: `cd frontend && npm run dev &`
4. Clear browser cache and reload
5. **Fallback:** Show static screenshots from `data/*/confidence_evolution.png`

### If API Returns Errors
1. Check backend logs: `tail -f backend.log` (if logging enabled)
2. Verify data files exist: `ls data/comprehensive_experiment/`
3. **Fallback:** Manually load JSON and show in terminal:
   ```bash
   cat data/comprehensive_experiment/analysis_results.json | jq
   ```

### If Demo Machines Crashes
1. Have backup screenshots ready in a folder
2. Walk through presentation script with static images
3. Show GitHub repo as proof of implementation
4. Offer to demo later in breakout session

## Post-Demo Actions

- [ ] Share GitHub repo link in chat
- [ ] Share DEMO_SUMMARY.md for detailed findings
- [ ] Answer follow-up questions in Discord/Slack
- [ ] Note any bugs or issues for post-hackathon fixes

## Success Metrics

- [ ] Audience understands the core question ("system vs model")
- [ ] Audience grasps the calibration gap concept
- [ ] Judges see the technical rigor (multi-seed, train/test split)
- [ ] Demo runs smoothly with no crashes
- [ ] Q&A handled confidently

## Final Confidence Check

Before starting:
- [ ] Deep breath
- [ ] "I know this system inside and out"
- [ ] "The findings are valuable even if unexpected"
- [ ] "I'm ready to demo"

**Let's go!**
