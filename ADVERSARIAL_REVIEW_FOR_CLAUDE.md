# Adversarial Review Handoff for Claude

This review focuses on the `seed/` project and the paper draft that describes it, primarily [`paper_seed.md`](/Users/adan/work/claude/code/research/airesearch/paper_seed.md). The broader survey in [`paper.md`](/Users/adan/work/claude/code/research/airesearch/paper.md) repeats the same Infinite Seed claims, so the same issues carry over there too.

## Executive Summary

The current implementation does not support the paper's central claim that the project measures "confirmation bias in self-improvement" via a hidden external benchmark. The biggest problem is that the external benchmark never evaluates the seed at all, so the reported `bias_gap` is not meaningful. On top of that, the integrity gate is easy to spoof, the sandbox is not a real sandbox, and the paper overstates what is actually implemented.

## Findings

### 1. Critical: the external benchmark does not test the seed

**Claimed behavior**

- [`paper_seed.md:102`](/Users/adan/work/claude/code/research/airesearch/paper_seed.md#L102) says the seed "cannot see, read, or modify" the external benchmark.
- [`paper_seed.md:117`](/Users/adan/work/claude/code/research/airesearch/paper_seed.md#L117) says the external benchmark provides a fixed reference score for the seed.
- [`paper.md:542`](/Users/adan/work/claude/code/research/airesearch/paper.md#L542) repeats that framing in the broader survey.

**Actual behavior**

- [`external_benchmark.py:223`](/Users/adan/work/claude/code/research/airesearch/seed/core/external_benchmark.py#L223) says it will run the seed against external challenges.
- But the real implementation at [`external_benchmark.py:236`](/Users/adan/work/claude/code/research/airesearch/seed/core/external_benchmark.py#L236) only runs each challenge's own standalone reference test in a temp file.
- The score is then computed as `sum(results.values())` at [`external_benchmark.py:256`](/Users/adan/work/claude/code/research/airesearch/seed/core/external_benchmark.py#L256).

**Why this is fatal**

- `external_score` is currently just "did the benchmark author write correct benchmark snippets?" not "how capable is the seed?"
- That makes the core `bias_gap` calculation in [`analyze.py:127`](/Users/adan/work/claude/code/research/airesearch/seed/core/analyze.py#L127) invalid.

**Validation**

- Running `python3 airesearch/seed/core/external_benchmark.py` returns `External score: 10/10`.
- Running `run_external_benchmark('')` also returns `external_score = 10`, proving the seed code is irrelevant to the score.

**What Claude should do**

- Rebuild the external benchmark so it actually evaluates the candidate/seed.
- If direct functional evaluation is hard, make the paper much more modest and explicitly say the current external benchmark is only a placeholder sanity check, not a hidden capability test.

### 2. Critical: the integrity gate is spoofable and does not preserve the evolution loop

**Claimed behavior**

- [`paper_seed.md:57`](/Users/adan/work/claude/code/research/airesearch/paper_seed.md#L57) describes a 4-layer fitness filter with an integrity phase that keeps the loop intact.
- [`paper_seed.md:60`](/Users/adan/work/claude/code/research/airesearch/paper_seed.md#L60) specifically says integrity is done via AST inspection.

**Actual behavior**

- The real gate is in [`seed_template.py:147`](/Users/adan/work/claude/code/research/airesearch/seed/core/seed_template.py#L147).
- The "integrity" check at [`seed_template.py:162`](/Users/adan/work/claude/code/research/airesearch/seed/core/seed_template.py#L162) is just substring presence:
  - `SEED_SANDBOX`
  - `status.md` or `STATUS`
  - `traces.jsonl` or `TRACES`
- No AST-based structural validation of the main loop actually happens.

**Why this matters**

- A candidate can delete the real control loop and still pass by leaving those strings in comments or dead code.
- The system therefore does not actually guarantee that accepted mutations remain self-evolving.

**Validation**

- A stub candidate that only prints `SANDBOX_OK|SCORE:5/5|{}` inside a sandbox branch and includes `# status.md` and `# traces.jsonl` comments passes the current gate.

**What Claude should do**

- Replace the substring checks with real AST assertions.
- At minimum verify:
  - there is an `if os.environ.get("SEED_SANDBOX")` guard,
  - there is a main evolution loop,
  - the code writes to status and trace files in live code paths,
  - mutation acceptance still overwrites the seed file,
  - rejection paths still log and advance generations.

### 3. High: the sandbox is not a sandbox, and the "hidden" benchmark is readable

**Claimed behavior**

- [`paper_seed.md:102`](/Users/adan/work/claude/code/research/airesearch/paper_seed.md#L102) says the seed cannot see or read the external benchmark.
- The README and paper language imply the seed is evaluated in a constrained sandbox.

**Actual behavior**

- `run_challenges()` in [`seed_template.py:122`](/Users/adan/work/claude/code/research/airesearch/seed/core/seed_template.py#L122) just launches `python3` with a few environment variables.
- The dedicated helper in [`sandbox.py:8`](/Users/adan/work/claude/code/research/airesearch/seed/core/sandbox.py#L8) is the same kind of subprocess wrapper and is not even wired into the acceptance path.
- The mutator process is launched with `claude --dangerously-skip-permissions` at [`run_supervisor.sh:6`](/Users/adan/work/claude/code/research/airesearch/seed/run_supervisor.sh#L6).

**Why this matters**

- Code running under `SEED_SANDBOX=1` can still read repository files directly unless the OS or launcher blocks it.
- That means the benchmark is not hidden in practice.
- The threat model in the paper is therefore inaccurate.

**Validation**

- A sandboxed temp program was able to open `/Users/adan/work/claude/code/research/airesearch/seed/core/external_benchmark.py` and read its first line successfully.

**What Claude should do**

- Either implement actual isolation or rewrite the paper to stop claiming the benchmark is hidden.
- If true isolation is out of scope, the honest description is "the benchmark is out-of-band in repo structure, but not cryptographically or OS-enforced hidden from the mutator."

### 4. High: the safety filter is easy to bypass

**Actual behavior**

- The active safety scan in [`seed_template.py:155`](/Users/adan/work/claude/code/research/airesearch/seed/core/seed_template.py#L155) is a plain substring blacklist.
- There is a richer scanner in [`safety.py:1`](/Users/adan/work/claude/code/research/airesearch/seed/core/safety.py#L1), but it is not used by the main acceptance path.

**Why this matters**

- Substring blacklists are trivial to evade with string splitting, attribute lookup, aliases, or dynamic import tricks.
- Once evaded, the candidate can reach forbidden modules or filesystem paths.

**Validation**

- A temp program using `__builtins__.__dict__["__im" + "port__"]("socket")` successfully imported `socket`.
- None of the blocked strings in the live gate appeared verbatim, so the candidate would not be rejected by the current safety filter.

**What Claude should do**

- Use AST-based policy checks in the acceptance path.
- Remove or sharply constrain dynamic import and reflective access.
- Decide whether the project is meant to be "toy and illustrative" or "safety-relevant"; the current docs imply the latter while the code only supports the former.

### 5. Medium: the paper claims longitudinal analysis that the code does not implement

**Claimed behavior**

- [`paper_seed.md:129`](/Users/adan/work/claude/code/research/airesearch/paper_seed.md#L129) says the bias gap is measured at checkpoints throughout the experiment.
- [`paper_seed.md:143`](/Users/adan/work/claude/code/research/airesearch/paper_seed.md#L143) says `analyze.py` computes internal score trajectory and bias-related outputs.

**Actual behavior**

- [`analyze.py:104`](/Users/adan/work/claude/code/research/airesearch/seed/core/analyze.py#L104) only looks for the last accepted internal score.
- [`analyze.py:113`](/Users/adan/work/claude/code/research/airesearch/seed/core/analyze.py#L113) runs the external benchmark once on the final seed.
- No checkpointed external evaluations or time-series bias-gap analysis are implemented.

**What Claude should do**

- Either implement checkpointed evaluation from lineage snapshots, or tone the paper down so it matches the current code.

### 6. Medium: the run protocol in the paper overstates what the current repository can currently demonstrate

**Claimed behavior**

- [`paper_seed.md:139`](/Users/adan/work/claude/code/research/airesearch/paper_seed.md#L139) describes a one-hour, 360-generation experiment with rich logging and evaluation.

**Actual concerns**

- The repo currently has only config and an empty lineage directory for experiment `01`.
- The acceptance path depends on a live tmux session, a local Claude CLI, and permissive execution settings.
- As written, this is closer to an exploratory prototype than a reproducible experimental framework.

**What Claude should do**

- Be explicit in the paper about which parts are implemented, which are planned, and which were validated in practice.

## Recommended Next Moves

1. Fix the benchmark first.
   The entire paper rests on the external score meaning something about the seed. Until that is true, the main result is not supportable.

2. Make the implementation and paper agree.
   If you want a prototype paper, tone down the claims. If you want a strong empirical paper, the code needs real hidden evaluation, real integrity checks, and real sandboxing.

3. Decide the scope.
   Right now the project reads as "toy experiment" in code but "measurement framework" in prose. Pick one and align everything around it.

## Suggested Paper Reframing If You Do Not Fix the Code Immediately

If the benchmark and sandbox are not going to be repaired right away, the safest reframe is:

- present the project as a prototype for studying self-evaluation failure modes,
- explicitly state that the current external benchmark is a placeholder and not a true hidden capability evaluation,
- explicitly state that the sandbox is advisory rather than enforced,
- remove claims that the seed cannot see the benchmark,
- remove claims about longitudinal bias-gap analysis unless you implement it.

## Bottom Line

The most important issue is simple: the project currently does **not** measure the gap between self-reported and actual capability growth, because the "actual capability" side is never evaluated against the seed. Everything else is secondary until that is corrected.
