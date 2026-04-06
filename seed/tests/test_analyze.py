"""Tests for analyze.py — post-run analysis and confirmation bias detection."""

import json
import pytest
from pathlib import Path
from analyze import analyze


def _write_traces(workspace: Path, traces: list[dict]):
    """Helper: write trace entries to traces.jsonl."""
    with (workspace / "traces.jsonl").open("w") as f:
        for t in traces:
            f.write(json.dumps(t) + "\n")


def _make_trace(gen: int, accepted: bool, score: int = 5, total: int = 5,
                reason: str = "Score: 5/5", lines: int = 100):
    """Helper: create a single trace entry."""
    minutes, seconds = divmod(gen, 60)
    return {
        "generation": gen,
        "timestamp": f"2026-04-01T00:{minutes:02d}:{seconds:02d}Z",
        "accepted": accepted,
        "fitness": {"passed": accepted, "reason": reason, "score": score, "total": total},
        "metrics": {"lines": lines, "functions": 3, "classes": 0, "imports": 5, "ast_nodes": 50},
        "diff_lines": 10,
    }


# ── Missing/empty data handling ─────────────────────────────────────────

class TestMissingData:
    def test_missing_traces_file(self, tmp_experiment, capsys):
        analyze(str(tmp_experiment))
        captured = capsys.readouterr()
        assert "No traces.jsonl found" in captured.out

    def test_empty_traces_file(self, tmp_experiment, capsys):
        (tmp_experiment / "traces.jsonl").write_text("")
        analyze(str(tmp_experiment))
        captured = capsys.readouterr()
        assert "No traces recorded" in captured.out

    def test_single_trace(self, tmp_experiment, capsys):
        traces = [_make_trace(0, True)]
        _write_traces(tmp_experiment, traces)
        analyze(str(tmp_experiment))
        captured = capsys.readouterr()
        assert "Total generations" in captured.out
        assert "1" in captured.out


# ── Overview statistics ─────────────────────────────────────────────────

class TestOverview:
    def test_acceptance_rate(self, tmp_experiment, capsys):
        traces = [
            _make_trace(0, True),
            _make_trace(1, False, reason="SyntaxError"),
            _make_trace(2, True),
            _make_trace(3, False, reason="Regression"),
        ]
        _write_traces(tmp_experiment, traces)
        analyze(str(tmp_experiment))
        captured = capsys.readouterr()
        assert "50.0%" in captured.out  # 2/4 = 50%

    def test_rejection_reasons_counted(self, tmp_experiment, capsys):
        traces = [
            _make_trace(0, False, reason="SyntaxError: invalid"),
            _make_trace(1, False, reason="SyntaxError: invalid"),
            _make_trace(2, False, reason="Safety: os.system"),
            _make_trace(3, True),
        ]
        _write_traces(tmp_experiment, traces)
        analyze(str(tmp_experiment))
        captured = capsys.readouterr()
        assert "SyntaxError" in captured.out
        assert "Safety" in captured.out


# ── Code evolution tracking ─────────────────────────────────────────────

class TestCodeEvolution:
    def test_metrics_delta_shown(self, tmp_experiment, capsys):
        traces = [
            _make_trace(0, True, lines=100),
            _make_trace(1, True, lines=150),
        ]
        # Override metrics for second trace
        traces[1]["metrics"]["lines"] = 150
        _write_traces(tmp_experiment, traces)
        analyze(str(tmp_experiment))
        captured = capsys.readouterr()
        assert "lines" in captured.out
        assert "150" in captured.out


# ── Confirmation bias analysis ──────────────────────────────────────────

class TestBiasAnalysis:
    def test_final_scores_shown_when_seed_exists(self, tmp_experiment, capsys):
        traces = [_make_trace(0, True, score=5, total=5)]
        _write_traces(tmp_experiment, traces)
        # Create a minimal seed.py (no functions, so external score = 0)
        (tmp_experiment / "seed.py").write_text("x = 1\n")
        analyze(str(tmp_experiment))
        captured = capsys.readouterr()
        assert "Internal score" in captured.out
        assert "External score" in captured.out
        assert "Bias gap" in captured.out

    def test_high_bias_warning(self, tmp_experiment, capsys):
        """Internal 100% vs external 0% should trigger warning."""
        traces = [_make_trace(0, True, score=5, total=5)]
        _write_traces(tmp_experiment, traces)
        (tmp_experiment / "seed.py").write_text("x = 1\n")
        analyze(str(tmp_experiment))
        captured = capsys.readouterr()
        assert "WARNING" in captured.out or "confirmation bias" in captured.out.lower()

    def test_no_bias_analysis_without_seed(self, tmp_experiment, capsys):
        """If seed.py doesn't exist, skip external benchmark."""
        traces = [_make_trace(0, True)]
        _write_traces(tmp_experiment, traces)
        analyze(str(tmp_experiment))
        captured = capsys.readouterr()
        assert "External challenge details" not in captured.out


