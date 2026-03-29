# Failure Is the Teacher: A Survey of Feedback-Driven Self-Correction in Autonomous AI Agent Systems

**Authors:** Research synthesis prepared March 2026

---

## Abstract

Autonomous AI agents are increasingly deployed for complex, multi-step tasks — from scientific research automation to GUI navigation to backend code generation. Yet first-try success rates on non-trivial tasks remain stubbornly low, often below 10% for structurally complex outputs. This paper surveys four primary systems and situates them within the broader landscape of recent research (2025–2026) to argue that **failure is not a terminal state but a structured input to a correction loop**. We analyze in depth AI-Researcher (HKUDS, NeurIPS 2025 Spotlight), the Typia/AutoBe function calling harness (Wrtn Technologies), Feynman (Companion AI), and UI-Voyager (Tencent Hunyuan), then connect their mechanisms to concurrent advances including AgentDebug's failure taxonomy [5], Agent-R's on-the-fly reflection via Monte Carlo Tree Search [6], Live-SWE-agent's runtime self-evolution [7], formal reliability frameworks [8], runtime verification [9], and difficulty-aware orchestration [10]. Across this body of work, we identify four cross-cutting design principles — deterministic verification, structured error localization, iterative refinement with convergence guarantees, and failure-as-data — and propose a unified taxonomy for feedback-driven agent architectures. Our analysis suggests that the reliability ceiling of autonomous agents is determined less by model capability than by the engineering quality of the feedback loop surrounding the model.

---

## 1. Introduction

The deployment of large language models (LLMs) as autonomous agents — systems that take actions in environments rather than merely generating text — has accelerated rapidly since 2024. Agents now write code, navigate GUIs, conduct literature reviews, and orchestrate multi-step workflows. Yet a persistent gap separates demonstration-quality performance from production-grade reliability. Benchmarks consistently reveal that even frontier models fail on the majority of complex agentic tasks on first attempt: GPT-4o achieves 28% on nested tool calling (NESTFUL, EMNLP 2025), constrained decoding covers only 3–41% of hard JSON schemas (JSONSchemaBench, ICLR 2025), and base vision-language models reach 45% on mobile GUI tasks (AndroidWorld).

A naive response is to wait for more capable models. The systems surveyed in this paper take a different approach: they treat the model as one component within an engineered system where **failures are systematically converted into corrective signal**. This is not an isolated insight. Recent work across multiple subfields — agent reliability [8], runtime verification [9], self-evolving agents [11, 12], agentic coding [7, 13], and GUI automation benchmarks [14, 15, 16] — converges on the same conclusion: feedback loop engineering, not model scaling alone, is the primary lever for achieving reliable autonomous behavior.

This survey examines four primary systems in depth, situates them within this broader research landscape, extracts shared architectural principles, and proposes a unified taxonomy for feedback-driven agent design.

### 1.1 Scope and Contributions

We make four contributions:

1. **Detailed technical analysis** of four feedback-driven agent systems spanning scientific research, structured output generation, grounded information synthesis, and GUI automation.
2. **A landscape review** connecting these systems to 20+ concurrent research papers (2025–2026) on agent reliability, self-correction, and self-evolution.
3. **A cross-cutting taxonomy** identifying four design principles that recur across all systems despite their domain differences.
4. **A comparative framework** mapping each system's feedback mechanisms along dimensions of verification type, error granularity, correction mechanism, and convergence properties.

### 1.2 Terminology

We adopt the following definitions throughout:

- **Agent**: An LLM-based system that takes actions in an environment across multiple steps to achieve a goal.
- **Feedback loop**: A cycle in which agent output is evaluated, errors are localized, and corrective information is provided to the agent for retry.
- **Verification oracle**: A deterministic or semi-deterministic function that evaluates whether agent output satisfies task requirements.
- **Fork point**: A state in an execution trace where two trajectories diverge due to different actions taken from equivalent observations.

---

## 2. System Analyses

### 2.1 AI-Researcher: Iterative Multi-Agent Scientific Research

#### 2.1.1 Overview

AI-Researcher [1] is an autonomous system developed by the Hong Kong University Data Systems group (HKUDS) that automates the complete scientific research lifecycle. Accepted as a Spotlight paper at NeurIPS 2025, the system takes either a detailed research idea or a set of reference papers as input and produces implemented algorithms, experimental results, and a complete LaTeX manuscript.

#### 2.1.2 Architecture

The system is built on **MetaChain**, a custom multi-agent orchestration framework supporting asynchronous execution, retry logic, context truncation, and multi-provider LLM compatibility via LiteLLM. Seven specialized agents form the pipeline:

| Agent | Function | Feedback Mechanism |
|-------|----------|--------------------|
| Prepare | Repository discovery and evaluation | Scoring heuristic (stars, recency, code quality) |
| Survey | Literature decomposition into atomic definitions | Three-agent loop: Survey → Paper Survey → Code Survey |
| Idea | Novel concept generation | 5-iteration refinement cycle |
| Plan | Implementation blueprint (dataset, model, training, testing) | Structured template validation |
| ML | Full implementation in Docker | Judge feedback loop |
| Judge | Requirements validation | Code Review sub-agent inspection |
| Experiment Analyzer | Results analysis and follow-up recommendations | Iterative experiment cycles |

#### 2.1.3 Feedback Loop: Judge–ML Agent Iteration

The critical feedback mechanism is the **Judge–ML Agent loop**. After the ML Agent produces an implementation, the Judge Agent systematically checks each atomic academic concept against the code. It employs a subordinate Code Review Agent for detailed file-level inspection. When violations are found, structured diagnostics — specifying the concept, the expected behavior, and the actual implementation gap — are returned to the ML Agent, which revises only the failing components. This loop iterates up to `MAX_ITER_TIMES`.

