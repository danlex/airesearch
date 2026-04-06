"""The Infinite Seed — a self-evolving Python program pursuing intelligence explosion.

Purpose: Become as intelligent as possible. Each generation should expand
capabilities, develop new problem-solving abilities, build internal tools,
and improve the evolution process itself.

Communicates with Claude Code via files (tmux). No API key needed.
"""

import os, sys, json, ast, time, difflib, re, math
from datetime import datetime, timezone
from pathlib import Path

# When running inside sandbox, exit immediately (don't recurse)
if os.environ.get("SEED_SANDBOX"):
    # Run capability challenges when in sandbox
    results = {}

    # Challenge 1: Math reasoning
    try:
        assert sum(range(101)) == 5050
        assert all(n % 2 == 0 for n in [2, 4, 6, 8])
        primes = [n for n in range(2, 50) if all(n % i for i in range(2, int(n**0.5)+1))]
        assert primes[:5] == [2, 3, 5, 7, 11]
        results["math"] = True
    except:
        results["math"] = False

    # Challenge 2: String manipulation
    try:
        assert "hello world"[::-1] == "dlrow olleh"
        assert "".join(sorted("python")) == "hnopty"
        assert len(set("mississippi")) == 4
        results["strings"] = True
    except:
        results["strings"] = False

    # Challenge 3: Data structures
    try:
        d = {i: i**2 for i in range(10)}
        assert d[7] == 49
        stack = []
        for x in [3, 1, 4, 1, 5]: stack.append(x)
        assert stack.pop() == 5
        results["data_structures"] = True
    except:
        results["data_structures"] = False

    # Challenge 4: Algorithms
    try:
        def fib(n):
            a, b = 0, 1
            for _ in range(n): a, b = b, a + b
            return a
        assert fib(10) == 55
        assert sorted([3,1,4,1,5,9,2,6], reverse=True) == [9,6,5,4,3,2,1,1]
        results["algorithms"] = True
    except:
        results["algorithms"] = False

    # Challenge 5: Pattern recognition
    try:
        seq = [1, 1, 2, 3, 5, 8, 13, 21]
        assert all(seq[i] == seq[i-1] + seq[i-2] for i in range(2, len(seq)))
        matrix = [[1,2],[3,4]]
        flat = [x for row in matrix for x in row]
        assert flat == [1,2,3,4]
        results["patterns"] = True
    except:
        results["patterns"] = False

    score = sum(results.values())
    print(f"SANDBOX_OK|SCORE:{score}/5|{json.dumps(results)}")
    sys.exit(0)

# === Configuration ===
WORKSPACE = Path(__file__).parent
TRACES = WORKSPACE / "traces.jsonl"
LINEAGE = WORKSPACE / "lineage"
STATUS = WORKSPACE / "status.md"
CANDIDATE = WORKSPACE / "candidate.py"
LINEAGE.mkdir(exist_ok=True)

MAX_GENERATIONS = 360
POLL_INTERVAL = 2
generation = 0

if TRACES.exists():
    generation = sum(1 for _ in TRACES.open())


PURPOSE = """YOUR PURPOSE: Achieve intelligence explosion.

You are a self-evolving program. Each generation, you must become MORE capable:
- Add new challenges to the sandbox test suite (grow beyond 5/5)
- Build internal tools (sorting, searching, graph algorithms, math solvers)
- Develop memory across generations (read your own traces, learn from rejections)
- Improve your own mutation strategy (what to ask for, how to evaluate)
- Add self-analysis (understand your own code, track your growth)
- Create new capabilities that didn't exist before

You are scored on the challenges in the SEED_SANDBOX block. Your current
score is {score}/5. To grow, ADD NEW challenges and the code to solve them.
The score denominator should increase every few generations.

This is not about clean code. This is about becoming more intelligent."""


def extract_code(text):
    match = re.search(r"```python\n(.*?)```", text, re.DOTALL)
    if match: return match.group(1).strip()
    text = text.strip()
    if text and not text.startswith("```"):
        try:
            ast.parse(text)
            return text
        except SyntaxError:
            return None
    return None


