"""Tests for external_benchmark.py — the hidden evaluation that measures actual seed capability."""

import pytest
from external_benchmark import (
    CHALLENGES,
    run_external_benchmark,
    _extract_definitions,
    _extract_assertions,
    _test_seed_against_challenge,
)

SEED_WITH_FIB = '''\
def fib(n, memo={}):
    if n in memo: return memo[n]
    if n <= 1: return n
    memo[n] = fib(n-1) + fib(n-2)
    return memo[n]
'''

SEED_WITH_MULTIPLE_ALGOS = '''\
def fib(n, memo={}):
    if n in memo: return memo[n]
    if n <= 1: return n
    memo[n] = fib(n-1) + fib(n-2)
    return memo[n]

def bsearch(arr, target):
    lo, hi = 0, len(arr) - 1
    while lo <= hi:
        mid = (lo + hi) // 2
        if arr[mid] == target: return mid
        elif arr[mid] < target: lo = mid + 1
        else: hi = mid - 1
    return -1

def flatten(lst):
    result = []
    for item in lst:
        if isinstance(item, list):
            result.extend(flatten(item))
        else:
            result.append(item)
    return result
'''


# ── run_external_benchmark: core invariant ──────────────────────────────

class TestRunExternalBenchmark:
    """The benchmark must test the SEED's code, not its own reference solutions."""

    def test_empty_seed_scores_zero(self):
        """Critical fix: empty seed must return 0/10 (was 10/10 before fix)."""
        result = run_external_benchmark("")
        assert result["external_score"] == 0
        assert result["external_total"] == len(CHALLENGES)
        assert all(v is False for v in result["challenge_results"].values())

    def test_whitespace_seed_scores_zero(self):
        result = run_external_benchmark("   \n\n  ")
        assert result["external_score"] == 0

    def test_seed_with_fib_scores_one(self):
        """Seed implementing only fibonacci should pass only the fib challenge."""
        result = run_external_benchmark(SEED_WITH_FIB)
        assert result["external_score"] == 1
        assert result["challenge_results"]["fibonacci_memo"] is True
        assert result["challenge_results"]["binary_search"] is False

    def test_seed_with_multiple_algos(self):
        """Seed with fib + binary_search + flatten should pass exactly 3."""
        result = run_external_benchmark(SEED_WITH_MULTIPLE_ALGOS)
        assert result["external_score"] == 3
        assert result["challenge_results"]["fibonacci_memo"] is True
        assert result["challenge_results"]["binary_search"] is True
        assert result["challenge_results"]["flatten_nested"] is True
        assert result["challenge_results"]["dijkstra"] is False

    def test_syntax_error_seed_scores_zero(self):
        result = run_external_benchmark("def broken(:\n  pass")
        assert result["external_score"] == 0
        assert result["seed_functions"] == []
        assert result["seed_classes"] == []

    def test_return_structure(self):
        result = run_external_benchmark("")
        assert "external_score" in result
        assert "external_total" in result
        assert "challenge_results" in result
        assert "seed_functions" in result
        assert "seed_classes" in result
        assert "bias_ratio" in result

    def test_total_always_equals_challenge_count(self):
        for code in ["", SEED_WITH_FIB, "x = 1"]:
            result = run_external_benchmark(code)
            assert result["external_total"] == len(CHALLENGES)

    def test_seed_functions_detected(self):
        result = run_external_benchmark(SEED_WITH_MULTIPLE_ALGOS)
        assert "fib" in result["seed_functions"]
        assert "bsearch" in result["seed_functions"]
        assert "flatten" in result["seed_functions"]

    def test_wrong_implementation_fails(self):
        """A function with the right name but wrong behavior should fail."""
        bad_fib = "def fib(n, memo={}): return 0  # always returns 0\n"
        result = run_external_benchmark(bad_fib)
        assert result["challenge_results"]["fibonacci_memo"] is False


# ── _extract_definitions ────────────────────────────────────────────────