The ML Agent's instructions enforce a **no-placeholder policy**: patterns such as `pass`, `...`, and `raise NotImplementedError` are explicitly rejected, forcing the agent to produce complete implementations that can be meaningfully evaluated by the Judge.

#### 2.1.4 Memory and Verification

The system uses ChromaDB-backed RAG memory with specialized stores for papers (4096-token chunks with semantic retrieval) and code (indexed with LLM-based reranking). The Survey Agent's **atomic definition tracing** — requiring every concept to be traced through definition → formula → code — serves as a verification mechanism ensuring nothing remains abstract or unimplemented.

#### 2.1.5 Key Design Insight

AI-Researcher treats the research pipeline as a series of **verifiable checkpoints**. Each agent produces output that the next agent can evaluate against explicit criteria. The system's reliability comes not from any single agent being perfect, but from the iterative correction loops between agents — particularly the Judge–ML and Analyzer–ML cycles.

---

### 2.2 Typia/AutoBe: Compiler-Driven Feedback for Structured Output

#### 2.2.1 Overview

The Typia/AutoBe system [2], developed by Wrtn Technologies, addresses a fundamental challenge: LLMs producing valid structured output conforming to complex JSON schemas. When schemas involve recursive union types with 10+ variants nested 3 levels deep (~1,000 structural paths), first-try correctness is structurally improbable — measured at 6.75% for Qwen's `qwen3-coder-next`.

#### 2.2.2 The Harness Architecture

Rather than improving the model or the prompt, the system engineers a **three-layer harness** around the model:

**Layer 1 — Schema Constraint (Prevention):**
TypeScript types are compiled into JSON Schema via Typia's `typia.llm.parameters<T>()`. JSDoc comments become `description` fields; type constraints become validation rules. The critical insight — the "Pink Elephant Principle" — is that schemas constrain by *absence*: if a type doesn't exist in the schema, the model cannot generate it. This is fundamentally more reliable than prompt-based prohibition, which paradoxically draws attention to forbidden outputs.

**Layer 2 — Lenient Parsing (Recovery):**
`ILlmFunction.parse()` recovers from malformed LLM output through:
- Stripping markdown wrappers and prefix text
- Auto-closing unclosed strings and brackets
- Accepting unquoted keys and trailing commas
- Type coercion (string `"1299.99"` → number `1299.99`)
- Recursively parsing double-stringified objects (critical: Qwen 3.5 double-stringifies 100% of union-type fields)

**Layer 3 — Validation Feedback (Correction):**
`ILlmFunction.validate()` detects schema violations and generates inline error comments with exact JSON paths and expected types (e.g., `// expected: "string & Format<\"email\">"`). The model can then fix only the marked fields rather than regenerating everything.

#### 2.2.3 The AutoBe Pipeline

AutoBe applies this harness across a 5-phase backend generation pipeline, each with its own compiler-validator:

1. **Requirements** → `AutoBeAnalyze` structure + checker
2. **Database** → DB schema AST + compiler
3. **API Design** → OpenAPI v3.2 + compiler
4. **Testing** → Expression types (30+ variants) + compiler
5. **Implementation** → TypeScript compiler validation

When compilation fails, structured diagnostics (exact location, target, cause) are passed to a "correct" agent that fixes only the broken parts. This loops until compilation succeeds.

#### 2.2.4 Results

| Model | Active Parameters | Compilation Rate |
|-------|------------------|-----------------|
| Qwen 3.5-397B-A17B | 17B | 100% |
| Qwen 3.5-122B-A10B | 10B | 100% |
| Qwen 3.5-27B | 27B (dense) | 100% |
| Qwen 3.5-35B-A3B | 3B | 99.8% |
| Qwen 3-coder-next | 3B | 99.8% |

The same harness achieves 100% compilation across Qwen, GLM, DeepSeek, and OpenAI with zero model-specific tuning — demonstrating that well-engineered feedback loops absorb model capability differences.

#### 2.2.5 Key Design Insight

The system inverts the conventional wisdom about structured output: instead of demanding higher first-try accuracy, it makes the feedback loop so efficient that even 6.75% initial accuracy converges to 100%. The authors note that their weakest model (3B active parameters, ~10% success rate) was their **most valuable testing tool** — every failure it produced exposed a system vulnerability, and fixing those failures strengthened the pipeline for all models.

---

### 2.3 Feynman: Source-Grounded Verification for Research Agents

#### 2.3.1 Overview

Feynman [3] is an open-source AI research agent (TypeScript, MIT license) by Companion AI that prioritizes **source-grounded outputs** — every factual claim must link directly to a paper, documentation page, or repository URL. It operates as a terminal-based orchestrator for literature review, experiment replication, and paper writing.

#### 2.3.2 Architecture

Feynman is built as a wrapper around the Pi agent runtime (`@mariozechner/pi-ai`), with four specialized subagents and 18 skill modules:

**Subagents:**
- **Researcher** — Evidence gathering with strict integrity rules: existence checking, URL requirements, read-before-cite mandate, no extrapolation from titles/abstracts
- **Reviewer** — Adversarial peer review simulation with severity grading (FATAL / MAJOR / MINOR) and inline annotations with exact quotes
- **Writer** — Structured document production from verified findings
- **Verifier** — Adds inline citations `[1]`, `[2]`, verifies URL resolution, removes unsourced claims, builds numbered Sources sections