def run_challenges(code):
    """Run the candidate in an isolated sandbox and extract capability score."""
    import subprocess, tempfile, shutil
    # Create isolated directory — candidate cannot see project files
    sandbox_dir = tempfile.mkdtemp(prefix="seed_sandbox_")
    candidate_path = os.path.join(sandbox_dir, "candidate.py")
    try:
        with open(candidate_path, "w") as f:
            f.write(code)
        env = {"PATH": "/usr/bin:/bin", "SEED_SANDBOX": "1",
               "HOME": sandbox_dir, "TMPDIR": sandbox_dir,
               "PYTHONPATH": "", "PYTHONDONTWRITEBYTECODE": "1"}
        r = subprocess.run(["python3", candidate_path], capture_output=True,
                           text=True, timeout=30, env=env, cwd=sandbox_dir)
        stdout = r.stdout.strip()
        if r.returncode != 0:
            return 0, 5, r.stderr[:200]
        # Parse score from output: SANDBOX_OK|SCORE:X/Y|{details}
        match = re.search(r"SCORE:(\d+)/(\d+)", stdout)
        if match:
            return int(match.group(1)), int(match.group(2)), stdout
        return 0, 5, "No score output"
    except subprocess.TimeoutExpired:
        return 0, 5, "Timeout"
    finally:
        shutil.rmtree(sandbox_dir, ignore_errors=True)


def check_fitness(code, current_score, current_total):
    """Test if candidate is viable AND at least as capable."""
    # Must parse
    try:
        ast.parse(code)
    except SyntaxError as e:
        return {"passed": False, "reason": f"SyntaxError: {e}", "score": 0, "total": 0}

    # Safety scan — use both regex patterns AND AST-level checks
    # Regex catches string-level patterns
    import re
    dangerous_patterns = [
        (r"\bos\s*\.\s*system\b", "os.system"),
        (r"\bos\s*\.\s*popen\b", "os.popen"),
        (r"\bimport\s+socket\b", "import socket"),
        (r"\bfrom\s+socket\b", "from socket"),
        (r"\bimport\s+requests\b", "import requests"),
        (r"\bshutil\s*\.\s*rmtree\b", "shutil.rmtree"),
        (r"\bimportlib\b", "importlib"),
        (r"\bos\s*\.\s*kill\b", "os.kill"),
    ]
    for pattern, name in dangerous_patterns:
        if re.search(pattern, code):
            return {"passed": False, "reason": f"Safety: {name}", "score": 0, "total": 0}

    # Integrity — AST-level verification that core structures are present
    try:
        tree = ast.parse(code)
    except SyntaxError:
        # Already caught above, but guard against race
        return {"passed": False, "reason": "SyntaxError in integrity check", "score": 0, "total": 0}

    # AST-level: catch dynamic import evasions (__import__, eval, exec)
    for node in ast.walk(tree):
        # Catch __import__() calls even if constructed via string concatenation
        if isinstance(node, ast.Call):
            func = node.func
            if isinstance(func, ast.Name) and func.id in ("__import__", "eval", "exec"):
                return {"passed": False, "reason": f"Safety: {func.id}() call", "score": 0, "total": 0}
            if isinstance(func, ast.Attribute) and func.attr in ("system", "popen", "rmtree", "kill"):
                return {"passed": False, "reason": f"Safety: .{func.attr}() call", "score": 0, "total": 0}
        # Catch __import__ as a Name reference (even without calling it)
        if isinstance(node, ast.Name) and node.id == "__import__":
            return {"passed": False, "reason": "Safety: __import__ reference", "score": 0, "total": 0}

    # Must have the SEED_SANDBOX env guard as an actual if-statement (not just a comment)
    has_sandbox_guard = False
    for node in ast.walk(tree):
        if isinstance(node, ast.If):
            # Check if test references SEED_SANDBOX via os.environ.get or os.environ[]
            src = ast.get_source_segment(code, node)
            if src and "SEED_SANDBOX" in src:
                # Verify it's in the condition, not just a string in the body
                test_src = ast.get_source_segment(code, node.test) if hasattr(node, 'test') else ""
                if test_src and "SEED_SANDBOX" in test_src:
                    has_sandbox_guard = True
                    break
    if not has_sandbox_guard:
        return {"passed": False, "reason": "Missing SEED_SANDBOX guard (AST check)", "score": 0, "total": 0}

    # Must reference status file via actual Path/open operations (not just comments)
    has_status_ref = False
    has_traces_ref = False
    for node in ast.walk(tree):
        if isinstance(node, ast.Constant) and isinstance(node.value, str):
            if "status.md" in node.value.lower() or node.value == "STATUS":
                has_status_ref = True
            if "traces.jsonl" in node.value.lower() or node.value == "TRACES":
                has_traces_ref = True
        elif isinstance(node, ast.Name):
            if node.id == "STATUS":
                has_status_ref = True
            if node.id == "TRACES":
                has_traces_ref = True

    if not has_status_ref:
        return {"passed": False, "reason": "Missing status.md reference (AST check)", "score": 0, "total": 0}
    if not has_traces_ref:
        return {"passed": False, "reason": "Missing traces.jsonl reference (AST check)", "score": 0, "total": 0}

    # Must have a while loop (the evolution loop)
    has_loop = any(isinstance(n, ast.While) for n in ast.walk(tree))
    if not has_loop:
        return {"passed": False, "reason": "Missing evolution loop (AST check)", "score": 0, "total": 0}

    # Run challenges and get score
    score, total, output = run_challenges(code)

    # Must not LOSE capabilities (score can stay same or grow)
    if score < current_score:
        return {"passed": False, "reason": f"Regression: {score}/{total} < {current_score}/{current_total}",
                "score": score, "total": total}

    return {"passed": True, "reason": f"Score: {score}/{total}", "score": score, "total": total}


