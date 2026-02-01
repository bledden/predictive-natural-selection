# WeaveHacks 3 - Context Handoff

**Date:** January 31 - February 1, 2026
**Event:** WeaveHacks 3 (W&B AI Agent Hackathon)
**Submissions due:** Sunday Feb 1, 1:30 PM

---

## Target Prize: Best Self-Improving Agent ($1,000 + TRMNL e-ink frame)

This is the most achievable category given existing work. Grand Prize and Runner-up are also in play if execution is strong.

---

## Priority Projects (Self-Improving / Agent Mesh)

### 1. AgentMesh-R (TOP PRIORITY)
**Path:** `/Users/bledden/Documents/agentmesh-r`
**What:** Recursive, self-improving multi-agent system with RLM-style task decomposition and memory-based learning.

**Key capabilities:**
- 5 execution strategies: DIRECT, PARTITION, SEQUENTIAL, MAP-REDUCE, RECURSIVE
- 4 agent types: Planner, Executor, Synthesizer, Memory
- Memory Agent extracts generalizable patterns from successful executions
- MongoDB Atlas vector search for semantic pattern matching and reuse
- FastAPI REST API + CLI interface

**Tech stack:** Python 3.11+, MongoDB Atlas, Fireworks AI, Voyage AI embeddings, FastAPI, Galileo AI quality gates

**Key files:**
- `src/agentmesh/orchestrator.py` — Main recursive execution loop (587 lines)
- `src/agentmesh/agents/planner.py` — Strategy selection
- `src/agentmesh/agents/memory_agent.py` — Pattern learning/extraction
- `src/agentmesh/demo.py` — Demo workflows
- `.env.example` — Required API keys

**State:** Single initial commit. Core architecture complete. Needs demo polish and real execution traces.

**Why this wins "Best Self-Improving Agent":** Explicit memory-based learning loop — the system literally gets better at task decomposition by extracting patterns from past successes. This is the clearest self-improvement story.

---

### 2. CodeSwarm
**Path:** `/Users/bledden/Documents/codeswarm`
**What:** Self-improving multi-agent code generation. Turns sketches/wireframes into production code using 5 specialized agents with quality gates and autonomous learning.

**Key capabilities:**
- 5 agents: Architecture, Implementation, Security, Testing, Vision
- Quality-driven iteration (90+ threshold to pass)
- Autonomous learning adapted from Anomaly Hunter
- Multi-model swarm: Claude Sonnet 4.5, GPT-5 Pro, Grok-4 via OpenRouter

**Tech stack:** Python, LangGraph orchestration, OpenRouter, Galileo evaluation, Weave observability

**State:** Demo-ready (90% confidence). All tests passing. 2,170+ lines production code.

**Hackathon angle:** Multi-model swarm that self-improves through quality feedback loops.

---

### 3. Weavehacks-Orchestrator (Self-Improving Orchestrator)
**Path:** `/Users/bledden/Documents/weavehacks-orchestrator`
**What:** Dual-layer learning system for self-improving task decomposition and routing.

**Key capabilities:**
- Fast in-memory cache + slow persistent database (dual-layer learning)
- Learns which decomposition strategies work best over iterations
- Visible learning progression within 5 iterations
- Goal: >80% strategy accuracy after 20 tasks

**Tech stack:** Python 3.11+, W&B Weave, SQLAlchemy/SQLite, OpenAI, Anthropic, Spacy

**State:** Hackathon prototype (October 2024). Not git-versioned. Has demo scenarios.

**Hackathon angle:** Purpose-built for WeaveHacks. Shows measurable improvement over iterations with W&B Weave tracing.

---

### 4. Weavehacks-Collaborative (Facilitair Sequential Agents)
**Path:** `/Users/bledden/Documents/weavehacks-collaborative`
**What:** Sequential AI collaboration: Architect -> Coder -> Reviewer -> Refiner -> Documenter.

**Key capabilities:**
- 73% pass rate vs 19% single-model on 100-task benchmark
- +36.8% quality improvement
- 4-layer evaluation with hallucination detection
- Full W&B Weave integration

**Tech stack:** Python 3.9+, FastAPI, W&B Weave, OpenRouter (200+ models)

**State:** Production-ready. 10,000+ lines, 85%+ test coverage.

**Hackathon angle:** Proven results with hard numbers. Strong "Best Use of Weave" candidate too.

---

## Secondary Projects (Useful Components / Fallbacks)

### 5. Anomaly Hunter
**Path:** `/Users/bledden/Documents/anomaly-hunter`
**What:** Multi-agent anomaly detection with 3 parallel agents + consensus voting. Autonomous adaptive weighting.

**State:** Production-ready. 60+ detections, 100% detection rate, 75.6% avg confidence.
**Angle:** Proven multi-agent consensus pattern. +42.5% vs single-agent baselines.