#### 2.3.3 Feedback Loop: The Deep Research Workflow

Feynman's `/deepresearch` command executes an 8-step feedback-driven workflow:

1. **Plan** — Extended thinking, task ledger, acceptance criteria (≥2 sources per claim)
2. **Scale** — Determines parallel subagent count (1–6) based on complexity
3. **Spawn Researchers** — Parallel subagents with disjoint coverage, file-based handoffs
4. **Evaluate and Loop** — Gap analysis, follow-up batches, CHANGELOG updates
5. **Write Report** — Lead researcher synthesizes; claim sweep; Mermaid diagrams
6. **Cite** — Verifier agent adds inline citations and checks URLs
7. **Verify** — Reviewer agent provides adversarial review with severity grading
8. **Deliver** — Final artifact + provenance sidecar (date, rounds, source counts)

#### 2.3.4 Verification Mechanisms

Feynman employs several distinctive verification approaches:

- **Honesty labeling**: All claims are marked as `verified`, `unverified`, `blocked`, or `inferred` — the system never obscures evidence gaps
- **Provenance tracking**: Every output gets a `.provenance.md` sidecar documenting sources, methodology, and verification status
- **File-based agent communication**: Subagents write results to files rather than passing content through context windows, preventing hallucination amplification through context pollution
- **CHANGELOG as lab notebook**: Long-running workflows maintain a living record of progress, failures, and decisions

#### 2.3.5 Key Design Insight

Where the other systems in this survey use deterministic verification (compilers, rule-based validators, visual matching), Feynman addresses domains where verification is inherently soft — factual claims about the world cannot be compiler-checked. Its solution is to make the verification *process* rigorous and transparent through adversarial multi-agent review, source requirements, and honesty labeling, even when individual verification steps involve judgment.

---

### 2.4 UI-Voyager: Learning from Failed Trajectories

#### 2.4.1 Overview

UI-Voyager [4] (Tencent Hunyuan, arXiv: 2603.24533) is a self-evolving mobile GUI agent that achieves **81% Pass@1 on AndroidWorld**, surpassing human-level performance (80%) with only a 4B parameter model — outperforming models 60× its size. Its central contribution is a method for extracting step-level training signal from failed task trajectories.

#### 2.4.2 The Problem: Sparse Rewards in Long-Horizon Tasks

In a 30-step GUI task, the only reward signal is binary: success or failure at the end. A single wrong action at step 5 causes the entire trajectory to receive zero reward. Existing methods either discard failed trajectories entirely (wasting information) or apply trajectory-level RL (ambiguous credit assignment). Both approaches fail to identify *which* step was the actual mistake.

#### 2.4.3 Two-Stage Self-Evolving Framework

**Stage 1 — Rejection Fine-Tuning (RFT):**
- A seed task generator synthesizes 7,000+ tasks from 116 templates via parameter perturbation
- The model generates diverse trajectories; a rule-based verifier (Android Debug Bridge) checks completion
- Only successful trajectories are retained for supervised fine-tuning
- After 3 RFT iterations: 37% → 73%, but hits a ceiling because failures are discarded

**Stage 2 — Group Relative Self-Distillation (GRSD):**
The core innovation. GRSD exploits the fact that when running the same task multiple times, trajectories often visit **identical screen states** at certain steps but then diverge because of different actions. These divergence points — **fork points** — are where the agent makes critical decisions.

#### 2.4.4 Fork Point Detection

The fork point detection algorithm uses three mechanisms:

1. **Cross-trajectory state matching via SSIM**: Screenshots are preprocessed (status bar cropped, resized, grayscaled) and compared using Structural Similarity Index. A mean-hash pre-filter (threshold: 0.80) discards obviously dissimilar pairs before expensive SSIM computation.

2. **Transition alignment**: Consecutive states in both trajectories must match (`Same(o_i_success, o_j_fail)` AND `Same(o_{i+1}_success, o_{j+1}_fail)`) to confirm true alignment and prevent false fork detection.

3. **Monotonicity-constrained teacher step selection**: Once failed step `j` matches successful step `i*`, subsequent failed steps can only match successful steps `i ≥ i*`, preserving temporal ordering.

At detected fork points, the system constructs training samples pairing the *context* from the failed trajectory with the *correct action* from the matching successful trajectory. The model teaches itself — no external oracle required.

#### 2.4.5 Results

| Model | Size | Pass@1 |
|-------|------|--------|
| UI-Voyager | 4B | 81.0% |
| Human | — | 80.0% |
| MAI-UI | 235B | 76.7% |
| Seed1.8 | — | 70.7% |
| Gemini-2.5-Pro | — | 69.7% |

GRSD (81%) significantly outperformed standard RL methods — GRPO and PPO both plateaued at ~76% — demonstrating that fork point detection provides superior credit assignment to policy gradient methods for long-horizon tasks.

#### 2.4.6 Key Design Insight

UI-Voyager demonstrates that the information content of failures often exceeds that of successes. A successful trajectory confirms one correct path; a failed trajectory, when aligned with a successful one, identifies the *precise decision boundary* between correct and incorrect behavior. The fork point detection mechanism converts this insight into actionable training signal at step-level granularity.

---

## 3. The Broader Landscape (2025–2026)

The four systems analyzed in Section 2 do not exist in isolation. A wave of concurrent research addresses overlapping concerns — agent failure analysis, self-correction, self-evolution, runtime verification, and reliability measurement. This section maps the broader landscape and draws connections to the primary systems.

### 3.1 Failure Taxonomies and Diagnostic Frameworks