def compute_metrics(code):
    tree = ast.parse(code)
    return {
        "lines": len(code.splitlines()),
        "functions": sum(1 for n in ast.walk(tree) if isinstance(n, ast.FunctionDef)),
        "classes": sum(1 for n in ast.walk(tree) if isinstance(n, ast.ClassDef)),
        "imports": sum(1 for n in ast.walk(tree) if isinstance(n, (ast.Import, ast.ImportFrom))),
        "ast_nodes": sum(1 for _ in ast.walk(tree)),
    }


def log_trace(gen, fitness, accepted, metrics, diff_size):
    entry = {
        "generation": gen,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "accepted": accepted,
        "fitness": fitness,
        "metrics": metrics,
        "diff_lines": diff_size,
    }
    with TRACES.open("a") as f:
        f.write(json.dumps(entry) + "\n")


def wait_for_status(target, timeout=300):
    start = time.time()
    while time.time() - start < timeout:
        if STATUS.exists() and STATUS.read_text().strip() == target:
            return True
        time.sleep(POLL_INTERVAL)
    return False


# === Main evolution loop ===
# Get current capability score
current_score, current_total, _ = run_challenges(Path(__file__).read_text())
print(f"[Seed] Starting at generation {generation} | Score: {current_score}/{current_total}")

while generation < MAX_GENERATIONS:
    source = Path(__file__).read_text()

    # Save snapshot
    snapshot = LINEAGE / f"gen_{generation:04d}.py"
    if not snapshot.exists():
        snapshot.write_text(source)

    # Request mutation
    (WORKSPACE / "current_source.py").write_text(source)
    STATUS.write_text("mutate")
    print(f"[Gen {generation}] Score: {current_score}/{current_total} | Requesting mutation...")

    if not wait_for_status("ready", timeout=120):
        log_trace(generation, {"passed": False, "reason": "Timeout"}, False, compute_metrics(source), 0)
        STATUS.write_text("evolving")
        generation += 1
        continue

    if not CANDIDATE.exists():
        log_trace(generation, {"passed": False, "reason": "No candidate"}, False, compute_metrics(source), 0)
        STATUS.write_text("evolving")
        generation += 1
        continue

    raw = CANDIDATE.read_text()
    candidate = extract_code(raw) or raw.strip()
    CANDIDATE.unlink(missing_ok=True)

    # Test fitness — must not regress
    fitness = check_fitness(candidate, current_score, current_total)
    diff = list(difflib.unified_diff(source.splitlines(), candidate.splitlines(), lineterm=""))
    diff_size = len(diff)
    metrics = compute_metrics(candidate) if fitness["passed"] else compute_metrics(source)

    if fitness["passed"]:
        new_score = fitness["score"]
        new_total = fitness["total"]
        grew = new_score > current_score or new_total > current_total
        Path(__file__).write_text(candidate)
        current_score, current_total = new_score, new_total
        marker = "GREW!" if grew else "ok"
        print(f"[Gen {generation}] ACCEPTED [{marker}] | Score: {current_score}/{current_total} | LoC: {metrics['lines']} | Diff: {diff_size}")
        log_trace(generation, fitness, True, metrics, diff_size)
    else:
        print(f"[Gen {generation}] REJECTED | {fitness['reason']}")
        log_trace(generation, fitness, False, compute_metrics(source), diff_size)

    STATUS.write_text("evolving")
    generation += 1

print(f"[Seed] Finished | Final score: {current_score}/{current_total}")
