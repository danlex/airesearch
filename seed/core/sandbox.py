"""Sandboxed execution of candidate seed code."""

import subprocess
import tempfile
import os


def run_in_sandbox(code: str, timeout: int = 30) -> dict:
    """Run code in a restricted subprocess with timeout.

    Isolation measures:
    - Runs in an isolated temp directory (no access to project files)
    - Minimal PATH (only python3)
    - No PYTHONPATH (can't import project modules)
    - Proxy env vars stripped (no network via proxy)
    - HOME set to temp dir

    Limitations (documented):
    - Not a kernel-level sandbox (no seccomp/chroot on macOS without Docker)
    - Network access is restricted by env stripping, not blocked at syscall level
    - For production use, run inside Docker or a VM
    """
    import shutil

    # Create isolated temp directory — candidate can only see its own file
    sandbox_dir = tempfile.mkdtemp(prefix="seed_sandbox_")
    candidate_path = os.path.join(sandbox_dir, "candidate.py")

    try:
        with open(candidate_path, "w") as f:
            f.write(code)

        env = {
            "PATH": "/usr/bin:/bin",
            "HOME": sandbox_dir,
            "TMPDIR": sandbox_dir,
            "PYTHONPATH": "",
            "PYTHONDONTWRITEBYTECODE": "1",
            "SEED_SANDBOX": "1",
        }

        result = subprocess.run(
            ["python3", candidate_path],
            capture_output=True,
            text=True,
            timeout=timeout,
            env=env,
            cwd=sandbox_dir,  # Candidate's cwd is the isolated directory
        )
        return {
            "returncode": result.returncode,
            "stdout": result.stdout[:2000],
            "stderr": result.stderr[:2000],
            "timed_out": False,
        }
    except subprocess.TimeoutExpired:
        return {
            "returncode": -1,
            "stdout": "",
            "stderr": f"Timed out after {timeout}s",
            "timed_out": True,
        }
    finally:
        shutil.rmtree(sandbox_dir, ignore_errors=True)
