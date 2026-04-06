# The Infinite Seed

A self-evolving Python program that rewrites its own source code, using Claude Code as the brain. Measures confirmation bias in self-improvement.

## Quick Start

```bash
cd seed

# Set up a new experiment
./setup_experiment.sh 01

# Launch (creates tmux session)
./run.sh 01
```

This creates a tmux session with 3 panes:
- **Left**: Claude Code (mutator)
- **Top-right**: Seed process
- **Bottom-right**: Live trace log

A background ticker bridges seed <-> Claude Code via files.

## Prerequisites

- Python 3.10+
- `tmux`
- `claude` CLI installed and authenticated (with scoped permissions -- see note below)

## Setup

```bash
# Initialize experiment directory (copies seed template, creates config)
./setup_experiment.sh 01
```

This copies `core/seed_template.py` to `experiments/01/seed.py` and creates a default `config.json` if one doesn't exist.

## How It Works

1. Seed writes its source to `current_source.py`, sets `status.md` = `"mutate"`
2. Ticker detects, sends prompt to Claude Code via `tmux send-keys`
3. Claude Code writes improved version to `candidate.py`, sets `status.md` = `"ready"`
4. Seed tests candidate through a **4-layer fitness check**:
   - **Parse**: candidate must be valid Python (AST parse)
   - **Safety**: regex + AST scan for forbidden calls (`os.system`, `subprocess.Popen`, `socket`, `requests`, `shutil.rmtree`, `eval`, `exec`, `__import__`)
   - **Integrity**: AST verification that core structures are preserved (`SEED_SANDBOX` guard, `status.md` reference, `traces.jsonl` reference, evolution loop)
   - **Capability**: sandbox execution scores challenges; score must not regress
5. Accept or reject. Repeat.

## Tests

```bash
source .venv/bin/activate
python -m pytest tests/ -v
```

## Analysis

```bash
# Analyze results from an experiment run
python3 core/analyze.py experiments/01

# Run external benchmark (confirmation bias check)
python3 core/external_benchmark.py experiments/01/seed.py
```

## Scoped Permissions

Previous versions used `--dangerously-skip-permissions` to run Claude Code unattended. This is no longer needed. Instead, configure scoped permissions in Claude Code so the mutator session can read/write only within the experiment workspace. This limits blast radius without disabling the permission system entirely.

## Stop

```bash
tmux kill-session -t seed
kill $(cat experiments/01/ticker.pid)
```

## File Layout

```
seed/
├── core/
│   ├── __init__.py           # Package marker
│   ├── seed_template.py      # Template copied into experiments
│   ├── analyze.py            # Post-run analysis
│   └── external_benchmark.py # Confirmation bias check
├── experiments/
│   └── 01/
│       ├── config.json       # Experiment configuration
│       ├── seed.py           # The evolving code (gitignored)
│       ├── status.md         # State: mutate / ready / evolving
│       ├── current_source.py # Source sent to Claude Code
│       ├── candidate.py      # Mutation from Claude Code
│       ├── traces.jsonl      # Every generation logged (gitignored)
│       ├── lineage/          # gen_0000.py, gen_0001.py, ... (gitignored)
│       └── ticker.pid        # Ticker process ID
├── tests/                    # Test suite
├── run.sh                    # Launch experiment in tmux
├── ticker.sh                 # Heartbeat: routes mutations to Claude Code
├── setup_experiment.sh       # Initialize a new experiment directory
└── .gitignore                # Excludes run artifacts and data
```
