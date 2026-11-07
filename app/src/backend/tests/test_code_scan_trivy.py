"""Regression test for BUG-2611061737: the build pipeline must complete.

The ``build_container.sh`` pipeline aborts in the ``Code Scanning`` stage of
``make code-scan``. The prior fix (commit 199a443) only addressed the
Software Composition Analysis (SCA) sub-step: ``pip-audit`` now reports no
known vulnerabilities, and ``bandit`` is clean. The stage still fails on the
next command of the same Makefile target:

    trivy config --exit-code 1 --quiet .

``trivy config`` performs Dockerfile/Infrastructure-as-Code misconfiguration
scanning relative to the CIS Docker Benchmark. The company security-testing
standard (``docs/standards/security-testing.md``) mandates that the container
image must NOT run as ``root`` and that the container configuration must be
secure, and the Code Scanning stage must block the build on any findings.

The repository currently ships two Dockerfiles whose only `FROM` uses the
floating ``:latest`` tag and which never declare a non-root ``USER``:

    ./Dockerfile
    ./app/scripts/Dockerfile.test

``trivy config`` therefore reports (per file) DS-0001 (MEDIUM), DS-0002
(HIGH) and DS-0026 (LOW). DS-0001 (floating ``:latest`` tag) is **intentionally
ignored by policy** in ``.trivyignore``: the base is a rolling ``:latest`` so
every build picks up security fixes, and pinned bases are forbidden. The
actionable requirements are therefore DS-0002 (non-root ``USER``) and DS-0026
(``HEALTHCHECK``). This test pins that gate as an executable requirement so the
build cannot silently regress.
"""

from __future__ import annotations

import shutil
import subprocess
from pathlib import Path

import pytest

# Repository layout: <repo-root>/app/src/backend/tests/test_code_scan_trivy.py
REPO_ROOT = Path(__file__).resolve().parents[4]


def _run(cmd: list[str]) -> subprocess.CompletedProcess[str]:
    """Run a command from the repository root (as the Makefile does)."""
    return subprocess.run(
        cmd,
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
    )


@pytest.mark.req("BUG-2611061737")
def test_trivy_config_finds_no_dockerfile_misconfigurations():
    """Reproduces BUG-2611061737: ``trivy config`` must pass.

    This is the command in the ``make code-scan`` stage that terminates
    ``build_container.sh``. It fails today because the shipped Dockerfiles
    use a floating ``FROM`` tag and declare no non-root ``USER`` (and no
    ``HEALTHCHECK``), which ``trivy`` reports as DS-0001/DS-0002/DS-0026.
    """
    if shutil.which("trivy") is None:
        pytest.skip("trivy is not installed in this environment")

    result = _run(
        [
            "trivy",
            "config",
            "--exit-code",
            "1",
            "--quiet",
            ".",
        ]
    )

    assert result.returncode == 0, (
        "trivy config found Dockerfile misconfigurations (non-zero exit). "
        "This is the failure that halts `build_container.sh` at the Code "
        "Scanning stage (BUG-2611061737). The shipped Dockerfiles must run as a "
        "non-root USER and declare a HEALTHCHECK (DS-0001 for the rolling "
        ":latest base is intentionally ignored by policy).\n\n"
        f"stdout:\n{result.stdout}\n\nstderr:\n{result.stderr}"
    )