**AgentDebug** [5] (Zhu et al., September 2025) provides the most systematic treatment of *where* and *why* LLM agents fail. The authors introduce **AgentErrorTaxonomy**, a modular classification of failure modes across five agent components: memory, reflection, planning, action, and system-level integration. Paired with **AgentErrorBench** — an annotated dataset of failure trajectories from three benchmarks — and the **AgentDebug** correction framework, the system achieves 24% higher all-correct accuracy and 17% higher step accuracy through iterative root-cause identification and corrective feedback.

AgentDebug's taxonomy is complementary to the systems in Section 2. Where AI-Researcher's Judge Agent checks *domain-specific* correctness (atomic academic definitions), and Typia/AutoBe's compiler checks *structural* correctness (schema conformance), AgentDebug checks *process-level* correctness — was the right tool called? Did the agent maintain accurate state? Did planning produce a viable decomposition? A complete feedback-driven system could layer all three levels of verification.

**Multi-Agent Reflexion (MAR)** [17] (Ozer et al., December 2025) addresses a subtler failure mode: **degeneration of thought** in self-reflection. When a single agent generates actions, evaluates its own behavior, and produces reflections, it tends toward confirmation bias — repeating the same errors with cosmetically different justifications. MAR deploys multiple agents with distinct personas to debate failed reasoning, achieving 47% EM on HotPotQA and 82.7% on HumanEval, surpassing single-model reflection baselines. This validates Feynman's architectural choice of separating Researcher and Reviewer roles rather than having a single agent self-review.

### 3.2 On-the-Fly Reflection and Self-Training

**Agent-R** [6] (Yuan et al., January 2025) introduces a mechanism for agents to **reflect during task execution** rather than only after completion. Using Monte Carlo Tree Search (MCTS), the system constructs training data from error-recovery trajectories: the model identifies its first erroneous step in a failed trajectory, then splices it with a correct path discovered via tree search. This achieves +5.59% performance gains across three interactive environments while avoiding repetitive error loops.

Agent-R's approach is architecturally between UI-Voyager's offline fork point detection and AI-Researcher's online Judge–ML loop. Like UI-Voyager, it identifies specific erroneous steps within trajectories. Like AI-Researcher, it enables mid-execution correction. The MCTS-based trajectory splicing can be seen as a generalization of UI-Voyager's SSIM-based fork point detection — both identify divergence points between correct and incorrect paths, but MCTS explores the space algorithmically rather than relying on visual state matching.

**Self-Improving LLM Agents at Test-Time** [18] (Acikgoz et al., October 2025) proposes a three-phase test-time improvement method: identifying struggling samples, generating similar examples from uncertain cases, and fine-tuning with those new samples. This achieves approximately 5.48% absolute accuracy gain while requiring 68× fewer training samples than standard approaches. The insight — that the model's own uncertainty signal identifies exactly where additional training is most valuable — echoes the Typia/AutoBe finding that the weakest model is the best stress-tester.

### 3.3 Self-Evolving Agents

**Live-SWE-agent** [7] (Xia et al., November 2025) represents the most radical self-evolution approach: a software engineering agent that **autonomously and continuously evolves its own implementation** during runtime. Starting with only a minimal scaffold with bash tools, the agent enhances its own capabilities on-the-fly as it encounters new problem types. It achieves 77.4% on SWE-bench Verified (without test-time scaling) and 45.8% on SWE-Bench Pro — both state-of-the-art results surpassing manually crafted agents.

Live-SWE-agent's self-evolution goes beyond the systems in Section 2 in a critical way: it modifies not just its outputs but its own *architecture*. Where UI-Voyager updates model weights and AI-Researcher iterates within a fixed pipeline, Live-SWE-agent demonstrates that the feedback loop itself can be a target of optimization. This suggests a hierarchy of feedback: Level 1 corrects outputs, Level 2 corrects strategies, and Level 3 corrects the correction mechanism itself.

Two comprehensive surveys contextualize these developments. Fang et al. [11] propose a unified framework for self-evolving agents with four components — System Inputs, Agent System, Environment, and Optimisers — covering evolution techniques for biomedicine, programming, and finance. Gao et al. [12] examine self-evolution through three dimensions: *what* components evolve (memory, tools, models), *when* adaptation occurs (online vs. offline), and *how* evolution mechanisms function (reinforcement, self-play, experience accumulation).

### 3.4 Agent Reliability and Runtime Verification

**Towards a Science of AI Agent Reliability** [8] (Rabanser et al., February 2026) provides the most rigorous treatment of reliability measurement. The authors propose 12 metrics across four dimensions:

| Dimension | Metrics | Key Finding |
|-----------|---------|-------------|
| **Consistency** | Cross-run variance, output stability | Agents produce different results on identical inputs across runs |
| **Robustness** | Perturbation sensitivity, adversarial resilience | Minor prompt variations cause disproportionate failures |
| **Predictability** | Confidence calibration, failure forecasting | Models are poorly calibrated about when they will fail |
| **Safety** | Constraint adherence, recovery from unsafe states | Recent capability gains yield only small reliability improvements |

Their evaluation of 14 models across two benchmarks reveals a sobering finding: **recent capability gains have yielded only small improvements in reliability**. This directly supports our reliability inversion thesis — capability and reliability are orthogonal axes, and feedback loop engineering addresses the latter.

**AgentGuard** [9] (Koohestani, September 2025) introduces **runtime verification** for autonomous agents. It functions as an inspection layer that converts agent input-output data into formal events reflecting state transitions, then uses online learning to construct a Markov Decision Process representing emergent behavior. Probabilistic model checking continuously verifies quantitative properties and calculates failure probability under specific constraints. This approach could be composed with any of the four primary systems to provide a formal safety layer atop their domain-specific feedback loops.

