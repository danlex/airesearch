#!/bin/bash
# Initialize a new experiment directory
set -e
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
EXPERIMENT="${1:-01}"
WORKSPACE="$SCRIPT_DIR/experiments/$EXPERIMENT"

mkdir -p "$WORKSPACE/lineage"

if [ ! -f "$WORKSPACE/seed.py" ]; then
    echo "Copying seed template to $WORKSPACE/seed.py"
    cp "$SCRIPT_DIR/core/seed_template.py" "$WORKSPACE/seed.py"
fi

if [ ! -f "$WORKSPACE/config.json" ]; then
    cat > "$WORKSPACE/config.json" << EOF
{
  "experiment_id": "$EXPERIMENT",
  "name": "Experiment $EXPERIMENT",
  "max_generations": 360,
  "cycle_delay_seconds": 10,
  "sandbox_timeout_seconds": 30
}
EOF
fi

echo "Experiment $EXPERIMENT ready at $WORKSPACE"
echo "Run with: ./run.sh $EXPERIMENT"
