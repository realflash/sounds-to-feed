"""Regression tests for BUG-2611061737: the build pipeline must complete.

The failing build reported under BUG-2611061737 aborts in the
``Code Scanning`` stage of ``build_container.sh`` (``make code-scan``).
The first command of that stage performs a Software Composition Analysis
(SCA) check of the *shipped runtime* dependency set:

    cd app && uv export --no-dev --format requirements-txt | uv run pip-audit -r /dev/stdin

Per the company security-testing standard, any known (fixed) vulnerability
in a shipped dependency MUST fail the build. Because the CI/CD pipeline is
"local-first" and driven by ``make``, a vulnerable lockfile therefore makes
``build_container.sh`` exit non-zero and the build never completes.

These tests pin the SCA gate as an executable requirement so the build
cannot silently regress: if an audit reports any known vulnerability in the
shipped dependency set, the build is broken and these tests fail.
"""

from __future__ import annotations

import subprocess
from pathlib import Path

import pytest

# Repository layout: <repo-root>/app/src/backend/tests/test_build_dependencies.py
REPO_ROOT = Path(__file__).resolve().parents[4]
APP_DIR = REPO_ROOT / "app"


def _run(cmd: str) -> subprocess.CompletedProcess[str]:
    """Run a shell command from the ``app`` directory (as the Makefile does)."""
    return subprocess.run(
        cmd,
        cwd=APP_DIR,
        shell=True,
        capture_output=True,
        text=True,
    )


@pytest.mark.req("BUG-2611061737")
def test_shipped_dependencies_have_no_known_vulnerabilities():
    """SCA gate: the shipped dependency set must be free of known CVEs.

    Reproduces BUG-2611061737: this is the first command of the
    ``make code-scan`` stage that terminates ``build_container.sh``.
    """
    result = _run(
        "uv export --no-dev --format requirements-txt "
        "| uv run pip-audit -r /dev/stdin"
    )

    assert result.returncode == 0, (
        "SCA (pip-audit) found known vulnerabilities in the shipped "
        "dependency set. This is the failure that halts `build_container.sh` "
        "at the Code Scanning stage (BUG-2611061737).\n\n"
        f"stdout:\n{result.stdout}\n\nstderr:\n{result.stderr}"
    )