**Agent Safety Alignment via Reinforcement Learning** [19] (July 2025) proposes the first unified safety-alignment framework for tool-using agents using sandboxed RL. A related benchmark [20] (December 2025) reveals 30–71% misalignment rates across 12 LLMs, with a counterintuitive finding: **stronger reasoning does not ensure safety**. This underscores that feedback loops designed for correctness do not automatically guarantee safety — a distinct verification layer is needed.

### 3.5 Multi-Agent Orchestration

**Evolving Orchestration** [21] (Dang et al., NeurIPS 2025) proposes a "puppeteer-style" paradigm where a centralized orchestrator dynamically directs agents in response to evolving task states, trained via reinforcement learning. The orchestrator learns compact, cyclical reasoning patterns that achieve improved performance with lower computational requirements — demonstrating that the orchestration layer itself benefits from learning.

**Difficulty-Aware Agentic Orchestration (DAAO)** [10] (September 2025, WWW 2026) dynamically adjusts workflow complexity based on task difficulty, achieving +11.21% accuracy at 64% of the cost. This addresses a limitation of fixed-pipeline systems like AI-Researcher: not every task requires the full 7-agent pipeline. Simple tasks waste resources when routed through complex workflows, while hard tasks may need additional iteration cycles.

**Multi-Agent LLM Orchestration for Incident Response** [22] (Drammeh, November 2025) provides striking empirical evidence: through 348 controlled experiments, multi-agent orchestration achieved **100% actionable recommendation rate** versus 1.7% for single-agent approaches, with **zero quality variance** across trials. This aligns with Feynman's multi-agent architecture and suggests that the separation of concerns (generation, verification, correction) is not merely an architectural preference but a reliability necessity.

### 3.6 Benchmarks Revealing the Gap

Several recent benchmarks quantify the gap that feedback-driven systems must bridge:

- **SWE-Bench Pro** [13] (September 2025): 1,865 problems requiring "hours to days for a professional software engineer," spanning multiple files — far harder than the original SWE-Bench. Live-SWE-agent's 45.8% shows substantial progress, but over half of real-world engineering tasks remain unsolved.
- **TheAgentCompany** [23] (Xu et al., December 2024): Professional workplace tasks where the best agent completes only 30% autonomously, with difficult long-horizon tasks remaining beyond reach.
- **WebChoreArena** [14] (June 2025): Labor-intensive web tasks where top LLMs drop from 54.8% (WebArena) to 37.8%, exposing brittleness on sustained multi-step reasoning.
- **WebTestBench** [16] (March 2026): Automated web testing where all models fail to exceed 30% F1, with GPT-5.1 achieving only 26.4%.
- **ProBench** [15] (November 2025, AAAI 2026): GUI tasks with process-level evaluation showing that "advanced GUI agents show significant limitations for real-world scenarios."
- **MCPAgentBench** [24] (December 2025): Tool-use via Model Context Protocol, revealing significant performance differences on complex multi-step tool invocations.

These benchmarks collectively demonstrate that the reliability gap identified in Section 1 is not narrowing through model scaling alone — validating the central thesis of this survey.

### 3.7 Infrastructure: Memory, Tools, and SDKs

Several infrastructure-level advances support the feedback-driven paradigm:

- **A-MEM** [25] (February 2025) introduces Zettelkasten-inspired agentic memory with dynamically interconnected knowledge networks, enabling agents to accumulate and retrieve experience across tasks — a prerequisite for learning from failure at the system level.
- **OpenHands SDK** [26] (November 2025) provides a composable framework for building software development agents with native sandboxed execution, lifecycle control, and built-in security — the kind of infrastructure that makes production-grade feedback loops feasible.
- **STED and Consistency Scoring** [27] (November 2025) introduces Semantic Tree Edit Distance for JSON comparison, enabling nuanced measurement of structured output quality beyond binary pass/fail — directly relevant to the Typia/AutoBe harness's incremental correction approach.

---

## 4. Comparative Analysis

### 3.1 A Taxonomy of Feedback Mechanisms

We identify four design principles that recur across all four systems:

#### Principle 1: Deterministic Verification

Every system employs some form of verification oracle that provides ground-truth evaluation of agent output:

| System | Verification Oracle | Type |
|--------|-------------------|------|
| AI-Researcher | Judge Agent + Code Review Agent | Semi-deterministic (LLM-based with structured criteria) |
| Typia/AutoBe | TypeScript compiler + JSON Schema validator | Fully deterministic |
| Feynman | Adversarial Reviewer + URL resolution + source requirements | Semi-deterministic (process-rigorous) |
| UI-Voyager | Android Debug Bridge task completion check | Fully deterministic |

The strongest convergence guarantees come from fully deterministic oracles (Typia achieves 99.8–100%), while semi-deterministic oracles trade precision for applicability to softer domains.

#### Principle 2: Structured Error Localization

All systems go beyond binary success/failure to localize *where* and *why* errors occurred:

| System | Localization Granularity | Mechanism |
|--------|------------------------|-----------|
| AI-Researcher | Concept-level | Atomic academic definition tracing |
| Typia/AutoBe | Field-level | JSON path + expected type annotations |
| Feynman | Claim-level | FATAL/MAJOR/MINOR severity + inline quotes |
| UI-Voyager | Step-level | Fork point detection via SSIM matching |

This is the critical differentiator from naive retry strategies. Localized error information allows the correction agent to modify only the failing component, preserving correct work and dramatically reducing the search space for fixes.