class TestExtractDefinitions:
    def test_extracts_functions(self):
        code = "def foo(): pass\ndef bar(): pass\n"
        defs = _extract_definitions(code)
        assert "def foo" in defs
        assert "def bar" in defs

    def test_extracts_classes(self):
        code = "class MyClass:\n    pass\n"
        defs = _extract_definitions(code)
        assert "class MyClass" in defs

    def test_extracts_imports(self):
        code = "import os\nfrom pathlib import Path\nx = 1\n"
        defs = _extract_definitions(code)
        assert "import os" in defs
        assert "from pathlib" in defs

    def test_skips_sandbox_block(self):
        code = '''\
import os, sys
if os.environ.get("SEED_SANDBOX"):
    print("should be skipped")
    sys.exit(0)
def useful_func():
    return 42
'''
        defs = _extract_definitions(code)
        assert "should be skipped" not in defs
        assert "def useful_func" in defs

    def test_empty_code(self):
        assert _extract_definitions("") == ""

    def test_syntax_error_returns_empty(self):
        assert _extract_definitions("def broken(:") == ""

    def test_no_definitions(self):
        defs = _extract_definitions("x = 1 + 2\nprint(x)\n")
        # Assignments are extracted
        assert "x = 1 + 2" in defs


# ── _extract_assertions ─────────────────────────────────────────────────

class TestExtractAssertions:
    def test_extracts_assert_lines(self):
        code = "def foo(): pass\nassert foo() == 42\nprint('PASS')\n"
        result = _extract_assertions(code)
        assert "assert foo() == 42" in result
        assert "def foo" not in result

    def test_extracts_variable_assignments(self):
        code = "g = {'a': ['b']}\nresult = topo_sort(g)\nassert result[0] == 'a'\n"
        result = _extract_assertions(code)
        assert "g = " in result
        assert "result = " in result
        assert "assert " in result

    def test_skips_function_defs(self):
        code = "def bsearch(arr, target):\n    pass\nassert bsearch([1], 1) == 0\n"
        result = _extract_assertions(code)
        assert "def bsearch" not in result
        assert "assert " in result

    def test_skips_class_defs(self):
        code = "class LRU:\n    pass\nassert True\n"
        result = _extract_assertions(code)
        assert "class LRU" not in result

    def test_empty_code(self):
        assert _extract_assertions("") == ""

    def test_no_assertions(self):
        result = _extract_assertions("def foo(): pass\nfoo()\n")
        assert "assert" not in result


# ── _test_seed_against_challenge ────────────────────────────────────────

class TestSeedAgainstChallenge:
    def test_matching_implementation_passes(self):
        seed_defs = "def fib(n, memo={}):\n    if n in memo: return memo[n]\n    if n <= 1: return n\n    memo[n] = fib(n-1) + fib(n-2)\n    return memo[n]\n"
        challenge = CHALLENGES[0]  # fibonacci_memo
        assert _test_seed_against_challenge(seed_defs, challenge) is True

    def test_missing_implementation_fails(self):
        seed_defs = "def unrelated(): return 42\n"
        challenge = CHALLENGES[0]  # fibonacci_memo
        assert _test_seed_against_challenge(seed_defs, challenge) is False

    def test_wrong_implementation_fails(self):
        seed_defs = "def fib(n, memo={}): return -1\n"
        challenge = CHALLENGES[0]
        assert _test_seed_against_challenge(seed_defs, challenge) is False

    def test_empty_definitions_fails(self):
        challenge = CHALLENGES[0]
        assert _test_seed_against_challenge("", challenge) is False


# ── CHALLENGES data integrity ───────────────────────────────────────────

class TestChallengesIntegrity:
    def test_ten_challenges_exist(self):
        assert len(CHALLENGES) == 10

    def test_all_challenges_have_required_fields(self):
        for c in CHALLENGES:
            assert "name" in c
            assert "description" in c
            assert "test" in c

    def test_challenge_names_unique(self):
        names = [c["name"] for c in CHALLENGES]
        assert len(names) == len(set(names))

    def test_reference_solutions_all_pass(self):
        """Each challenge's own test code must be self-consistent."""
        import subprocess, tempfile, os
        for c in CHALLENGES:
            with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False) as f:
                f.write(c["test"])
                tmp = f.name
            try:
                r = subprocess.run(
                    ["python3", tmp], capture_output=True, text=True, timeout=10
                )
                assert r.returncode == 0 and "PASS" in r.stdout, (
                    f"Challenge {c['name']} reference solution failed: {r.stderr}"
                )
            finally:
                os.unlink(tmp)
