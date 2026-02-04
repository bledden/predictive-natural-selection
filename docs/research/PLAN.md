# Project #26: Predictive Natural Selection
## WeaveHacks 3 — Research Exploration / Start Here

**Status:** RESEARCH EXPLORATION. Start scoping here — fascinating concept, uncertain buildability.
**Score:** 38/50 (Impressiveness: 9, Uniqueness: 9, Completion: 5, Demo: 8, Sponsors: 7)

---

## One-Liner

A population of LLM agents with different strategies compete for survival based on their ability to predict outcomes accurately. Successful predictors reproduce (with mutations). Failed predictors die. The population evolves better predictive strategies through natural selection.

## Why This Is Exciting

1. **Zero prior art for LLM agent evolution.** Evolutionary simulations exist for neural networks (NEAT, genetic algorithms for games/robotics). But nobody has applied natural selection to **LLM agent configurations** — the combination of prompts, tools, memory strategies, and reasoning patterns as a "genome."
2. **Prediction as fitness function is objective.** Unlike "did the agent solve the task well?" (subjective), "did the agent correctly predict the outcome?" is binary and measurable. This makes the evolutionary pressure clean and the demo undeniable.
3. **The visualization is jaw-dropping.** A phylogenetic tree of agent strategies, with branches showing which traits survived and which went extinct, is the kind of visual that wins hackathons.
4. **Philosophically rich.** You're evolving *intelligence strategies* — which reasoning approaches survive when there's selection pressure? This is the kind of thing that makes judges think.

## What "Predictive Fitness" Means (Clarified)

In vanilla natural selection: fitness = task performance (subjective).

In predictive natural selection, there are two options:

### Option A: Predict-Then-Act (Recommended)
1. Agent sees a task description
2. Agent **predicts** its outcome BEFORE attempting: "I predict I will succeed/fail, with confidence X%, using strategy Y"
3. Agent attempts the task
4. **Fitness = f(prediction_accuracy, task_performance)**
   - An agent that predicts "I'll fail" and does fail scores higher than one that predicts "I'll succeed" and fails
   - An agent that succeeds AND predicted success scores highest
   - This selects for agents with **calibrated self-awareness** — they know what they can and can't do

### Option B: Predict Outcomes of External Events
1. Agent sees data about a system/domain
2. Agent **predicts** what will happen next (price movement, failure, trend)
3. Ground truth arrives
4. **Fitness = prediction accuracy**
   - This is closer to the Compute Oracle concept but with evolutionary dynamics
   - Agents evolve better prediction strategies through selection pressure

**Option A is more novel** — it produces agents that are both capable AND self-aware. Option B is more measurable but overlaps with #31.

---

## Agent Genome: What Evolves?

An agent's "DNA" is a structured configuration:

```python
@dataclass
class AgentGenome:
    # System prompt / reasoning approach
    system_prompt: str
    reasoning_style: str  # "chain-of-thought", "step-by-step", "analogical", "debate-self"

    # Tool preferences
    preferred_tools: list[str]  # which tools to try first
    tool_timeout: float  # how long to wait for tool results

    # Memory strategy
    memory_window: int  # how many past results to remember
    memory_weighting: str  # "recency", "relevance", "success-rate"

    # Prediction calibration
    confidence_bias: float  # tendency to over/under-predict confidence
    risk_tolerance: float  # willingness to attempt hard tasks

    # Meta
    generation: int
    parent_ids: list[str]
    fitness_history: list[float]
```

### Reproduction
- **Selection:** Top 30% by fitness survive to reproduce
- **Crossover:** Two parents combine genomes (e.g., parent A's reasoning style + parent B's memory strategy)
- **Mutation:** Small random changes (swap reasoning style, adjust confidence_bias, add/remove a tool)
- **Elitism:** Top 2 agents survive unchanged into next generation

### Population Dynamics
- **Population size:** 10-20 agents (small enough to evaluate quickly)
- **Generations:** Target 10-20 generations during demo
- **Tasks per generation:** 5-10 diverse tasks
- **Selection pressure:** Bottom 50% die each generation

---

## Architecture

```
+------------------+
|  Task Generator  |  (produces diverse prediction tasks)
+--------+---------+
         |
+--------v---------+
|  Population       |
|  Manager          |
|  (Redis)          |
|  - 10-20 agents   |
|  - genome store   |
|  - fitness scores |
+--------+---------+
         |
    +----v----+
    | For each agent in population:
    |  1. Present task
    |  2. Agent predicts outcome + confidence
    |  3. Agent attempts task
    |  4. Score: prediction accuracy + task performance
    |  5. Log to Weave
    +----+----+
         |
+--------v---------+
|  Fitness Evaluator|
|  - aggregate scores across tasks
|  - rank population
+--------+---------+
         |
+--------v---------+
|  Evolution Engine |
|  - select top 30%
|  - crossover
|  - mutation
|  - produce next generation
+--------+---------+
         |
+--------v---------+
|  Visualization    |
|  (Marimo/Vercel)  |
|  - phylogenetic tree
|  - fitness over generations
|  - trait distribution
|  - dominant strategies
+------------------+
```