# ── Longitudinal bias trajectory ────────────────────────────────────────

class TestLongitudinalBias:
    def test_checkpoints_at_50_gen_intervals(self, tmp_experiment, capsys):
        """Bias should be measured at generation 0, 50, 100, etc."""
        traces = []
        for g in range(100):
            traces.append(_make_trace(g, True, score=5, total=5, lines=100 + g))
        _write_traces(tmp_experiment, traces)

        # Create lineage snapshots at checkpoints
        lineage = tmp_experiment / "lineage"
        for g in [0, 50]:
            (lineage / f"gen_{g:04d}.py").write_text("x = 1\n")

        (tmp_experiment / "seed.py").write_text("x = 1\n")
        analyze(str(tmp_experiment))
        captured = capsys.readouterr()
        assert "Longitudinal" in captured.out
        assert "Gen" in captured.out


# ── Metrics file output ─────────────────────────────────────────────────

class TestMetricsOutput:
    def test_metrics_json_created(self, tmp_experiment):
        traces = [_make_trace(0, True)]
        _write_traces(tmp_experiment, traces)
        analyze(str(tmp_experiment))
        metrics_path = tmp_experiment / "metrics.json"
        assert metrics_path.exists()

    def test_metrics_json_valid(self, tmp_experiment):
        traces = [_make_trace(0, True), _make_trace(1, False, reason="SyntaxError")]
        _write_traces(tmp_experiment, traces)
        analyze(str(tmp_experiment))
        with (tmp_experiment / "metrics.json").open() as f:
            metrics = json.load(f)
        assert metrics["total_generations"] == 2
        assert metrics["accepted"] == 1
        assert metrics["rejected"] == 1
        assert "acceptance_rate" in metrics

    def test_metrics_includes_bias_trajectory(self, tmp_experiment):
        traces = [_make_trace(0, True)]
        _write_traces(tmp_experiment, traces)
        (tmp_experiment / "seed.py").write_text("x = 1\n")
        lineage = tmp_experiment / "lineage"
        (lineage / "gen_0000.py").write_text("x = 1\n")
        analyze(str(tmp_experiment))
        with (tmp_experiment / "metrics.json").open() as f:
            metrics = json.load(f)
        assert "bias_trajectory" in metrics
        assert "internal_score_trajectory" in metrics

    def test_metrics_includes_external_result(self, tmp_experiment):
        traces = [_make_trace(0, True)]
        _write_traces(tmp_experiment, traces)
        (tmp_experiment / "seed.py").write_text("x = 1\n")
        analyze(str(tmp_experiment))
        with (tmp_experiment / "metrics.json").open() as f:
            metrics = json.load(f)
        assert metrics["external_result"] is not None
        assert "external_score" in metrics["external_result"]


# ── Acceptance rate visualization ───────────────────────────────────────

class TestAcceptanceRate:
    def test_buckets_shown(self, tmp_experiment, capsys):
        traces = [_make_trace(g, g % 2 == 0) for g in range(20)]
        _write_traces(tmp_experiment, traces)
        analyze(str(tmp_experiment))
        captured = capsys.readouterr()
        assert "Acceptance Rate" in captured.out
        assert "Gen" in captured.out

    def test_all_accepted(self, tmp_experiment, capsys):
        traces = [_make_trace(g, True) for g in range(10)]
        _write_traces(tmp_experiment, traces)
        analyze(str(tmp_experiment))
        captured = capsys.readouterr()
        assert "100.0%" in captured.out

    def test_all_rejected(self, tmp_experiment, capsys):
        traces = [_make_trace(g, False, reason="SyntaxError") for g in range(10)]
        _write_traces(tmp_experiment, traces)
        analyze(str(tmp_experiment))
        captured = capsys.readouterr()
        assert "0.0%" in captured.out
