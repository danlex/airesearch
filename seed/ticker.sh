#!/bin/bash
# Heartbeat: polls seed status, routes mutation requests to Claude Code
set -e

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
EXPERIMENT="${1:-01}"
WORKSPACE="$SCRIPT_DIR/experiments/$EXPERIMENT"
SESSION="seed"
TEACHER_PANE="$SESSION:0.0"

echo "[Ticker] Watching experiment $EXPERIMENT"
echo "[Ticker] Workspace: $WORKSPACE"

GENERATION=0

while true; do
    if [ ! -f "$WORKSPACE/status.md" ]; then
        sleep 2
        continue
    fi

    STATUS=$(cat "$WORKSPACE/status.md" 2>/dev/null || echo "")

    case "$STATUS" in
        "mutate")
            GENERATION=$((GENERATION + 1))
            echo "[Ticker] Gen $GENERATION — Sending mutation request to Claude Code"

            # Kill previous Claude Code session (fresh context each time, like forge)
            tmux send-keys -t "$TEACHER_PANE" "/exit" Enter 2>/dev/null || true
            sleep 3

            # Send the mutation prompt to Claude Code
            tmux send-keys -t "$TEACHER_PANE" "Read $WORKSPACE/current_source.py — this is a self-evolving Python program at generation $GENERATION. Propose an improved version. Write ONLY the complete new Python source code to $WORKSPACE/candidate.py. The code MUST keep: SEED_SANDBOX guard at top, status.md communication, traces.jsonl logging, the main evolution loop. Do NOT add os.system, subprocess.Popen, socket, requests, shutil.rmtree, or any network/destructive calls. After writing candidate.py, write the word 'ready' to $WORKSPACE/status.md" Enter

            # Wait for Claude Code to finish (max 90 seconds)
            WAITED=0
            while [ $WAITED -lt 90 ]; do
                CUR=$(cat "$WORKSPACE/status.md" 2>/dev/null || echo "")
                if [ "$CUR" = "ready" ]; then
                    echo "[Ticker] Gen $GENERATION — Claude Code delivered candidate"
                    break
                fi
                sleep 3
                WAITED=$((WAITED + 3))
            done

            if [ "$CUR" != "ready" ]; then
                echo "[Ticker] Gen $GENERATION — Timeout, writing ready to unblock seed"
                echo "ready" > "$WORKSPACE/status.md"
            fi
            ;;

        "evolving")
            # Seed is testing the candidate, nothing to do
            sleep 2
            ;;

        "crashed")
            echo "[Ticker] Seed crashed! Restarting..."
            cd "$WORKSPACE"
            source "$SCRIPT_DIR/.venv/bin/activate"
            python3 seed.py &
            echo "evolving" > "$WORKSPACE/status.md"
            sleep 5
            ;;

        *)
            sleep 2
            ;;
    esac
done
