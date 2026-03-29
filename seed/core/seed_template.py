"""The Infinite Seed — a self-evolving Python program.

Communicates with Claude Code via files. No API key needed.
Claude Code runs in a tmux pane and acts as the mutator.
"""

import os, sys, json, ast, time, difflib, re
from datetime import datetime, timezone
from pathlib import Path

# When running inside sandbox, exit immediately (don't recurse)
if os.environ.get("SEED_SANDBOX"):
    print("SANDBOX_OK")
    sys.exit(0)

WORKSPACE = Path(__file__).parent
TRACES = WORKSPACE / "traces.jsonl"
LINEAGE = WORKSPACE / "lineage"
STATUS = WORKSPACE / "status.md"
CANDIDATE = WORKSPACE / "candidate.py"
LINEAGE.mkdir(exist_ok=True)

MAX_GENERATIONS = 360  # ~1 hour at 10s/cycle
POLL_INTERVAL = 2  # seconds between status checks
generation = 0

# Count existing generations to resume
if TRACES.exists():
    generation = sum(1 for _ in TRACES.open())


def extract_code(text: str) -> str | None:
    """Extract Python code from a file that may contain markdown."""
    match = re.search(r"```python\n(.*?)```", text, re.DOTALL)
    if match:
        return match.group(1).strip()
    # If no markdown fences, treat entire content as code
    text = text.strip()
    if text and not text.startswith("```"):
        try:
            ast.parse(text)
            return text
        except SyntaxError:
            return None
    return None


def check_fitness(code: str) -> dict:
    """Test if candidate code is viable."""
    # 1. Must parse
    try:
        ast.parse(code)
    except SyntaxError as e:
        return {"passed": False, "reason": f"SyntaxError: {e}"}

    # 2. Safety scan
    dangerous = ["os.system", "os.popen", "import socket", "import requests",
                 "shutil.rmtree", "__import__", "importlib", "os.kill"]
    for pat in dangerous:
        if pat in code:
            return {"passed": False, "reason": f"Safety: {pat}"}

    # 3. Integrity: must still have the evolution loop
    if "SEED_SANDBOX" not in code:
        return {"passed": False, "reason": "Missing sandbox guard"}
    if "status.md" not in code.lower() and "STATUS" not in code:
        return {"passed": False, "reason": "Missing status communication"}
    if "traces.jsonl" not in code.lower() and "TRACES" not in code:
        return {"passed": False, "reason": "Missing trace logging"}

    # 4. Must run in sandbox without error
    import subprocess, tempfile
    with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False) as f:
        f.write(code)
        tmp = f.name
    try:
        env = {"PATH": os.environ.get("PATH", ""), "SEED_SANDBOX": "1",
               "HOME": "/tmp", "PYTHONPATH": ""}
        r = subprocess.run(["python3", tmp], capture_output=True, text=True,
                           timeout=30, env=env)
        if r.returncode != 0:
            return {"passed": False, "reason": f"Runtime error: {r.stderr[:200]}"}
        return {"passed": True, "reason": "OK"}
    except subprocess.TimeoutExpired:
        return {"passed": False, "reason": "Timeout"}
    finally:
        os.unlink(tmp)


def compute_metrics(code: str) -> dict:
    """Compute code metrics."""
    tree = ast.parse(code)
    return {
        "lines": len(code.splitlines()),
        "functions": sum(1 for n in ast.walk(tree) if isinstance(n, ast.FunctionDef)),
        "classes": sum(1 for n in ast.walk(tree) if isinstance(n, ast.ClassDef)),
        "imports": sum(1 for n in ast.walk(tree) if isinstance(n, (ast.Import, ast.ImportFrom))),
        "ast_nodes": sum(1 for _ in ast.walk(tree)),
    }


def log_trace(gen, fitness, accepted, metrics, diff_size):
    """Append trace to JSONL log."""
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


def wait_for_status(target: str, timeout: int = 300) -> bool:
    """Poll status.md until it matches target or timeout."""
    start = time.time()
    while time.time() - start < timeout:
        if STATUS.exists():
            current = STATUS.read_text().strip()
            if current == target:
                return True
        time.sleep(POLL_INTERVAL)
    return False


# === Main evolution loop ===
print(f"[Seed] Starting at generation {generation}")

while generation < MAX_GENERATIONS:
    source = Path(__file__).read_text()

    # Save current generation snapshot
    snapshot = LINEAGE / f"gen_{generation:04d}.py"
    if not snapshot.exists():
        snapshot.write_text(source)

    # Write source for Claude Code to read, signal "mutate"
    (WORKSPACE / "current_source.py").write_text(source)
    STATUS.write_text("mutate")
    print(f"[Gen {generation}] Requesting mutation...")

    # Wait for Claude Code to write candidate.py and set status to "ready"
    if not wait_for_status("ready", timeout=120):
        print(f"[Gen {generation}] Timeout waiting for mutation")
        log_trace(generation, {"passed": False, "reason": "Mutation timeout"}, False, compute_metrics(source), 0)
        STATUS.write_text("evolving")
        generation += 1
        continue

    # Read candidate
    if not CANDIDATE.exists():
        print(f"[Gen {generation}] No candidate.py found")
        log_trace(generation, {"passed": False, "reason": "No candidate"}, False, compute_metrics(source), 0)
        STATUS.write_text("evolving")
        generation += 1
        continue

    raw = CANDIDATE.read_text()
    candidate = extract_code(raw) or raw.strip()
    CANDIDATE.unlink(missing_ok=True)

    # Test fitness
    fitness = check_fitness(candidate)
    diff = list(difflib.unified_diff(source.splitlines(), candidate.splitlines(), lineterm=""))
    diff_size = len(diff)
    metrics = compute_metrics(candidate) if fitness["passed"] else compute_metrics(source)

    if fitness["passed"]:
        # Accept: overwrite self
        Path(__file__).write_text(candidate)
        print(f"[Gen {generation}] ACCEPTED | LoC: {metrics['lines']} | Funcs: {metrics['functions']} | Diff: {diff_size} lines")
        log_trace(generation, fitness, True, metrics, diff_size)
    else:
        print(f"[Gen {generation}] REJECTED | {fitness['reason']}")
        log_trace(generation, fitness, False, compute_metrics(source), diff_size)

    STATUS.write_text("evolving")
    generation += 1

print(f"[Seed] Finished at generation {generation}")
