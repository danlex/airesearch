#!/bin/bash
# Launch the Infinite Seed experiment
set -e

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
EXPERIMENT="${1:-01}"
WORKSPACE="$SCRIPT_DIR/experiments/$EXPERIMENT"
SESSION="seed"

if [ ! -d "$WORKSPACE" ]; then
    echo "Experiment $EXPERIMENT not found"
    exit 1
fi

# Copy seed template if seed.py doesn't exist yet
if [ ! -f "$WORKSPACE/seed.py" ]; then
    echo "Initializing seed from template..."
    cp "$SCRIPT_DIR/core/seed_template.py" "$WORKSPACE/seed.py"
    mkdir -p "$WORKSPACE/lineage"
fi

# Kill old session if exists
tmux kill-session -t "$SESSION" 2>/dev/null || true
sleep 1

echo "=== The Infinite Seed: Experiment $EXPERIMENT ==="

# Create tmux session with 3 panes:
#   Pane 0 (left):  Claude Code (mutator/supervisor)
#   Pane 1 (right-top): Seed process
#   Pane 2 (right-bottom): Monitor / logs

tmux new-session -d -s "$SESSION" -n main

# Pane 0: Claude Code supervisor
tmux send-keys -t "$SESSION:0.0" "cd $SCRIPT_DIR && bash run_supervisor.sh" Enter

# Split right pane (60% for seed)
tmux split-window -h -p 60 -t "$SESSION:0.0"

# Pane 1: Seed process
tmux send-keys -t "$SESSION:0.1" "cd $WORKSPACE && source $SCRIPT_DIR/.venv/bin/activate && python3 seed.py" Enter

# Split pane 1 vertically for monitor
tmux split-window -v -p 30 -t "$SESSION:0.1"

# Pane 2: Live log tail
tmux send-keys -t "$SESSION:0.2" "cd $WORKSPACE && tail -f traces.jsonl 2>/dev/null || echo 'Waiting for traces...'" Enter

sleep 2

# Start ticker in background
echo "[run.sh] Starting ticker..."
nohup bash "$SCRIPT_DIR/ticker.sh" "$EXPERIMENT" > "$WORKSPACE/ticker.log" 2>&1 &
TICKER_PID=$!
echo "$TICKER_PID" > "$WORKSPACE/ticker.pid"
echo "[run.sh] Ticker PID: $TICKER_PID"

echo "[run.sh] Attaching to tmux session '$SESSION'..."
echo "[run.sh] Pane 0: Claude Code | Pane 1: Seed | Pane 2: Logs"
echo ""

tmux attach -t "$SESSION"
