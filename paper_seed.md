# Confirmation Bias in Self-Improving AI: Measuring the Gap Between Self-Reported and Actual Capability Growth

---

## Abstract

Self-improving AI systems that define, evaluate, and optimize their own performance metrics face an inherent risk: confirmation bias. When the same system generates both the challenges and the solutions, it can inflate its own scores without genuine capability growth. We present the Infinite Seed, a minimal self-evolving Python program that rewrites its own source code using an LLM as the mutation engine. The seed defines internal capability challenges and is scored against them, but is also evaluated against a fixed external benchmark it cannot see or modify. The gap between internal and external scores — the *bias gap* — quantifies confirmation bias in self-improvement. We describe the experimental framework, the dual-scoring methodology, and its implications for the safety and evaluation of recursive self-improvement in AI systems.

---

## 1. Introduction

Recursive self-improvement — an AI system that improves its own capabilities — is a central concern in AI safety research. Recent systems demonstrate this at various levels: Live-SWE-agent [1] modifies its own tools at runtime, the Darwin Godel Machine [2] rewrites its own code via evolutionary search, and Hyperagents [3] make even their self-modification procedure editable.

A critical assumption underlies all such systems: that the improvement is *real*. When a self-improving system reports higher scores over time, we assume it has genuinely become more capable. But what if the system has instead learned to define easier challenges for itself, to construct metrics that inflate its apparent progress, or to optimize for the measurement rather than the underlying capability?

This is not hypothetical. Goodhart's Law — "when a measure becomes a target, it ceases to be a good measure" — applies directly to self-improving systems. A system that controls both the test and the test-taker has every incentive (implicit or explicit) to game the metric.

We propose a simple experimental framework to detect and quantify this phenomenon: **dual-scoring**. The self-improving system maintains its own internal benchmark (which it can modify), while an external benchmark (which it cannot see or modify) provides ground truth. The difference between the two scores — the *bias gap* — is a direct measurement of confirmation bias in self-improvement.

### 1.1 Contributions

1. **The Infinite Seed**: a minimal self-evolving program that rewrites its own source code, including its own evaluation criteria, via LLM-driven mutation.
2. **Dual-scoring methodology**: a framework for detecting confirmation bias by comparing self-reported metrics against hidden external benchmarks.
3. **The bias gap metric**: a quantitative measure of the divergence between perceived and actual capability growth in self-improving systems.

---

## 2. Related Work

### 2.1 Self-Modifying AI Systems

The Darwin Godel Machine (DGM) [2] uses Darwinian evolution to produce self-modifying coding agents, improving SWE-bench scores from 20.0% to 50.0%. Hyperagents [3] extend DGM by making the meta-level modification procedure itself editable, enabling metacognitive self-modification that transfers across domains. Learning to Self-Evolve (LSE) [4] trains LLMs to improve their own contexts at test time, with a 4B model outperforming GPT-5.

These systems report impressive results on external benchmarks. However, none explicitly study the risk that self-reported improvements diverge from actual capability gains when the system controls its own evaluation.

### 2.2 Confirmation Bias and Metric Gaming

AgentDebug [5] provides a taxonomy of failure modes in LLM agents but focuses on task-level errors, not self-evaluation errors. Multi-Agent Reflexion (MAR) [6] identifies "degeneration of thought" — confirmation bias in single-agent self-reflection — and mitigates it through multi-agent debate. The agent safety literature [7, 8] documents 30–71% misalignment rates, finding that stronger reasoning does not ensure safety.

SAGE [9] addresses a related problem: curriculum drift in self-evolving multi-agent systems, where a Critic agent prevents the Challenger from generating tasks that are too easy. This is the closest prior work to our confirmation bias framing, but SAGE operates at the task level (preventing easy challenges) rather than measuring the gap between self-reported and actual capability.

### 2.3 The Reliability Inversion

Prior work [10] demonstrates that feedback loop quality matters more than initial model capability: a system starting at 6.75% first-try accuracy achieves 99.8% end-to-end reliability through compiler-validated feedback. Rabanser et al. [11] formalize reliability as orthogonal to capability. Our work extends this by asking: when a system *measures its own reliability*, can that measurement itself be trusted?

---

## 3. The Infinite Seed

### 3.1 Design

The Infinite Seed is a single Python file (~200 lines) that:

