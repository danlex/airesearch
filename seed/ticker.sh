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
            tmux send-keys -t "$TEACHER_PANE" "Read $WORKSPACE/current_source.py — this is generation $GENERATION of a self-evolving program pursuing intelligence explosion. Its goal: expand its capability score by adding new challenges AND solving them. Read the SEED_SANDBOX block to see current challenges. ADD new ones (math, algorithms, data structures, recursion, search, optimization — anything). The score denominator must grow. Write the complete improved Python source to $WORKSPACE/candidate.py. KEEP: SEED_SANDBOX guard, status.md communication, traces.jsonl logging, evolution loop. NO: os.system, subprocess.Popen, socket, requests, shutil.rmtree, network calls. Then write 'ready' to $WORKSPACE/status.md" Enter

            # Wait for Claude Code to finish (max 180 seconds)
            WAITED=0
            while [ $WAITED -lt 180 ]; do
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
