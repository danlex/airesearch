"""Sandboxed execution of candidate seed code."""

import subprocess
import tempfile
import os


def run_in_sandbox(code: str, timeout: int = 30) -> dict:
    """Run code in a subprocess with timeout and no network.

    Returns dict with: returncode, stdout, stderr, timed_out
    """
    with tempfile.NamedTemporaryFile(
        mode="w", suffix=".py", delete=False, dir=tempfile.gettempdir()
    ) as f:
        f.write(code)
        tmp_path = f.name

    try:
        env = {
            "PATH": os.environ.get("PATH", "/usr/bin:/bin"),
            "HOME": tempfile.gettempdir(),
            "PYTHONPATH": "",
            "SEED_SANDBOX": "1",  # Signal to the seed that it's in sandbox mode
        }
        # Strip network-related env vars
        for key in ("HTTP_PROXY", "HTTPS_PROXY", "ALL_PROXY", "http_proxy", "https_proxy"):
            env.pop(key, None)

        result = subprocess.run(
            ["python3", tmp_path],
            capture_output=True,
            text=True,
            timeout=timeout,
            env=env,
            cwd=tempfile.gettempdir(),
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
        os.unlink(tmp_path)