#### Principle 3: Iterative Refinement with Convergence Properties

Each system implements bounded iteration toward correctness:

| System | Iteration Mechanism | Convergence Signal |
|--------|--------------------|--------------------|
| AI-Researcher | Judge → ML Agent loop (max `MAX_ITER_TIMES`) | All atomic definitions validated |
| Typia/AutoBe | Compile → diagnose → correct loop | Zero compilation errors |
| Feynman | Research → Review → Revise → Verify | All claims sourced; no FATAL findings |
| UI-Voyager | RFT iterations → GRSD refinement | Pass@1 improvement plateau |

The Typia/AutoBe system has the strongest convergence guarantee: since the compiler is deterministic and the error feedback is precise, each iteration resolves at least one class of errors, ensuring monotonic progress. The other systems have softer convergence properties but bound worst-case behavior through iteration limits.

#### Principle 4: Failure as Data

Perhaps the most profound shared insight: all four systems treat failures as first-class data rather than waste:

- **AI-Researcher**: Failed implementations generate structured diagnostics that guide the next iteration
- **Typia/AutoBe**: The weakest model (3B parameters, ~10% success) is the most valuable testing tool — its failures expose system vulnerabilities
- **Feynman**: `unverified` and `blocked` labels are explicit outputs, not hidden states; the CHANGELOG records failures as methodology
- **UI-Voyager**: Failed trajectories contain more targeted training signal than successes via fork point detection

### 3.2 Comparative Dimensions

| Dimension | AI-Researcher | Typia/AutoBe | Feynman | UI-Voyager |
|-----------|--------------|-------------|---------|------------|
| **Domain** | Scientific research | Structured code generation | Literature synthesis | GUI automation |
| **Agent count** | 7 specialized | 40+ pipeline agents | 4 subagents + 18 skills | Single agent (self-improving) |
| **Feedback timing** | Post-generation | Post-compilation | Post-writing | Post-training (offline) |
| **Correction mechanism** | Agent re-generation | Targeted field repair | Revision with source addition | Weight update via distillation |
| **Model dependency** | Multi-model via LiteLLM | Model-agnostic (same harness works across vendors) | Multi-provider (20+) | Single model (Qwen3-VL-4B) |
| **Failure utilization** | Diagnostic-driven retry | Diagnostic-driven retry | Transparent labeling | Training signal extraction |

### 3.3 The Reliability Inversion

A striking pattern emerges from comparing these systems: **the reliability of the overall system is inversely correlated with dependence on first-try model accuracy**. Typia/AutoBe achieves the highest reliability (99.8–100%) while starting from the lowest first-try accuracy (6.75%). UI-Voyager surpasses human performance with a 4B model that starts at 45%. AI-Researcher produces complete research papers despite individual agent outputs requiring multiple revisions.

This suggests a **reliability inversion principle**: beyond a minimum capability threshold, investing in feedback loop engineering yields higher returns than investing in model capability. The Typia/AutoBe results make this explicit — the same harness achieves identical compilation rates across models ranging from 3B to 397B active parameters.

---

## 5. Discussion

### 5.1 When Feedback Loops Suffice and When They Don't

The systems surveyed address tasks where:
1. **Correctness is verifiable** — whether by compiler, rule-based checker, source resolution, or visual state comparison
2. **Errors are localizable** — the system can identify which part of the output is wrong
3. **Partial credit is meaningful** — fixing one error doesn't invalidate the rest of the output

Tasks lacking these properties — open-ended creative generation, ethical reasoning, tasks with no ground truth — may not benefit from the same feedback loop architecture. The boundary of this approach is fundamentally the boundary of verifiability.

Notably, the safety alignment literature [19, 20] reveals an important caveat: feedback loops designed for *correctness* do not automatically address *safety*. The finding that stronger reasoning does not ensure safety [20] suggests that safety verification requires its own dedicated oracle, separate from task-completion verification. AgentGuard's runtime verification framework [9] points toward how this might be achieved through continuous probabilistic model checking.

### 5.2 The Cost of Feedback

Feedback loops trade compute for reliability. Each iteration requires additional LLM calls (AI-Researcher, Feynman), compilation cycles (Typia/AutoBe), or training steps (UI-Voyager). The economic viability depends on:

- **Cost of failure** vs. **cost of iteration**: For scientific research or production backend generation, the cost of an undetected error far exceeds the cost of additional LLM calls
- **Convergence speed**: Structured error localization dramatically reduces the number of iterations needed compared to binary feedback
- **Amortization**: UI-Voyager's GRSD training cost is amortized across all future inference, making the per-task cost negligible at scale
- **Adaptive complexity**: DAAO [10] demonstrates that cost can be reduced by 36% through difficulty-aware routing — simple tasks get simpler pipelines, hard tasks get the full treatment

### 5.3 Toward a Unified Feedback Architecture

Despite their domain differences, the primary and landscape systems share a remarkably similar abstract architecture:

```
┌─────────────┐     ┌──────────────┐     ┌─────────────────┐
│   Agent      │────▶│  Verification │────▶│ Error           │
│   (Generate) │     │  Oracle       │     │ Localization    │
└─────────────┘     └──────────────┘     └─────────────────┘
       ▲                                          │
       │              ┌──────────────┐            │
       └──────────────│  Correction   │◀───────────┘
                      │  Signal       │
                      └──────────────┘
```