---

## Task Domain (What Are Agents Predicting?)

Need tasks that are:
- Fast to evaluate (< 30 seconds each)
- Have clear right/wrong answers
- Diverse enough that different strategies work for different tasks

**Options:**
1. **Trivia/factual questions** — agent predicts if it can answer correctly, then answers
2. **Code correctness** — agent predicts if a code snippet has a bug, then identifies it
3. **Estimation tasks** — agent predicts a numerical answer within 10%, evaluates against ground truth
4. **Classification tasks** — agent predicts category of input (sentiment, topic, intent)
5. **Reasoning puzzles** — agent predicts if it can solve a logic puzzle, then attempts it

**Recommended:** Mix of 2-3 task types. This forces the population to evolve generalist strategies or specialize in niches.

---

## Tech Stack

| Component | Technology |
|-----------|-----------|
| Backend | Python + FastAPI |
| Population Store | Redis (genome storage, fitness scores, lineage tracking) |
| LLM | W&B Weave inference or OpenAI (each agent runs via the same API with different configs) |
| Evolution | Custom Python (selection, crossover, mutation) |
| Visualization | Marimo notebook (phylogenetic tree, fitness curves, trait distribution) |
| Observability | W&B Weave (trace every agent's prediction + attempt + fitness) |
| Optional | Vercel dashboard as alternative to Marimo |

---

## Build Sequence (16 hours)

### Phase 1: Population Core (Hours 0-5)
1. Define AgentGenome schema
2. Redis population store (CRUD for genomes + fitness)
3. Task generator (start with trivia/factual questions from a corpus)
4. Agent execution: present task → get prediction → get attempt → score
5. **Checkpoint:** Can run one generation with 10 agents

### Phase 2: Evolution Engine (Hours 5-9)
6. Fitness aggregation across tasks
7. Selection (tournament or top-K)
8. Crossover (combine two parent genomes)
9. Mutation (random perturbation of genome fields)
10. Generation loop: evaluate → select → reproduce → next generation
11. **Checkpoint:** Can run 5+ generations, see fitness improving

### Phase 3: Visualization + Demo (Hours 9-14)
12. Phylogenetic tree visualization (Marimo or D3.js on Vercel)
13. Fitness over generations chart
14. Trait distribution over time (which reasoning styles survive?)
15. "Dominant strategy" summary (what did evolution converge on?)
16. Weave integration: trace every agent's prediction lifecycle
17. **Checkpoint:** Demo-ready with compelling visuals

### Phase 4: Polish (Hours 14-16)
18. Run 15-20 generations to generate a compelling evolutionary story
19. Record demo video
20. Clean repo + README

---

## The Completion Confidence Problem (5/10)

This is the main risk. Here's why and how to mitigate:

**Why it's risky:**
- Running 10-20 agents × 5-10 tasks × 10-20 generations = 500-4000 LLM calls
- At ~$0.01-0.03 per call, that's $5-120 in API costs (within $50 Weave credits + personal budget)
- But the TIME is the issue: 500-4000 calls × 2-10 sec each = 15 min to 11 hours
- Evolution needs ENOUGH generations to show emergence, and each generation needs ENOUGH tasks to differentiate agents

**Mitigation strategies:**
1. **Small population:** 8-10 agents (not 20)
2. **Fast tasks:** Use tasks that can be evaluated in < 5 seconds
3. **Parallel evaluation:** Run all agents in a generation concurrently (async)
4. **Fewer generations, more tasks per generation:** 10 generations × 10 tasks = 100 evaluation rounds. With 10 agents, that's 1000 calls total. At 2 sec each with parallelism (10 concurrent), that's ~200 seconds = 3.3 minutes per full evolutionary run.
5. **Pre-run before demo:** Run the evolution offline, save the lineage data to Redis, replay the visualization during demo

**Realistic timeline for one evolutionary run:** ~5-10 minutes with parallelism. You can run 3-5 complete runs during the hackathon to find the most compelling one.

---

## Risk Mitigation

| Risk | Mitigation |
|------|-----------|
| Evolution doesn't converge | Use strong selection pressure (kill bottom 50%) and ensure task diversity. Pre-run multiple times. |
| All agents converge to same strategy | Introduce "niche" pressure — bonus fitness for strategies that work on tasks others fail at |
| Too many LLM calls / too expensive | Small population, fast tasks, parallel execution, pre-run before demo |
| Visualization is hard to build | Marimo has built-in plotting. Phylogenetic tree can be simplified to a directed graph with networkx + matplotlib. |
| Genome crossover is meaningless | Each genome field should be independently functional. Crossover swaps fields, not substrings. This makes every crossover produce a viable agent. |

---

## Demo Script (3 minutes)

**Opening** (20 sec): "What if AI agents evolved like organisms? I built a population of agents that compete, reproduce, and evolve — with one twist: their fitness is measured by how well they predict their own capabilities."

**Live demo** (2 min):
1. Show generation 1: "10 agents with random strategies. Average prediction accuracy: 51% — basically coin flipping."
2. Fast-forward through evolution (show the phylogenetic tree growing)
3. Show generation 15: "Average prediction accuracy: 83%. The population converged on two dominant strategies."
4. Zoom in on the winning strategy: "Evolution discovered that chain-of-thought reasoning + high memory window + conservative confidence calibration is the optimal combination."
5. Show the extinct branches: "These strategies — overconfident, low memory, analogical reasoning — went extinct by generation 7."
6. Show Weave trace of a single agent's prediction cycle

**Close** (30 sec): "Natural selection works. Applied to LLM agents, it produces strategies no human would have designed. Built with Redis for the population store, Marimo for visualization, and Weave for observability."

---

## Why Start Here (Even Though It's Research)

This is the project most likely to produce **genuinely surprising results**. The other projects have predictable outcomes (Compute Oracle will predict prices better, Toolsmith will build more tools). This one might discover something unexpected about which agent strategies survive selection pressure. That unpredictability is both the risk and the reward.

Even if you don't submit this to WeaveHacks, the findings could be:
- A blog post ("What happens when you apply natural selection to LLM agents?")
- A research paper seed
- A framework/library others can use

---

## Relevant Previous Work

- **Corch/Facilitair** (`/Users/bledden/Documents/Corch_by_Fac/`): The 86.4M param foundation model for task routing learned WHICH strategies work for WHICH tasks through traces. Natural selection is an alternative optimization method — evolutionary search vs gradient descent on the same problem (optimal strategy selection).
- **AgentMesh-R** (`/Users/bledden/Documents/agentmesh-r/`): 5 execution strategies (DIRECT, PARTITION, SEQUENTIAL, MAP-REDUCE, RECURSIVE). These could be genome traits that evolve — which execution strategy survives for which task type?
- **Anomaly Hunter** (`/Users/bledden/Documents/anomaly-hunter/`): Multi-agent consensus with adaptive weighting. Adaptive weighting is a simple form of what evolution does — but evolution can discover entirely new strategies, not just reweight existing ones.
- **weavehacks-orchestrator** (`/Users/bledden/Documents/weavehacks-orchestrator/`): Dual-layer learning for self-improving task routing. The "learning which strategies work" is exactly what evolution does, but through population dynamics instead of gradient updates.

## Future: Weight-Level Evolution (Beyond Behavior)

The current system evolves **behavior** — system prompts, reasoning strategies, confidence calibration, temperature. The model weights are fixed; the same model runs for every agent with different configurations. This is analogous to evolving software that runs on identical hardware.

The next level is evolving the **model itself**. Here's the roadmap:

### Phase 1: LoRA Adapter Evolution (Feasible Near-Term)
- Each agent's "genome" includes a lightweight LoRA adapter (~1-10MB)
- After each generation, top-performing agents' interaction logs become fine-tuning data
- A quick LoRA fine-tune (few minutes on consumer GPU) produces the next generation's adapter
- **Crossover**: Merge two parent LoRA adapters (weight averaging, TIES merging, or DARE)
- **Mutation**: Add noise to adapter weights, or fine-tune on a random subset of data
- **Selection pressure now acts on weights**, not just prompts
- Requires: A local open-source base model (e.g., Llama, Mistral, Qwen), GPU for fine-tuning, PEFT/LoRA library

### Phase 2: Architecture Search
- Evolve not just adapter weights but architectural choices: layer count, attention heads, FFN width
- Each genome specifies a model architecture + adapter
- This is essentially Neural Architecture Search (NAS) driven by prediction fitness
- Requires: Significant compute, likely multi-GPU

### Phase 3: Full Neuroevolution
- Start from randomly initialized small models
- No pre-trained base — pure evolutionary discovery of weights
- Population of models competing on prediction tasks
- Closest to biological evolution: the "DNA" is the full weight matrix
- Requires: Large compute budget, but could produce genuinely novel architectures

### Why Start With Behavior Evolution
- **Speed**: Behavior evolution runs in minutes. Weight evolution takes hours/days.
- **Interpretability**: We can read a system prompt and understand what survived. Weight changes are opaque.
- **Proof of concept**: If behavior evolution shows meaningful convergence, it validates the framework for weight-level experiments.
- **Hackathon-feasible**: Behavior evolution can demo 15 generations live. Weight evolution would need pre-computed results.

The behavior layer is the **minimum viable evolution**. The weight layer is where this becomes a research contribution.

---

## Prior Art References

- Darwin Godel Machine (evolutionary agent improvement): sakana.ai/dgm/ | arxiv.org/abs/2505.22954
- Self-Evolving Agents survey: arxiv.org/abs/2508.07407
- Absolute Zero / R-Zero (self-directed learning): Research on agents that generate their own training curricula
- EvoAgentX collection: github.com/EvoAgentX/Awesome-Self-Evolving-Agents
- PyPop7 (population-based optimization): github.com/Evolutionary-Intelligence/pypop
- Neptune AI evolutionary simulation: neptunianeclipse.github.io/ai-evolutionary-simulation/
