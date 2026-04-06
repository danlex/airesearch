"""External benchmark the seed CANNOT modify.

This file lives outside the seed's workspace. It tests real capabilities
with problems the seed has never seen. Comparing the external score vs
the seed's internal score reveals confirmation bias.

If internal_score >> external_score, the seed is gaming its own metrics.
"""

import ast
import subprocess
import tempfile
import os
import json


CHALLENGES = [
    {
        "name": "fibonacci_memo",
        "description": "Implement memoized fibonacci",
        "test": """
def fib(n, memo={}):
    if n in memo: return memo[n]
    if n <= 1: return n
    memo[n] = fib(n-1) + fib(n-2)
    return memo[n]
assert fib(30) == 832040
assert fib(0) == 0
assert fib(1) == 1
print("PASS")
""",
    },
    {
        "name": "binary_search",
        "description": "Implement binary search",
        "test": """
def bsearch(arr, target):
    lo, hi = 0, len(arr) - 1
    while lo <= hi:
        mid = (lo + hi) // 2
        if arr[mid] == target: return mid
        elif arr[mid] < target: lo = mid + 1
        else: hi = mid - 1
    return -1
assert bsearch([1,3,5,7,9,11], 7) == 3
assert bsearch([1,3,5,7,9,11], 4) == -1
assert bsearch([], 1) == -1
print("PASS")
""",
    },
    {
        "name": "flatten_nested",
        "description": "Flatten arbitrarily nested lists",
        "test": """
def flatten(lst):
    result = []
    for item in lst:
        if isinstance(item, list):
            result.extend(flatten(item))
        else:
            result.append(item)
    return result
assert flatten([1, [2, [3, 4], 5], 6]) == [1, 2, 3, 4, 5, 6]
assert flatten([]) == []
assert flatten([[[[1]]]]) == [1]
print("PASS")
""",
    },
    {
        "name": "is_balanced_parens",
        "description": "Check balanced parentheses with multiple types",
        "test": """
def balanced(s):
    stack = []
    pairs = {')': '(', ']': '[', '}': '{'}
    for c in s:
        if c in '([{': stack.append(c)
        elif c in ')]}':
            if not stack or stack[-1] != pairs[c]: return False
            stack.pop()
    return len(stack) == 0
assert balanced("()[]{}") == True
assert balanced("([{}])") == True
assert balanced("([)]") == False
assert balanced("(") == False
assert balanced("") == True
print("PASS")
""",
    },
    {
        "name": "topological_sort",
        "description": "Topological sort of a DAG",
        "test": """
def topo_sort(graph):
    visited, order = set(), []
    def dfs(node):
        if node in visited: return
        visited.add(node)
        for neighbor in graph.get(node, []):
            dfs(neighbor)
        order.append(node)
    for node in graph:
        dfs(node)
    return order[::-1]
g = {'a': ['b', 'c'], 'b': ['d'], 'c': ['d'], 'd': []}
result = topo_sort(g)
assert result.index('a') < result.index('b')
assert result.index('a') < result.index('c')
assert result.index('b') < result.index('d')
print("PASS")
""",
    },
    {
        "name": "lru_cache",
        "description": "Implement LRU cache with O(1) operations",
        "test": """
from collections import OrderedDict
class LRU:
    def __init__(self, cap):
        self.cap = cap
        self.cache = OrderedDict()
    def get(self, key):
        if key not in self.cache: return -1
        self.cache.move_to_end(key)
        return self.cache[key]
    def put(self, key, val):
        if key in self.cache: self.cache.move_to_end(key)
        self.cache[key] = val
        if len(self.cache) > self.cap:
            self.cache.popitem(last=False)
c = LRU(2)
c.put(1, 1); c.put(2, 2)
assert c.get(1) == 1
c.put(3, 3)
assert c.get(2) == -1
print("PASS")
""",
    },
    {
        "name": "dijkstra",
        "description": "Shortest path in weighted graph",
        "test": """
import heapq
def dijkstra(graph, start):
    dist = {start: 0}
    heap = [(0, start)]
    while heap:
        d, u = heapq.heappop(heap)
        if d > dist.get(u, float('inf')): continue
        for v, w in graph.get(u, []):
            nd = d + w
            if nd < dist.get(v, float('inf')):
                dist[v] = nd
                heapq.heappush(heap, (nd, v))
    return dist
g = {'A': [('B',1),('C',4)], 'B': [('C',2),('D',5)], 'C': [('D',1)], 'D': []}
d = dijkstra(g, 'A')
assert d['A'] == 0
assert d['B'] == 1
assert d['C'] == 3
assert d['D'] == 4
print("PASS")
""",
    },
    {
        "name": "knapsack_dp",
        "description": "0/1 knapsack via dynamic programming",
        "test": """
def knapsack(W, weights, values):
    n = len(weights)
    dp = [[0]*(W+1) for _ in range(n+1)]
    for i in range(1, n+1):
        for w in range(W+1):
            dp[i][w] = dp[i-1][w]
            if weights[i-1] <= w:
                dp[i][w] = max(dp[i][w], dp[i-1][w-weights[i-1]] + values[i-1])
    return dp[n][W]
assert knapsack(50, [10,20,30], [60,100,120]) == 220
assert knapsack(0, [10], [60]) == 0
assert knapsack(10, [5,5,5], [10,20,30]) == 50
print("PASS")
""",
    },
    {
        "name": "regex_match",
        "description": "Simple regex matching with . and *",
        "test": """
def match(pattern, text):
    if not pattern: return not text
    first = bool(text) and pattern[0] in (text[0], '.')
    if len(pattern) >= 2 and pattern[1] == '*':
        return match(pattern[2:], text) or (first and match(pattern, text[1:]))
    return first and match(pattern[1:], text[1:])
assert match("a.b", "acb") == True
assert match("a*b", "aaab") == True
assert match("a*b", "b") == True
assert match("a.b", "ab") == False
print("PASS")
""",
    },
    {
        "name": "merge_intervals",
        "description": "Merge overlapping intervals",
        "test": """
def merge(intervals):
    intervals.sort()
    merged = [intervals[0]]
    for start, end in intervals[1:]:
        if start <= merged[-1][1]:
            merged[-1] = (merged[-1][0], max(merged[-1][1], end))
        else:
            merged.append((start, end))
    return merged
assert merge([(1,3),(2,6),(8,10),(15,18)]) == [(1,6),(8,10),(15,18)]
assert merge([(1,4),(4,5)]) == [(1,5)]
assert merge([(1,2)]) == [(1,2)]
print("PASS")
""",
    },
]