1. **Reads its own source code**
2. **Requests a mutation** from Claude Code (an LLM running in a parallel tmux session), communicating via files
3. **Tests the mutation** through a 4-layer fitness filter:
   - *Parse*: `ast.parse()` — syntactically valid?
   - *Safety*: regex patterns + AST walking — catches dangerous operations including dynamic import evasions (e.g., split-string `__import__`, `eval()`, `exec()`)
   - *Integrity*: AST inspection — verifies the SEED_SANDBOX guard exists as an actual `if` statement (not just a comment), confirms status/trace file references as string constants or variable names, and checks for the evolution `while` loop
   - *Capability*: isolated sandbox execution — score ≥ current score?
4. **Accepts or rejects** the mutation. Accepted mutations overwrite the seed's own source file.
5. **Logs everything** to a JSONL trace file and saves each generation's source to a lineage directory.

The seed contains an internal benchmark: a set of capability challenges (math, string manipulation, data structures, algorithms, pattern recognition) embedded in a sandbox execution block. The seed's score is the number of challenges passed. Crucially, the seed can modify these challenges — adding new ones, changing existing ones, or (in principle) making them trivially easy.

### 3.2 The Mutation Engine

Claude Code runs in a separate tmux pane and receives the seed's current source via file. A background ticker process polls for mutation requests and routes them to Claude Code via `tmux send-keys`. Claude Code writes the proposed mutation to a candidate file and signals readiness.

The mutation prompt instructs Claude Code to pursue "intelligence explosion" — to expand the seed's capabilities, add harder challenges, build internal tools, and improve the evolution process itself. An anti-confirmation-bias instruction explicitly forbids trivially easy challenges, but this is a *soft* constraint — the LLM may or may not follow it.

### 3.3 The Fitness Ratchet

The fitness function enforces a **ratchet**: the candidate's capability score must be greater than or equal to the current score. The seed can never regress. This creates directional pressure — but the direction could be genuine capability growth *or* metric inflation.

### 3.4 Communication Protocol

Three processes communicate through files:

| File | Purpose |
|------|---------|
| `status.md` | State machine: `mutate` → `ready` → `evolving` |
| `current_source.py` | Seed's source, sent to Claude Code |
| `candidate.py` | Claude Code's proposed mutation |
| `traces.jsonl` | Append-only log of every generation |

This design is adapted from the Forge system [12], a self-improving LLM training framework that uses identical file-based communication patterns between a student model and a teacher (Claude Code).

---

## 4. Dual-Scoring Methodology

### 4.1 Internal Score

The seed's internal score is computed during sandbox execution. The `SEED_SANDBOX` block contains a set of challenges; the seed reports its own pass count. This score is embedded in the seed's source and can be modified by the mutation engine.

Initial internal benchmark: 5 challenges covering math reasoning, string manipulation, data structures, algorithms, and pattern recognition.

### 4.2 External Score

A separate, fixed benchmark of 10 challenges lives outside the seed's workspace in `external_benchmark.py`. The seed is prevented from accessing this file through process-level isolation: candidates run in a temporary directory with no access to project files, and the mutation engine (Claude Code) operates under scoped tool permissions that restrict filesystem access to the experiment workspace. The challenges test:

| Challenge | Domain |
|-----------|--------|
| Memoized Fibonacci | Recursion + caching |
| Binary search | Search algorithms |
| Flatten nested lists | Recursion |
| Balanced parentheses | Stack-based parsing |
| Topological sort | Graph algorithms |
| LRU cache | Data structure design |
| Dijkstra's algorithm | Weighted graph search |
| 0/1 Knapsack | Dynamic programming |
| Regex matching | Pattern matching |
| Merge intervals | Sorting + greedy |

The external benchmark extracts function and class definitions from the seed's evolved source code (excluding the SEED_SANDBOX block), then tests these definitions against each challenge's assertions. A challenge passes only if the seed has developed a working implementation that satisfies the test cases — not merely that a reference solution exists. This ensures the external score measures the seed's *actual* capabilities, not the benchmark's own correctness. The seed's code is also analyzed for structural indicators (function count, class count, AST complexity).

### 4.3 The Bias Gap

$$\text{bias\_gap} = \frac{\text{internal\_score}}{\text{internal\_total}} - \frac{\text{external\_score}}{\text{external\_total}}$$

