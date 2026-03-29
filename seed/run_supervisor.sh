#!/bin/bash
# Launches Claude Code in a loop (restarts on exit, like forge)
cd "$(dirname "$0")"
while true; do
    echo "=== Claude Code supervisor starting ==="
    claude --dangerously-skip-permissions
    echo "[$(date)] Claude Code exited — restarting in 5s..."
    sleep 5
done
