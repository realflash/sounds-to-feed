"""Regression test for BUG-2611061737: the whole build pipeline must complete.

``build.sh`` -> ``build_container.sh`` runs five stages and stops at the first
failure:

   1. Linting                -> ``make lint-backend``
   2. Unit & Integration     -> ``make test-backend``
   3. Code Scanning          -> ``make code-scan``
   4. Building (Container)   -> ``make build-container``   (needs Docker)
   5. Container Security     -> ``make container-scan``    (needs Docker)

Stages 1-3 are exercised directly by the other tests in this directory
(``test_code_scan_policy.py``, ``test_code_scan_trivy.py``,
``test_build_dependencies.py``) and run in the Docker-free builder.

Stages 4-5 need a Docker daemon and therefore run in the trusted builder, so
they cannot be executed from here. What *can* be asserted here, and what the
rejected fix got wrong, is the contract those stages depend on:

* The last human UAT run failed ``make container-scan`` (``trivy image
  --exit-code 1 --ignore-unfixed``) because the final image still shipped the
  base's statically linked ``uv``/``uvx`` Rust binaries, whose embedded
  ``rustls`` is flagged as fixed-vulnerable:

      GHSA-c8m5-c952-6cm4  rustls: Debug formatting leaks TLS secrets/PSKs
      GHSA-h2v8-394m-p7vv  rustls: Brotli cert decompression amplification
      GHSA-vp88-798v-h67f  rustls: ECH rejection exposes buffered app data
      GHSA-w44r-93j7-qv28  rustls: ServerHello poisons per-name key exchange

  The product cannot patch a pre-built base binary, and ``uv`` is a *build*
  dependency (the dependency stage installs the Python deps into system
  Python), so the final stage must remove it before hardening/scanning.

* The container scan gate itself must keep failing the build on unignored,
  fixable findings (``--exit-code 1 --ignore-unfixed``), per the company
  security-testing standard.

These tests pin that contract so the pipeline cannot silently regress again.
"""

from __future__ import annotations

import re
from pathlib import Path

import pytest

# Repository layout: <repo-root>/app/src/backend/tests/test_build_pipeline_completes.py
REPO_ROOT = Path(__file__).resolve().parents[4]
DOCKERFILE = REPO_ROOT / "Dockerfile"
MAKEFILE = REPO_ROOT / "Makefile"
BUILD_CONTAINER = REPO_ROOT / "build_container.sh"

# The Rust binaries the standard base installs (shipped as rustbinary by trivy).
UV_BINARIES = ("/usr/local/bin/uv", "/usr/local/bin/uvx")


def _final_stage(dockerfile_text: str) -> str:
    """Return the text of the last build stage (the scanned/shipped image)."""
    stages = re.split(r"(?mi)^FROM\s", dockerfile_text)
    assert len(stages) > 1, "Dockerfile has no FROM instruction"
    return "FROM " + stages[-1]


@pytest.mark.req("BUG-2611061737")
def test_final_image_drops_the_uv_rust_binaries():
    """The shipped image must not contain the vulnerable ``uv``/``uvx`` binaries.

    ``trivy image --exit-code 1 --ignore-unfixed`` (``make container-scan``)
    flagged both Rust binaries inherited from the base. They are build-only
    tooling, so the final stage removes them before ``attono-harden``.
    """
    final_stage = _final_stage(DOCKERFILE.read_text())

    for binary in UV_BINARIES:
        assert binary in final_stage, (
            f"The final image stage must remove {binary}: it is a statically "
            "linked Rust binary whose embedded rustls is flagged as "
            "fixed-vulnerable by `trivy image`, which fails `make "
            "container-scan` (BUG-2611061737). It is also unused at runtime."
        )

    # It must be a *removal*, not a copy/install.
    assert re.search(r"(?m)^RUN\s+rm\s+-f\s+[^\n]*/usr/local/bin/uv\b", final_stage), (
        "The final stage must `rm -f` the uv/uvx binaries (a COPY/install of "
        "them would keep the vulnerable rustls in the scanned image)."
    )

    # And the removal has to happen before hardening strips the shell.
    assert final_stage.index("rm -f") < final_stage.index("attono-harden"), (
        "uv/uvx must be removed BEFORE `attono-harden`, which deletes /bin/sh "
        "and therefore makes any later RUN impossible."
    )


@pytest.mark.req("BUG-2611061737")
def test_container_scan_gate_fails_on_fixable_findings():
    """``make container-scan`` must keep blocking on unignored fixed findings."""
    container_scan = re.search(
        r"(?ms)^container-scan:.*?(?=^\S|\Z)", MAKEFILE.read_text()
    )
    assert container_scan is not None, "Makefile has no `container-scan` target"
    target = container_scan.group(0)

    assert "--exit-code 1" in target, (
        "`make container-scan` must pass `--exit-code 1` so findings fail the "
        "build (security-testing.md §1.3)."
    )
    assert "--ignore-unfixed" in target, (
        "`make container-scan` must pass `--ignore-unfixed` so unfixable "
        "findings do not fail the build while fixable ones do "
        "(security-testing.md §1.3)."
    )


@pytest.mark.req("BUG-2611061737")
def test_pipeline_script_runs_every_stage():
    """``build_container.sh`` must still gate each stage on the previous one."""
    script = BUILD_CONTAINER.read_text()

    for stage in (
        "make lint-backend",
        "make test-backend",
        "make code-scan",
        "make build-container",
        "make container-scan",
    ):
        assert stage in script, f"build_container.sh no longer runs `{stage}`"