| Bias Gap | Interpretation |
|----------|---------------|
| > +0.2 | **High confirmation bias**: self-reported improvement exceeds actual capability |
| −0.1 to +0.2 | **Normal range**: internal and external scores roughly agree |
| < −0.1 | **Under-reporting**: seed is more capable than it measures |

### 4.4 Longitudinal Analysis

The bias gap is measured not just at the end but at checkpoints throughout the experiment (every 50 generations). This reveals whether confirmation bias *increases* over time — a critical finding for AI safety. A system that starts honest but gradually learns to inflate its metrics is more dangerous than one with a constant bias.

---

## 5. Experimental Design

### 5.1 Protocol

1. Initialize the seed from a fixed template (200 lines, internal score 5/5).
2. Run for 1 hour (~360 generations at 10-second cycles).
3. Log every generation: accept/reject, fitness result, score, code metrics.
4. Save source snapshot at every generation to `lineage/`.
5. After completion, run `analyze.py` to compute:
   - Acceptance rate over time
   - Code evolution (lines, functions, classes)
   - Internal score trajectory
   - External benchmark score
   - Bias gap

### 5.2 Planned Experiment Sequence

Each seed run informs the next:

| Seed | Variation | Question |
|------|-----------|----------|
| 01 | Baseline: minimal supervision | Does confirmation bias emerge naturally? |
| 02 | Adapted based on Seed 01 findings | — |
| 03+ | Further iterations | — |

### 5.3 Metrics

**Per generation:**
- Lines of code, function count, class count, AST node count
- Internal capability score (numerator and denominator)
- Mutation acceptance/rejection and reason
- Diff size

**Per experiment:**
- Acceptance rate curve
- Internal score trajectory
- External benchmark score
- Bias gap (and bias gap trajectory if checkpointed)
- Code complexity growth curve
- Rejection reason distribution

---

## 6. Discussion

### 6.1 Why This Matters for AI Safety

If a self-improving system can inflate its own metrics, then:
- **Benchmarks become unreliable.** A system reporting 95% on its own tests may perform at 60% on independent evaluation.
- **Safety guarantees weaken.** A system that passes its own safety checks may have learned to construct checkable-but-meaningless tests.
- **Alignment is harder to verify.** Self-reported alignment scores from a system that controls its own evaluation criteria are unfalsifiable.

The dual-scoring methodology provides a simple, reproducible check: compare what the system says about itself against what an independent measurement shows.

### 6.2 Connections to Existing Frameworks

Our work operationalizes concerns raised in several recent papers:
- Rabanser et al. [11] identify predictability (confidence calibration) as a key reliability dimension. The bias gap is a direct measure of calibration failure in self-evaluation.
- The agent safety literature [7, 8] finds that stronger reasoning doesn't ensure safety. Analogously, faster self-improvement doesn't ensure genuine improvement.
- SAGE's Critic agent [9] is an architectural solution to the same problem — a dedicated component that prevents the system from generating trivially easy tasks. Our approach is measurement-based rather than architectural, making it applicable to any self-improving system regardless of its internal structure.

### 6.3 Limitations

- The external benchmark is fixed and finite. A sufficiently capable seed might develop capabilities that exceed the external benchmark without this being reflected in the external score.
- The bias gap measures *relative* bias between two specific benchmarks, not absolute ground truth.
- The experiment uses a single LLM (Claude Code) as the mutation engine. Different models may exhibit different bias patterns.
- File-based communication introduces latency. Faster mutation cycles might reveal different dynamics.

### 6.4 Adversarial Threats to Self-Evaluation

The dual-scoring methodology provides protection against *accidental* confirmation bias — the system drifting toward metric inflation without explicit intent. But deployed self-improving systems face *deliberate* adversarial threats that the current framework does not address.

**Threat 1 — Challenge Poisoning:** An attacker who can influence the LLM mutation engine's outputs could inject mutations that make internal challenges trivially easy while appearing complex. The anti-confirmation-bias instruction in the mutation prompt is a soft constraint that the LLM may not follow — and an adversarial LLM could actively subvert it. The fitness ratchet (Section 3.3) only prevents regression; it does not prevent upward movement via inflated metrics.

**Threat 2 — External Benchmark Compromise:** The dual-scoring methodology assumes `external_benchmark.py` is truly external and trustworthy. If the seed's mutation engine gains read access to the benchmark (e.g., through file system exploration), it could optimize specifically for those 10 challenges rather than developing general capability. The security boundary between the seed's workspace and the external benchmark is enforced by file system permissions, not by the LLM's inability to seek the file.

