"""Isolated ephemeral code runner for sandbox recipe verification."""

from __future__ import annotations

import subprocess
import sys
import time
from .models import SandboxResult


def run_code_in_sandbox(code: str, language: str = "python", timeout_s: int = 15) -> SandboxResult:
    """Execute code snippet in an isolated ephemeral process."""
    started = time.time()
    if language.lower() not in ("python", "py"):
        return SandboxResult(
            success=False,
            language=language,
            code=code,
            stderr=f"Unsupported language '{language}'. Only 'python' is supported in pilot.",
            returncode=1,
            ms=0,
        )

    try:
        p = subprocess.run(
            [sys.executable, "-c", code],
            capture_output=True,
            text=True,
            timeout=timeout_s,
        )
        elapsed_ms = int((time.time() - started) * 1000)
        return SandboxResult(
            success=p.returncode == 0,
            language=language,
            code=code,
            stdout=p.stdout,
            stderr=p.stderr,
            returncode=p.returncode,
            ms=elapsed_ms,
        )
    except subprocess.TimeoutExpired:
        elapsed_ms = int((time.time() - started) * 1000)
        return SandboxResult(
            success=False,
            language=language,
            code=code,
            stderr=f"Sandbox execution timed out after {timeout_s}s",
            returncode=124,
            ms=elapsed_ms,
        )
    except Exception as e:
        elapsed_ms = int((time.time() - started) * 1000)
        return SandboxResult(
            success=False,
            language=language,
            code=code,
            stderr=f"{type(e).__name__}: {e}",
            returncode=1,
            ms=elapsed_ms,
        )