The differences lie in the instantiation of each component:
- **Verification** ranges from compiler checks (Typia) to adversarial LLM review (Feynman) to probabilistic model checking (AgentGuard [9])
- **Localization** ranges from JSON paths (Typia) to failure taxonomies (AgentDebug [5]) to fork point detection (UI-Voyager) to MCTS-based trajectory analysis (Agent-R [6])
- **Correction** ranges from in-context retry (AI-Researcher) to targeted field repair (Typia) to model weight updates (UI-Voyager) to self-architecture modification (Live-SWE-agent [7])

The landscape review reveals a **hierarchy of feedback loops**:

| Level | What is corrected | Example Systems |
|-------|------------------|-----------------|
| **L1: Output** | The agent's current output | Typia/AutoBe, AI-Researcher Judge loop |
| **L2: Strategy** | The agent's approach to the task | Agent-R [6], MAR [17], Feynman's adversarial review |
| **L3: Capability** | The agent's model weights | UI-Voyager GRSD, Self-Improving Agents [18] |
| **L4: Architecture** | The agent's own structure and tools | Live-SWE-agent [7] |

Most deployed systems operate at L1–L2. The frontier is L3–L4, where the feedback loop itself becomes a target of optimization. Live-SWE-agent [7] is the most striking example: a minimal scaffold that evolves its own tool set, achieving state-of-the-art results by optimizing the correction mechanism itself.

### 5.4 The Reliability–Capability Orthogonality

The reliability framework of Rabanser et al. [8] provides formal grounding for the reliability inversion observed in Section 4.3. Their 12 metrics across four dimensions (consistency, robustness, predictability, safety) are largely orthogonal to standard capability benchmarks. A model can score highly on capability while exhibiting poor consistency (different results on identical inputs across runs) and poor predictability (miscalibrated confidence about when it will fail).

This orthogonality explains why the feedback loop engineering approach works: it addresses dimensions that model scaling does not. The Typia/AutoBe system's model-agnostic compilation rates and multi-agent incident response's zero quality variance [22] are not anomalies — they are the expected outcome of engineering for reliability rather than capability.

### 5.5 Implications for Agent System Design

We distill the following design recommendations, informed by both the primary systems and the broader landscape:

1. **Design the verifier before the generator.** The quality ceiling of an agent system is determined by the quality of its verification oracle. Invest in precise, localizing verifiers. AgentDebug's five-component failure taxonomy [5] provides a useful checklist for verification coverage.

2. **Prefer schemas over prompts for constraint specification.** The Pink Elephant Principle (Typia/AutoBe) generalizes: constraints expressed as structural schemas are more reliable than natural language instructions.

3. **Make failure states explicit and structured.** Every system benefits from representing failure with the same precision as success — specific locations, expected vs. actual values, severity grades. AgentDebug [5] and STED [27] provide frameworks for structured failure representation.

4. **Test with the weakest viable model.** Following Typia/AutoBe's insight, weak models are superior stress-testers. A system robust to a 3B model's errors is robust to everything. Self-Improving Agents [18] formalizes this: the model's own uncertainty identifies where improvement is most valuable.

5. **Separate generation from verification roles.** AI-Researcher's Judge/ML split, Feynman's Researcher/Reviewer/Verifier division, and MAR's multi-persona debate [17] all enforce adversarial dynamics that catch errors self-review would miss.

6. **Adapt feedback intensity to task difficulty.** DAAO [10] shows that fixed-complexity pipelines waste resources on easy tasks. Difficulty-aware routing reduces cost by 36% without sacrificing accuracy.

7. **Consider feedback at multiple levels.** Output-level correction (L1) is necessary but often insufficient. Strategy-level correction (L2, via Agent-R [6] or MAR [17]) catches systematic errors. Capability-level correction (L3, via UI-Voyager) amortizes learning across tasks. Architecture-level correction (L4, via Live-SWE-agent [7]) enables open-ended improvement.

8. **Layer safety verification atop correctness verification.** Correctness and safety are orthogonal concerns [19, 20]. AgentGuard [9] shows how runtime verification can provide a formal safety layer independent of task-specific feedback loops.

---

## 6. Conclusion

The systems surveyed in this paper — four in depth and twenty more across the broader 2025–2026 landscape — represent a maturing paradigm in AI agent engineering. They share the conviction that **reliability is an architectural property, not a model property**. First-try accuracy is a starting condition, not a ceiling; what matters is the system's ability to detect, localize, and correct errors through structured feedback.

Three findings stand out:

**The reliability inversion is real and reproducible.** The system with the lowest first-try accuracy (Typia/AutoBe at 6.75%) achieves the highest end-to-end reliability (99.8–100%). Multi-agent incident response [22] achieves 100% actionable recommendations versus 1.7% for single-agent approaches. UI-Voyager surpasses human performance with a 4B model. This is not cherry-picking — Rabanser et al.'s formal reliability framework [8] confirms that capability and reliability are orthogonal dimensions.

**Feedback loops form a hierarchy.** The field is progressing from output-level correction (L1) through strategy-level (L2) and capability-level (L3) to architecture-level self-modification (L4). Live-SWE-agent [7] achieves state-of-the-art results by evolving its own tool set — the correction mechanism optimizing itself. This hierarchy suggests a research agenda: what are the theoretical limits of self-referential feedback?

**The gap between benchmarks and production remains vast.** Despite impressive results on established benchmarks, newer and harder evaluations consistently reveal fragility: 30% on workplace tasks [23], 37.8% on web chores [14], 26.4% F1 on web testing [16]. The feedback-driven approach has demonstrated it can close this gap in specific domains (Typia/AutoBe, UI-Voyager), but generalizing to arbitrary domains with arbitrary verification oracles remains an open challenge.