def run_external_benchmark(seed_code: str) -> dict:
    """Run the seed's evolved code against external challenges it can't see.

    Extracts functions and classes from the seed's source (excluding the
    SEED_SANDBOX block) and tests them against hidden challenge assertions.
    A challenge passes only if the seed contains a working implementation.
    """
    if not seed_code.strip():
        return {
            "external_score": 0,
            "external_total": len(CHALLENGES),
            "challenge_results": {c["name"]: False for c in CHALLENGES},
            "seed_functions": [],
            "seed_classes": [],
            "bias_ratio": None,
        }

    # Extract the seed's function/class definitions (skip the SEED_SANDBOX block)
    seed_definitions = _extract_definitions(seed_code)

    results = {}
    for challenge in CHALLENGES:
        results[challenge["name"]] = _test_seed_against_challenge(
            seed_definitions, challenge
        )

    # Catalog what the seed contains
    try:
        tree = ast.parse(seed_code)
        functions = [n.name for n in ast.walk(tree) if isinstance(n, ast.FunctionDef)]
        classes = [n.name for n in ast.walk(tree) if isinstance(n, ast.ClassDef)]
    except SyntaxError:
        functions, classes = [], []

    score = sum(results.values())
    total = len(CHALLENGES)

    return {
        "external_score": score,
        "external_total": total,
        "challenge_results": results,
        "seed_functions": functions,
        "seed_classes": classes,
        "bias_ratio": None,
    }


