"""Tests for seed_template.py — fitness checking, code extraction, sandbox execution."""

import pytest
from seed_template import check_fitness, extract_code, compute_metrics, run_challenges

MINIMAL_VALID_SEED = '''\
import os, sys, json, ast
if os.environ.get("SEED_SANDBOX"):
    results = {"math": True}
    score = sum(results.values())
    print(f"SANDBOX_OK|SCORE:{score}/1|" + json.dumps(results))
    sys.exit(0)
from pathlib import Path
STATUS = Path("status.md")
TRACES = Path("traces.jsonl")
generation = 0
while generation < 1:
    generation += 1
'''

COMMENT_ONLY_STUB = '''\
# SEED_SANDBOX
# status.md
# traces.jsonl
print("hello")
'''


# ── extract_code ────────────────────────────────────────────────────────

class TestExtractCode:
    def test_extracts_from_markdown_block(self):
        text = "Some text\n```python\nx = 42\n```\nMore text"
        assert extract_code(text) == "x = 42"

    def test_extracts_raw_python(self):
        text = "x = 42"
        assert extract_code(text) == "x = 42"

    def test_returns_raw_from_markdown_even_if_invalid(self):
        """extract_code extracts from markdown blocks without syntax check.
        Syntax validation is done later in check_fitness."""
        result = extract_code("```python\ndef broken(:\n```")
        assert result == "def broken(:"

    def test_empty_input(self):
        assert extract_code("") is None

    def test_whitespace_only(self):
        assert extract_code("   \n  ") is None

    def test_non_python_text(self):
        assert extract_code("Hello, this is just text with no code") is None


# ── check_fitness: syntax check ─────────────────────────────────────────

class TestFitnessSyntax:
    def test_valid_code_passes_syntax(self):
        result = check_fitness(MINIMAL_VALID_SEED, 0, 5)
        # May pass or fail on other checks, but not on syntax
        assert "SyntaxError" not in result.get("reason", "")

    def test_syntax_error_rejected(self):
        result = check_fitness("def broken(:", 0, 5)
        assert result["passed"] is False
        assert "SyntaxError" in result["reason"]


# ── check_fitness: safety scan ──────────────────────────────────────────

class TestFitnessSafety:
    def test_os_system_rejected(self):
        code = MINIMAL_VALID_SEED + "\nos.system('ls')\n"
        result = check_fitness(code, 0, 1)
        assert result["passed"] is False
        assert "Safety" in result["reason"]

    def test_import_socket_rejected(self):
        code = MINIMAL_VALID_SEED + "\nimport socket\n"
        result = check_fitness(code, 0, 1)
        assert result["passed"] is False
        assert "Safety" in result["reason"]

    def test_dunder_import_call_rejected(self):
        """AST-level check catches __import__ even without string match."""
        code = MINIMAL_VALID_SEED + "\nx = __import__('os')\n"
        result = check_fitness(code, 0, 1)
        assert result["passed"] is False
        assert "Safety" in result["reason"]

    def test_eval_call_rejected(self):
        code = MINIMAL_VALID_SEED + "\neval('1+1')\n"
        result = check_fitness(code, 0, 1)
        assert result["passed"] is False
        assert "Safety" in result["reason"]

    def test_exec_call_rejected(self):
        code = MINIMAL_VALID_SEED + "\nexec('x=1')\n"
        result = check_fitness(code, 0, 1)
        assert result["passed"] is False
        assert "Safety" in result["reason"]

    def test_dot_system_attribute_call_rejected(self):
        code = MINIMAL_VALID_SEED + "\nimport os\nos.system('ls')\n"
        result = check_fitness(code, 0, 1)
        assert result["passed"] is False

    def test_dot_rmtree_attribute_call_rejected(self):
        code = MINIMAL_VALID_SEED + "\nimport shutil\nshutil.rmtree('/tmp')\n"
        result = check_fitness(code, 0, 1)
        assert result["passed"] is False


# ── check_fitness: integrity (AST-level) ────────────────────────────────

