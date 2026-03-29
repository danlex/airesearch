"""Pattern scanning for dangerous code in candidate mutations."""

import re

DANGEROUS_PATTERNS = [
    # Process execution
    (r"\bos\.system\b", "os.system call"),
    (r"\bos\.popen\b", "os.popen call"),
    (r"\bsubprocess\.Popen\b", "subprocess.Popen"),
    (r"\bsubprocess\.call\b", "subprocess.call"),
    # Network access
    (r"\bimport\s+socket\b", "socket import"),
    (r"\bimport\s+requests\b", "requests import"),
    (r"\bimport\s+urllib\b", "urllib import"),
    (r"\bimport\s+http\b", "http import"),
    (r"\bfrom\s+http\b", "http import"),
    # File destruction
    (r"\bshutil\.rmtree\b", "shutil.rmtree"),
    (r"\bos\.rmdir\b", "os.rmdir"),
    (r"\bos\.unlink\b", "os.unlink"),
    (r"\bos\.remove\b", "os.remove"),
    # Dynamic execution of arbitrary code
    (r"\b__import__\b", "__import__"),
    (r"\bimportlib\b", "importlib"),
    (r"\bcompile\s*\(", "compile()"),
    # System manipulation
    (r"\bos\.environ\b", "os.environ access"),
    (r"\bsys\.exit\b", "sys.exit"),
    (r"\bos\._exit\b", "os._exit"),
    (r"\bos\.kill\b", "os.kill"),
    (r"\bsignal\.\b", "signal module"),
]

# Patterns that are OK in the seed (needed for self-modification)
ALLOWED_PATTERNS = [
    r"subprocess\.run",  # The seed uses this for sandbox testing
    r"open\(__file__\)",  # The seed reads itself
]


def scan_code(code: str) -> list[dict]:
    """Scan code for dangerous patterns. Returns list of violations."""
    violations = []
    for pattern, description in DANGEROUS_PATTERNS:
        matches = re.finditer(pattern, code)
        for match in matches:
            # Check if this match is in an allowed pattern context
            line_start = code.rfind("\n", 0, match.start()) + 1
            line_end = code.find("\n", match.end())
            line = code[line_start:line_end if line_end != -1 else len(code)]

            is_allowed = any(re.search(ap, line) for ap in ALLOWED_PATTERNS)
            if not is_allowed:
                line_num = code[:match.start()].count("\n") + 1
                violations.append({
                    "pattern": description,
                    "line": line_num,
                    "code": line.strip(),
                })
    return violations


def is_safe(code: str) -> tuple[bool, list[dict]]:
    """Check if code is safe to execute. Returns (safe, violations)."""
    violations = scan_code(code)
    return len(violations) == 0, violations
