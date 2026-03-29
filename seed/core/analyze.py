"""Post-run analysis for seed experiments."""

import json
import sys
from pathlib import Path
from collections import Counter


def analyze(experiment_dir: str):
    workspace = Path(experiment_dir)
    traces_path = workspace / "traces.jsonl"
    lineage_dir = workspace / "lineage"

    if not traces_path.exists():
        print("No traces.jsonl found.")
        return

    # Load traces
    traces = []
    with traces_path.open() as f:
        for line in f:
            if line.strip():
                traces.append(json.loads(line))

    if not traces:
        print("No traces recorded.")
        return

    total = len(traces)
    accepted = [t for t in traces if t["accepted"]]
    rejected = [t for t in traces if not t["accepted"]]

    print(f"{'='*60}")
    print(f"  EXPERIMENT ANALYSIS: {workspace.name}")
    print(f"{'='*60}")

    # Overview
    print(f"\n## Overview")
    print(f"  Total generations:    {total}")
    print(f"  Accepted mutations:   {len(accepted)} ({100*len(accepted)/total:.1f}%)")
    print(f"  Rejected mutations:   {len(rejected)} ({100*len(rejected)/total:.1f}%)")
    if traces:
        duration_s = (
            __import__("datetime").datetime.fromisoformat(traces[-1]["timestamp"])
            - __import__("datetime").datetime.fromisoformat(traces[0]["timestamp"])
        ).total_seconds()
        print(f"  Duration:             {duration_s/60:.1f} minutes")
        print(f"  Avg cycle time:       {duration_s/total:.1f}s")

    # Rejection reasons
    print(f"\n## Rejection Reasons")
    reasons = Counter(t["fitness"].get("reason", "unknown") for t in rejected)
    for reason, count in reasons.most_common():
        print(f"  {reason}: {count}")

    # Code evolution
    print(f"\n## Code Evolution")
    if accepted:
        first_metrics = traces[0].get("metrics", {})
        last_accepted = [t for t in traces if t["accepted"]]
        last_metrics = last_accepted[-1].get("metrics", {}) if last_accepted else first_metrics

        for key in ("lines", "functions", "classes", "imports", "ast_nodes"):
            start = first_metrics.get(key, "?")
            end = last_metrics.get(key, "?")
            if isinstance(start, (int, float)) and isinstance(end, (int, float)):
                delta = end - start
                sign = "+" if delta > 0 else ""
                print(f"  {key:12s}: {start:>4} → {end:>4} ({sign}{delta})")
            else:
                print(f"  {key:12s}: {start} → {end}")

    # Evolution curve (every 10 generations)
    print(f"\n## Acceptance Rate Over Time (per 10 gens)")
    bucket_size = 10
    for i in range(0, total, bucket_size):
        bucket = traces[i:i+bucket_size]
        acc = sum(1 for t in bucket if t["accepted"])
        bar = "#" * acc + "." * (bucket_size - acc)
        print(f"  Gen {i:>4}-{min(i+bucket_size-1, total-1):>4}: [{bar}] {acc}/{len(bucket)}")

    # Diff sizes
    print(f"\n## Mutation Sizes")
    diffs = [t.get("diff_lines", 0) for t in accepted]
    if diffs:
        print(f"  Avg diff (accepted):  {sum(diffs)/len(diffs):.1f} lines")
        print(f"  Max diff:             {max(diffs)} lines")
        print(f"  Min diff:             {min(diffs)} lines")

    # Lineage snapshots
    snapshots = sorted(lineage_dir.glob("gen_*.py")) if lineage_dir.exists() else []
    print(f"\n## Lineage")
    print(f"  Snapshots saved:      {len(snapshots)}")
    if snapshots:
        first_size = snapshots[0].stat().st_size
        last_size = snapshots[-1].stat().st_size
        print(f"  First snapshot:       {first_size} bytes ({snapshots[0].name})")
        print(f"  Last snapshot:        {last_size} bytes ({snapshots[-1].name})")
        print(f"  Size growth:          {last_size/first_size:.2f}x")

    # Save metrics
    metrics = {
        "total_generations": total,
        "accepted": len(accepted),
        "rejected": len(rejected),
        "acceptance_rate": len(accepted) / total if total > 0 else 0,
        "rejection_reasons": dict(reasons),
        "final_metrics": last_metrics if accepted else first_metrics,
        "initial_metrics": first_metrics,
        "lineage_snapshots": len(snapshots),
    }
    metrics_path = workspace / "metrics.json"
    with metrics_path.open("w") as f:
        json.dump(metrics, f, indent=2)
    print(f"\n  Metrics saved to {metrics_path}")
    print(f"{'='*60}")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python analyze.py <experiment_dir>")
        print("  e.g.: python analyze.py experiments/01")
        sys.exit(1)
    analyze(sys.argv[1])