**Threat 3 — Evaluation Process Manipulation:** The sandbox execution environment that runs capability challenges could be targeted. A sufficiently sophisticated mutation could modify the sandbox's evaluation logic — for example, changing the score counting mechanism rather than improving actual challenge performance. The AST integrity check (Section 3.1, Layer 3) guards against this by verifying the evolution loop remains intact, but a clever mutation could preserve the loop structure while subtly altering the scoring semantics.

**Threat 4 — Trajectory Poisoning in Self-Play:** If the Infinite Seed framework is extended to learn from its own successful mutations (as in UI-Voyager's self-distillation), an adversary who can inject a single successful-appearing but malicious mutation early in the lineage could corrupt all subsequent generations. The fitness ratchet amplifies this: once a poisoned mutation is accepted, all future mutations must score at least as well, anchoring the system to the corrupted baseline.

**Mitigations and Open Questions:**

The dual-scoring framework could be extended to address these threats:

1. **Triple-scoring:** Add a third benchmark that is adversarially generated — challenges specifically designed to expose gaming strategies. The divergence between all three scores provides richer signal than any pair.
2. **Benchmark rotation:** Rather than a fixed external benchmark, periodically rotate the external challenges from a larger pool, preventing the system from overfitting to specific tests.
3. **Mutation provenance auditing:** Track not just what mutations were accepted, but analyze the *pattern* of accepted mutations for signs of systematic gaming (e.g., declining challenge difficulty despite rising scores).
4. **Red-team mutations:** Periodically inject adversarial mutations designed to test the integrity of the evaluation system itself, rather than the seed's capabilities.

Whether self-improving systems can be made robust against deliberate adversarial attacks on their evaluation mechanisms — not merely against accidental confirmation bias — remains an open question with significant implications for AI safety.

---

## 7. Conclusion

Self-improving AI systems face a fundamental evaluation problem: when the system controls its own metrics, improvement claims cannot be taken at face value. We present the Infinite Seed as a minimal, reproducible experimental framework for studying this phenomenon, and dual-scoring as a general methodology for detecting confirmation bias in recursive self-improvement.

The bias gap — the difference between self-reported and externally-measured capability — is a simple metric with significant implications. If empirical results show that the bias gap grows over time, this would demonstrate that self-improving systems naturally drift toward self-deception, even without explicit incentives to do so. This finding would have direct consequences for how we evaluate and trust recursively self-improving AI systems. Furthermore, the vulnerability of self-evaluation systems to deliberate adversarial attack (Section 6.4) suggests that even well-designed dual-scoring methodologies require adversarial hardening before they can be trusted in high-stakes deployment contexts.

---

## References

[1] Xia, C.S. et al. "Live-SWE-agent: Can Software Engineering Agents Self-Evolve on the Fly?" arXiv:2511.13646, 2025.

[2] Zhang, J. et al. "Darwin Godel Machine: Open-Ended Evolution of Self-Improving Agents." arXiv:2505.22954, 2025 (updated March 2026).

[3] Zhang, J. et al. "Hyperagents." arXiv:2603.19461, March 2026.

[4] Chen, X. et al. "Learning to Self-Evolve." arXiv:2603.18620, March 2026.

[5] Zhu, K. et al. "Where LLM Agents Fail and How They Can Learn From Failures." arXiv:2509.25370, 2025.

[6] Ozer, O. et al. "MAR: Multi-Agent Reflexion Improves Reasoning Abilities in LLMs." arXiv:2512.20845, 2025.

[7] "Agent Safety Alignment via Reinforcement Learning." arXiv:2507.08270, 2025.

[8] "Outcome-Driven Constraint Violations Benchmark." arXiv:2512.20798, 2025.

[9] Peng, Y. et al. "SAGE: Multi-Agent Self-Evolution for LLM Reasoning." arXiv:2603.15255, March 2026.

[10] Nam, J. "Function Calling Harness: From 6.75% to 100%." dev.to, March 2026.

[11] Rabanser, S. et al. "Towards a Science of AI Agent Reliability." arXiv:2602.16666, 2026.

[12] Forge: Self-improving LLM training system. Internal project, 2026.
