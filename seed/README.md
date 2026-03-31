# The Infinite Seed

A self-evolving Python program that rewrites its own source code, using Claude Code as the brain. Measures confirmation bias in self-improvement.

## Quick Start

```bash
cd seed
./run.sh 01
```

This creates a tmux session with 3 panes:
- **Left**: Claude Code (mutator)
- **Top-right**: Seed process
- **Bottom-right**: Live trace log

A background ticker bridges seed ↔ Claude Code via files.

## Prerequisites

- Python 3.10+
- `tmux`
- `claude` CLI installed and authenticated

## How It Works

1. Seed writes its source to `current_source.py`, sets `status.md` = `"mutate"`
2. Ticker detects, sends prompt to Claude Code via `tmux send-keys`
3. Claude Code writes improved version to `candidate.py`, sets `status.md` = `"ready"`
4. Seed tests candidate (parse → safety → integrity → sandbox → score regression)
5. Accept or reject. Repeat.

## After the Experiment

```bash
# Analyze results
python3 core/analyze.py experiments/01

# Run external benchmark (confirmation bias check)
python3 core/external_benchmark.py experiments/01/seed.py
```

## Stop

```bash
tmux kill-session -t seed
kill $(cat experiments/01/ticker.pid)
```

## File Layout

```
experiments/01/
├── seed.py           # The evolving code
├── status.md         # State: mutate / ready / evolving
├── current_source.py # Source sent to Claude Code
├── candidate.py      # Mutation from Claude Code
├── traces.jsonl      # Every generation logged
├── lineage/          # gen_0000.py, gen_0001.py, ...
└── ticker.pid        # Ticker process ID
```