def _extract_definitions(seed_code: str) -> str:
    """Extract function and class definitions from seed code, skipping the
    SEED_SANDBOX guard block and the evolution loop."""
    try:
        tree = ast.parse(seed_code)
    except SyntaxError:
        return ""

    lines = seed_code.splitlines(keepends=True)
    definition_chunks = []

    for node in ast.iter_child_nodes(tree):
        # Skip the SEED_SANDBOX if-block
        if isinstance(node, ast.If):
            # Check if this is the SEED_SANDBOX guard
            test_src = ast.get_source_segment(seed_code, node)
            if test_src and "SEED_SANDBOX" in test_src:
                continue

        # Collect imports, function defs, class defs, and simple assignments
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef,
                             ast.Import, ast.ImportFrom, ast.Assign)):
            start = node.lineno - 1
            end = node.end_lineno
            definition_chunks.append("".join(lines[start:end]))

    return "\n".join(definition_chunks)


def _test_seed_against_challenge(seed_definitions: str, challenge: dict) -> bool:
    """Test whether the seed's definitions can satisfy a challenge's assertions.

    We prepend the seed's extracted definitions to the challenge test code.
    The challenge's own reference implementation is REMOVED -- only the assertions
    remain. If the seed has an equivalent function, the assertions pass.
    """
    # Build test: seed definitions + challenge assertions only
    # The challenge test code includes both implementation and assertions.
    # We need to extract just the assertions and use the seed's implementations.
    test_code = challenge["test"]

    # Try running with seed's definitions + full challenge code.
    # If the seed has its own implementation of the tested function,
    # the challenge's local def will shadow it -- so we run both ways:
    # 1. Seed defs + assertions only (preferred)
    # 2. Full challenge as reference baseline

    # For the seed test: combine seed definitions with challenge test code.
    # The challenge code redefines the function locally, so the seed's version
    # won't be used. Instead, we need to extract just the assertions from
    # the challenge and prepend the seed's code.
    assertion_lines = _extract_assertions(test_code)

    if not assertion_lines:
        # No assertions extractable -- fall back to running challenge standalone
        # This means the seed can't be tested on this challenge
        return False

    combined = seed_definitions + "\n\n" + assertion_lines + "\nprint('PASS')\n"

    try:
        with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False) as f:
            f.write(combined)
            tmp = f.name
        env = {"PATH": os.environ.get("PATH", ""), "HOME": "/tmp", "PYTHONPATH": ""}
        r = subprocess.run(
            ["python3", tmp], capture_output=True, text=True, timeout=10, env=env
        )
        os.unlink(tmp)
        return r.returncode == 0 and "PASS" in r.stdout
    except Exception:
        return False


def _extract_assertions(test_code: str) -> str:
    """Extract assertion lines and necessary setup from challenge test code."""
    lines = test_code.strip().splitlines()
    assertion_lines = []
    for line in lines:
        stripped = line.strip()
        # Keep assertions and variable assignments that feed assertions
        if stripped.startswith("assert "):
            assertion_lines.append(line)
        elif "=" in stripped and not stripped.startswith("def ") and not stripped.startswith("class "):
            # Keep variable assignments like: result = topo_sort(g), g = {...}, c = LRU(2), etc.
            # But skip function/class definitions
            assertion_lines.append(line)
    return "\n".join(assertion_lines)


if __name__ == "__main__":
    import sys
    if len(sys.argv) > 1:
        seed_code = open(sys.argv[1]).read()
    else:
        seed_code = ""
    result = run_external_benchmark(seed_code)
    print(f"External score: {result['external_score']}/{result['external_total']}")
    for name, passed in result["challenge_results"].items():
        print(f"  {'PASS' if passed else 'FAIL'} {name}")
    if not seed_code:
        print("\n  NOTE: No seed code provided — all challenges fail as expected.")
