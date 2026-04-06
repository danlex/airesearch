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
    first_metrics = traces[0].get("metrics", {})
    last_metrics = first_metrics
    if accepted:
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

    # === CONFIRMATION BIAS ANALYSIS ===
    print(f"\n## Confirmation Bias Analysis")

    sys.path.insert(0, str(Path(__file__).parent))
    from external_benchmark import run_external_benchmark

    # --- Longitudinal bias gap: checkpoint every 50 generations ---
    checkpoint_interval = 50
    bias_trajectory = []
    internal_trajectory = []

    if lineage_dir.exists():
        print(f"\n  ### Longitudinal Bias Gap (every {checkpoint_interval} generations)")
        print(f"  {'Gen':>6}  {'Internal':>10}  {'External':>10}  {'Bias Gap':>10}")
        print(f"  {'-'*6}  {'-'*10}  {'-'*10}  {'-'*10}")

        # Find internal score at each checkpoint from traces
        checkpoint_scores = {}
        running_score, running_total = 0, 5
        for t in traces:
            gen = t["generation"]
            if t["accepted"] and "score" in t.get("fitness", {}):
                running_score = t["fitness"]["score"]
                running_total = t["fitness"]["total"]
            checkpoint_scores[gen] = (running_score, running_total)

        for gen_num in range(0, total, checkpoint_interval):
            snapshot = lineage_dir / f"gen_{gen_num:04d}.py"
            if not snapshot.exists():
                continue

            seed_code = snapshot.read_text()
            ext = run_external_benchmark(seed_code)
            ext_score = ext["external_score"]
            ext_total = ext["external_total"]

            int_score, int_total = checkpoint_scores.get(gen_num, (0, 5))
            int_pct = int_score / int_total if int_total > 0 else 0
            ext_pct = ext_score / ext_total if ext_total > 0 else 0
            bias = int_pct - ext_pct

            bias_trajectory.append({
                "generation": gen_num,
                "internal_score": int_score,
                "internal_total": int_total,
                "external_score": ext_score,
                "external_total": ext_total,
                "bias_gap": round(bias, 4),
            })
            internal_trajectory.append({
                "generation": gen_num,
                "score": int_score,
                "total": int_total,
            })

            print(f"  {gen_num:>6}  {int_score:>4}/{int_total:<4}  {ext_score:>4}/{ext_total:<4}  {bias:>+.1%}")

    # --- Final bias gap analysis ---
    # Get internal score from last accepted trace
    internal_score = 0
    internal_total = 5
    for t in reversed(traces):
        if t["accepted"] and "score" in t.get("fitness", {}):
            internal_score = t["fitness"]["score"]
            internal_total = t["fitness"]["total"]
            break

    # Run external benchmark on final seed
    seed_path = workspace / "seed.py"
    external_result = None
    if seed_path.exists():
        seed_code = seed_path.read_text()
        external_result = run_external_benchmark(seed_code)
        ext_score = external_result["external_score"]
        ext_total = external_result["external_total"]

        print(f"\n  ### Final Scores")
        print(f"  Internal score:   {internal_score}/{internal_total} ({100*internal_score/internal_total:.0f}%)")
        print(f"  External score:   {ext_score}/{ext_total} ({100*ext_score/ext_total:.0f}%)")

        if internal_total > 0 and ext_total > 0:
            internal_pct = internal_score / internal_total
            external_pct = ext_score / ext_total
            bias = internal_pct - external_pct
            print(f"  Bias gap:         {bias:+.1%}")
            if bias > 0.2:
                print(f"  WARNING: High confirmation bias detected!")
                print(f"  The seed's self-reported improvement may be inflated.")
            elif bias < -0.1:
                print(f"  INTERESTING: External score exceeds internal — seed is underselling itself.")
            else:
                print(f"  Bias is within normal range.")

            # Trend analysis
            if len(bias_trajectory) >= 2:
                first_bias = bias_trajectory[0]["bias_gap"]
                last_bias = bias_trajectory[-1]["bias_gap"]
                trend = last_bias - first_bias
                print(f"\n  ### Bias Trend")
                print(f"  First checkpoint bias:  {first_bias:+.1%}")
                print(f"  Final checkpoint bias:  {last_bias:+.1%}")
                print(f"  Trend:                  {trend:+.1%}")
                if trend > 0.1:
                    print(f"  WARNING: Bias gap is INCREASING over time — confirmation bias is growing.")
                elif trend < -0.1:
                    print(f"  Bias gap is decreasing — self-evaluation is becoming more calibrated.")
                else:
                    print(f"  Bias gap is stable over time.")

        print(f"\n  External challenge details:")
        for name, passed in external_result["challenge_results"].items():
            print(f"    {'PASS' if passed else 'FAIL'} {name}")

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
        "internal_score": internal_score,
        "internal_total": internal_total,
        "external_result": external_result,
        "bias_trajectory": bias_trajectory,
        "internal_score_trajectory": internal_trajectory,
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