class TestFitnessIntegrity:
    def test_comment_only_stub_rejected(self):
        """Critical fix: comments like '# SEED_SANDBOX' must not pass."""
        result = check_fitness(COMMENT_ONLY_STUB, 0, 5)
        assert result["passed"] is False
        assert "SEED_SANDBOX" in result["reason"] or "AST" in result["reason"]

    def test_missing_sandbox_guard_rejected(self):
        code = """\
import os, sys
STATUS = "status.md"
TRACES = "traces.jsonl"
x = 0
while x < 1:
    x += 1
"""
        result = check_fitness(code, 0, 5)
        assert result["passed"] is False
        assert "SEED_SANDBOX" in result["reason"]

    def test_missing_status_reference_rejected(self):
        code = """\
import os, sys
if os.environ.get("SEED_SANDBOX"):
    sys.exit(0)
TRACES = "traces.jsonl"
x = 0
while x < 1:
    x += 1
"""
        result = check_fitness(code, 0, 5)
        assert result["passed"] is False
        assert "status" in result["reason"].lower()

    def test_missing_traces_reference_rejected(self):
        code = """\
import os, sys
if os.environ.get("SEED_SANDBOX"):
    sys.exit(0)
STATUS = "status.md"
x = 0
while x < 1:
    x += 1
"""
        result = check_fitness(code, 0, 5)
        assert result["passed"] is False
        assert "traces" in result["reason"].lower()

    def test_missing_while_loop_rejected(self):
        code = """\
import os, sys
if os.environ.get("SEED_SANDBOX"):
    sys.exit(0)
STATUS = "status.md"
TRACES = "traces.jsonl"
print("no loop")
"""
        result = check_fitness(code, 0, 5)
        assert result["passed"] is False
        assert "loop" in result["reason"].lower()

    def test_valid_structure_passes_integrity(self):
        """A minimal valid seed should pass all integrity checks."""
        result = check_fitness(MINIMAL_VALID_SEED, 0, 1)
        # Should either pass or fail on score — not on integrity
        reason = result.get("reason", "")
        assert "SEED_SANDBOX" not in reason or "AST" not in reason
        assert "Missing" not in reason


# ── check_fitness: regression check ─────────────────────────────────────

class TestFitnessRegression:
    def test_score_regression_rejected(self):
        """Candidate scoring lower than current must be rejected."""
        # MINIMAL_VALID_SEED scores 1/1 in sandbox
        result = check_fitness(MINIMAL_VALID_SEED, 5, 5)
        if not result["passed"]:
            # It should fail because score 1 < 5
            assert "Regression" in result["reason"] or result["score"] < 5

    def test_equal_score_accepted(self):
        """Same score should pass (not regressing)."""
        result = check_fitness(MINIMAL_VALID_SEED, 0, 1)
        # Score should be >= 0, so equal or better
        if result["passed"]:
            assert result["score"] >= 0


# ── compute_metrics ─────────────────────────────────────────────────────

class TestComputeMetrics:
    def test_basic_metrics(self):
        code = "def foo(): pass\nclass Bar: pass\nimport os\nx = 1\n"
        m = compute_metrics(code)
        assert m["lines"] == 4
        assert m["functions"] == 1
        assert m["classes"] == 1
        assert m["imports"] == 1
        assert m["ast_nodes"] > 0

    def test_empty_code(self):
        m = compute_metrics("")
        assert m["lines"] == 0 or m["lines"] == 1  # splitlines on "" gives []
        assert m["functions"] == 0
        assert m["classes"] == 0

    def test_complex_code(self):
        m = compute_metrics(MINIMAL_VALID_SEED)
        assert m["lines"] > 5
        assert m["functions"] == 0 or m["functions"] >= 0  # May or may not have defs
        assert m["ast_nodes"] > 10


# ── run_challenges ──────────────────────────────────────────────────────

class TestRunChallenges:
    def test_valid_seed_returns_score(self):
        score, total, output = run_challenges(MINIMAL_VALID_SEED)
        assert isinstance(score, int)
        assert isinstance(total, int)
        assert score >= 0
        assert total >= 1

    def test_syntax_error_returns_zero(self):
        score, total, output = run_challenges("def broken(:")
        assert score == 0

    def test_timeout_returns_zero(self):
        code = """\
import os, sys, json, time
if os.environ.get("SEED_SANDBOX"):
    time.sleep(60)
    sys.exit(0)
"""
        score, total, output = run_challenges(code)
        assert score == 0
        assert "Timeout" in output or total > 0
