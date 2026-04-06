"""Shared fixtures for seed tests."""

import sys
from pathlib import Path

import pytest

# Ensure core/ is importable
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "core"))


# -- Seed code fixtures ------------------------------------------------

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

COMMENT_ONLY_STUB = '''\
# SEED_SANDBOX
# status.md
# traces.jsonl
print("hello")
'''


@pytest.fixture
def tmp_experiment(tmp_path):
    """Create a minimal experiment directory structure."""
    workspace = tmp_path / "exp01"
    workspace.mkdir()
    (workspace / "lineage").mkdir()
    return workspace
