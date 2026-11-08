"""Regression test for BUG-2611080335: the README must unambiguously state the
reference point of the background expiry window.

Reported bug
------------
``README.md`` (Architecture Overview, item 4 "Time-based Expiry") says:

    A background expiry task (running hourly alongside polling) retires
    episodes once they are older than the configured ``expiry_days`` window.

It is **not clear** whether "older" is measured against the episode's *publish*
(broadcast) date or against its *download* date. The bug asks for the README to
clarify this.

The real behaviour (``src/backend/core/expiry.py`` +
``src/backend/db/state.py::get_expired_episodes``) is that expiry is driven by
the ``downloaded_at`` column, which is stamped by ``mark_downloaded`` when the
service first downloads the episode. The BBC publish/broadcast date is never
persisted and never consulted by the expiry task. Therefore the only correct
clarification is that ``expiry_days`` is measured from the episode's **first
download**, and - to dispel the reported publish-vs-download ambiguity - that
this is *distinct from* the programme's publish/broadcast date.

This is a documentation/content (system) test: it pins the exact sentence that
was reported as ambiguous and asserts the clarification is present. It fails
against the current README and passes once the sentence is clarified. No
application code is modified.
"""

from __future__ import annotations

import re
from pathlib import Path

import pytest

# Layout: <repo-root>/app/src/backend/tests/test_readme_expiry_clarification.py
REPO_ROOT = Path(__file__).resolve().parents[4]
README = REPO_ROOT / "README.md"

# The reference point the README must identify: the episode's first download /
# download date (NOT the publish/broadcast date).
DOWNLOAD_ANCHOR = re.compile(
    r"(?i)\b("
    r"first\s+download(?:ed|s)?"
    r"|download(?:ed|s)?\s+(?:date|time|timestamp)"
    r"|downloaded_at"
    r"|date\s+of\s+(?:its\s+|the\s+|their\s+)?download"
    r"|when\s+it\s+was\s+downloaded"
    r"|from\s+(?:its|the|their)\s+download"
    r")\b"
)

# To resolve the reported publish-vs-download ambiguity the clarified sentence
# should also name the publish/broadcast date it is being contrasted with.
PUBLISH_ANCHOR = re.compile(
    r"(?i)\b(publish(?:ed|ing)?|broadcast|air\s*date|original\s*date)\b"
)


def _expiry_task_block(text: str) -> str:
    """Return the README paragraph/bullet describing the background expiry task."""
    lines = text.splitlines()
    start = next(
        (i for i, line in enumerate(lines) if "background expiry task" in line.lower()),
        None,
    )
    assert start is not None, (
        "README.md no longer contains a sentence describing the 'background expiry "
        "task' (BUG-2611080335). The expiry documentation must not be removed."
    )
    block = [lines[start]]
    for line in lines[start + 1 :]:
        stripped = line.strip()
        # A new list item or a blank line ends the paragraph.
        if stripped == "" or re.match(r"^(\d+\.|[-*+])\s", stripped):
            break
        block.append(line)
    return "\n".join(block)


@pytest.mark.req("BUG-2611080335")
def test_readme_expiry_task_states_reference_point():
    """The background expiry description must say what the age is measured from.

    Verifies BUG-2611080335: the README must clarify that ``expiry_days`` is
    measured from the episode's first download (download date), not its publish
    date.
    """
    assert README.is_file(), f"README.md not found at {README}"

    block = _expiry_task_block(README.read_text(encoding="utf-8"))

    assert DOWNLOAD_ANCHOR.search(block), (
        "BUG-2611080335: the README's description of the background expiry task "
        "does not state what the `expiry_days` window is measured against. It "
        "currently says episodes are retired 'once they are older than the "
        "configured `expiry_days` window', which is ambiguous between the "
        "episode's publish date and its download date. Clarify that the window "
        "is measured from the episode's first download (its download date), "
        "which is what `downloaded_at` records and what the expiry task uses.\n\n"
        f"Offending text:\n{block}"
    )

    assert PUBLISH_ANCHOR.search(block), (
        "BUG-2611080335: the README's background expiry description must dispel "
        "the reported publish-vs-download ambiguity by contrasting the download "
        "date with the programme's publish/broadcast date (e.g. 'measured from "
        "the episode's first download, not its publish date').\n\n"
        f"Offending text:\n{block}"
    )