### 6. Corch/Facilitair (Corch_by_Fac)
**Path:** `/Users/bledden/Documents/Corch_by_Fac`
**What:** AI task orchestration platform with custom 86.4M parameter foundation model for routing.

**State:** Beta-ready. V13 model at 95.86% validation accuracy. 228 MCP integrations, 53 models deployed.
**Angle:** Self-improving via trace collection -> retrain loop. Foundation model learns optimal routing from usage data.

### 7. Facilitair_v2
**Path:** `/Users/bledden/Documents/Facilitair_v2`
**What:** Multi-agent orchestration with 5 execution strategies and foundation model in development (5.75B params target).

**State:** Beta-ready. 305 training traces collected. Core platform complete.
**Angle:** Self-improving routing from real usage data.

### 8. SecondNature
**Path:** `/Users/bledden/Documents/secondnature`
**What:** Privacy-preserving collaborative reasoning. Two Expert LLMs analyze string fragments without exposing raw data; Mediator reconstructs via targeted follow-ups.

**State:** Early-stage research. 91+ unit tests passing. Core reasoning pipeline working.
**Angle:** Novel multi-agent collaboration with information hiding.

### 9. Dendritic Hackathon
**Path:** `/Users/bledden/Documents/dendritic-hackathon`
**What:** Neural network compression using Perforated AI dendritic optimization. Self-improving compression pipeline with plateau detection.

**State:** Active development. In-progress 35-epoch test. Production-ready training pipeline.
**Angle:** Self-improving model compression, but hardware-intensive (needs GPU).

---

## Sponsor Integration Opportunities

| Sponsor | Relevant Project | Integration Path |
|---------|-----------------|------------------|
| **W&B Weave** | All projects | Tracing/observability already integrated in Collaborative + Orchestrator. Add to AgentMesh-R for "Best Use of Weave" |
| **Redis** | AgentMesh-R | Replace or augment MongoDB with Redis for fast pattern cache + vector search |
| **Browserbase/Stagehand** | CodeSwarm | Add web automation as an agent capability |
| **Vercel** | Any frontend | Deploy demo dashboard on Vercel |
| **Daily/Pipecat** | tinker-voice | Voice-controlled agent interaction layer |
| **Marimo** | Any | Interactive notebook demo of agent learning curves |
| **Google Cloud ADK/A2A** | AgentMesh-R | Use ADK for agent definitions, A2A for inter-agent protocol |

---

## Recommended Strategy

**Option A: Polish AgentMesh-R (highest ceiling)**
- Already has the self-improving architecture
- Add W&B Weave tracing for observability (sponsor prize eligible)
- Create compelling demo showing pattern extraction improving over 5-10 tasks
- Risk: needs MongoDB Atlas setup, Fireworks/Voyage API keys

**Option B: Merge Orchestrator + Collaborative (safest)**
- Orchestrator has the self-improving routing logic
- Collaborative has proven quality results + Weave integration
- Combine: self-improving routing that selects between collaboration strategies
- Risk: integration complexity in 24 hours

**Option C: CodeSwarm with Weave (most demo-friendly)**
- Sketch/wireframe -> production code is visually impressive
- Quality improvement loop is measurable
- Already demo-ready
- Risk: less novel "self-improving" story vs AgentMesh-R

---

## Key API Keys Needed

Check `.env.example` files in each project. Common requirements:
- OpenAI API key
- Anthropic API key
- Fireworks AI key (AgentMesh-R)
- Voyage AI key (AgentMesh-R embeddings)
- MongoDB Atlas connection string (AgentMesh-R)
- OpenRouter API key (CodeSwarm, Collaborative)
- W&B API key (all projects)
- Galileo AI key (CodeSwarm quality gates)

---

## Schedule Alignment

| Time | Action |
|------|--------|
| 9:00 AM Sat | Arrive, set up environment |
| 9:30 AM | Kickoff - confirm project choice |
| 10:15 AM | Start hacking - get core demo running |
| 12:45 PM | Lunch presentation (optional) |
| Afternoon | Build self-improving demo loop + Weave integration |
| 6:30 PM | Dinner - checkpoint progress |
| Evening | Polish demo, record video (Social Media Prize) |
| 9:00 AM Sun | Final polish |
| 12:30 PM | Lunch - prep presentation |
| 1:30 PM | Submit |
| 2:00 PM | Present |

---

## Judge-Specific Notes

- **Kwindla (Daily/Pipecat):** Voice agent angle if using tinker-voice
- **Vjeux (Meta):** Clean frontend demo, React-based dashboards
- **Shadi Saba (CoreWeave):** Distributed training / ML infrastructure depth
- **Matthew Berman:** Impressive demo > technical depth. Make it visual.
- **Itamar Friedman (Qodo):** Code quality, AI-assisted development (CodeSwarm angle)
- **Talon Miller (Redis):** Redis integration for agent memory/caching
- **George Cameron (Artificial Analysis):** Benchmarking, measurable improvements
- **Karan Vaidya (Composio):** Tool integration, SaaS access for agents
