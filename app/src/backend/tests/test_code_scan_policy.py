"""Regression test for BUG-2611061737: the `make code-scan` stage must pass.

The product build (build.sh -> build_container.sh) aborts in the Docker-free
`make code-scan` stage, the security gate mandated by the company
security-testing standard (docs/standards/security-testing.md).

`make code-scan` aggregates four sub-steps, any non-zero exit of which halts
the build:

  1. ``pip-audit``      - Software Composition Analysis of shipped deps
  2. ``bandit``         - Python Static Application Security Testing
  3. ``semgrep``        - source Static Application Security Testing
  4. ``trivy config``   - Infrastructure-as-Code / Dockerfile misconfiguration

This test pins the whole target as an executable requirement so the build
cannot silently regress.
"""

from __future__ import annotations

import shutil
import subprocess
from pathlib import Path

import pytest

# Layout: <repo-root>/app/src/backend/tests/test_code_scan_policy.py
REPO_ROOT = Path(__file__).resolve().parents[4]


def _run(cmd: str) -> subprocess.CompletedProcess[str]:
    """Run a shell command from the repository root (as the Makefile does)."""
    return subprocess.run(
        cmd,
        cwd=REPO_ROOT,
        shell=True,
        capture_output=True,
        text=True,
    )


@pytest.mark.req("BUG-2611061737")
def test_code_scan_stage_passes():
    """``make code-scan`` must complete with a zero exit code.

    This is the stage that terminates ``build_container.sh``. It aggregates the
    SCA (pip-audit), SAST (bandit, semgrep) and IaC (trivy config) gates, so a
    single failure here stops the whole build.
    """
    for tool in ("make", "uv", "semgrep", "trivy"):
        if shutil.which(tool) is None:
            pytest.skip(f"{tool} is not installed in this environment")

    result = _run("make code-scan")

    assert result.returncode == 0, (
        "`make code-scan` failed (non-zero exit). This is the failure that "
        "halts `build_container.sh` at the Code Scanning stage "
        "(BUG-2611061737).\n\n"
        f"stdout:\n{result.stdout}\n\nstderr:\n{result.stderr}"
    )
