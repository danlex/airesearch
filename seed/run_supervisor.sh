#!/bin/bash
# Launches Claude Code as the mutation engine with scoped permissions.
# The mutator can only read/write within the experiment workspace —
# it CANNOT access external_benchmark.py or files outside the workspace.
cd "$(dirname "$0")"
while true; do
    echo "=== Claude Code supervisor starting ==="
    claude --allowedTools 'Read,Write,Edit,Bash(python3 *)' \
           --permission-prompt-tool Bash
    echo "[$(date)] Claude Code exited — restarting in 5s..."
    sleep 5
done