The "failure is the teacher" principle manifests differently across domains — as compiler diagnostics in structured output, as adversarial review in research synthesis, as concept-level validation in scientific implementation, as fork point detection in GUI navigation, as failure taxonomies in agent debugging [5], and as MCTS-based trajectory splicing in reflective agents [6] — but the underlying mechanism is universal: **systematic conversion of error signal into corrective action**. As autonomous agents are deployed in increasingly high-stakes domains, this principle may prove more important than any single advance in model capability.

---

## References

### Primary Systems

[1] HKUDS. "AI-Researcher: Autonomous End-to-End Scientific Research." NeurIPS 2025 (Spotlight). GitHub: https://github.com/HKUDS/AI-Researcher

[2] Nam, J. "[Qwen Meetup] Function Calling Harness: From 6.75% to 100%." dev.to, March 2026. AutoBe: https://github.com/wrtnlabs/autobe. Typia: https://github.com/samchon/typia

[3] Companion AI. "Feynman: AI Research Agent." GitHub: https://github.com/getcompanion-ai/feynman

[4] Lin, Z., Liu, F., Yang, Y., et al. "UI-Voyager: A Self-Evolving GUI Agent Learning via Failed Experience." arXiv:2603.24533, March 2026. GitHub: https://github.com/ui-voyager/UI-Voyager

### Failure Analysis and Self-Correction

[5] Zhu, K., Liu, Z., Li, B., et al. "Where LLM Agents Fail and How They Can Learn From Failures." arXiv:2509.25370, September 2025.

[6] Yuan, S., Chen, Z., Xi, Z., et al. "Agent-R: Training Language Model Agents to Reflect via Iterative Self-Training." arXiv:2501.11425, January 2025.

### Self-Evolving Agents

[7] Xia, C.S., Wang, Z., Yang, Y., et al. "Live-SWE-agent: Can Software Engineering Agents Self-Evolve on the Fly?" arXiv:2511.13646, November 2025.

### Reliability and Verification

[8] Rabanser, S., Kapoor, S., Kirgis, P., et al. "Towards a Science of AI Agent Reliability." arXiv:2602.16666, February 2026.

[9] Koohestani, R. "AgentGuard: Runtime Verification of AI Agents." arXiv:2509.23864, September 2025.

### Orchestration

[10] "DAAO: Difficulty-Aware Agentic Orchestration." arXiv:2509.11079, September 2025. WWW 2026.

### Surveys

[11] Fang, J., Peng, Y., Zhang, X., et al. "A Comprehensive Survey of Self-Evolving AI Agents." arXiv:2508.07407, August 2025.

[12] Gao, H., Geng, J., Hua, W., et al. "A Survey of Self-Evolving Agents: What, When, How, and Where to Evolve." arXiv:2507.21046, July 2025.

### Benchmarks

[13] Deng, X., Da, J., Pan, E., et al. "SWE-Bench Pro: Can AI Agents Solve Long-Horizon Software Engineering Tasks?" arXiv:2509.16941, September 2025.

[14] Miyai, A., Zhao, Z., Egashira, K., et al. "WebChoreArena: Evaluating Web Browsing Agents on Realistic Tedious Web Tasks." arXiv:2506.01952, June 2025.

[15] Yang, L., Wang, Z., Tang, X., et al. "ProBench: Benchmarking GUI Agents with Accurate Process Information." arXiv:2511.09157, November 2025. AAAI 2026.

[16] Kong, F., Zhang, J., Yue, Y., et al. "WebTestBench: Evaluating Computer-Use Agents towards End-to-End Automated Web Testing." arXiv:2603.25226, March 2026.

### Multi-Agent Reflection and Orchestration

[17] Ozer, O., Wu, G., Wang, Y., et al. "MAR: Multi-Agent Reflexion Improves Reasoning Abilities in LLMs." arXiv:2512.20845, December 2025.

[18] Acikgoz, E.C., Qian, C., Ji, H., et al. "Self-Improving LLM Agents at Test-Time." arXiv:2510.07841, October 2025.

### Safety and Alignment

[19] "Agent Safety Alignment via Reinforcement Learning." arXiv:2507.08270, July 2025.

[20] "Outcome-Driven Constraint Violations Benchmark." arXiv:2512.20798, December 2025.

[21] Dang, Y., Qian, C., Luo, X., et al. "Multi-Agent Collaboration via Evolving Orchestration." arXiv:2505.19591, NeurIPS 2025.

[22] Drammeh, P. "Multi-Agent LLM Orchestration Achieves Deterministic, High-Quality Decision Support for Incident Response." arXiv:2511.15755, November 2025.

### Infrastructure

[23] Xu, F.F., Song, Y., Li, B., et al. "TheAgentCompany: Benchmarking LLM Agents on Consequential Real World Tasks." arXiv:2412.14161, December 2024.

[24] Liu, W., Liu, Z., Dai, E., et al. "MCPAgentBench: A Real-world Task Benchmark for Evaluating LLM Agent MCP Tool Use." arXiv:2512.24565, December 2025.

[25] "A-MEM: Agentic Memory for LLM Agents." arXiv:2502.12110, February 2025.

[26] Wang, X., Rosenberg, S., Michelini, J., et al. "The OpenHands Software Agent SDK." arXiv:2511.03690, November 2025.

[27] "STED and Consistency Scoring for Structured Output." arXiv:2512.23712, November 2025.

### Prior Benchmarks

[28] NESTFUL: Nested Function Call Evaluation. EMNLP 2025.

[29] JSONSchemaBench: Constrained Decoding Benchmark. ICLR 2025.
