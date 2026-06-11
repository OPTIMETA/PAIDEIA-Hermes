"""Canonical ``errors/log.md`` reader/writer for PAIDEIA-Hermes.

The error log is the single source of truth for weakness tracking. Downstream
surfaces (:mod:`pd_status`, :mod:`pd_banner`, :mod:`pd_weakmap`) regex over the
``pattern:`` and ``problem_id:`` keys, so the schema must not drift.
"""
from __future__ import annotations

import datetime
import re
from pathlib import Path

ERROR_TYPES = (
    "pattern-missed",
    "wrong-variable",
    "wrong-end-form",
    "algebraic",
    "sign",
    "definition",
)

# Accept the canonical `pattern:` key and the legacy `pattern_missed_initial:`.
PATTERN_RX = re.compile(r"\b(?:pattern|pattern_missed_initial)\s*:\s*(P\d+)")
_ENTRY_RX = re.compile(r"^\s*-\s+problem_id\s*:", re.MULTILINE)
_MOCK_SOURCE_RX = re.compile(
    r"^\s*source\s*:\s*(?:answers/converted/)?mock[/_]", re.MULTILINE
)
_MOCK_ID_RX = re.compile(r"^\s*problem_id\s*:\s*['\"]?mock[_\-]", re.MULTILINE)


def errors_path(cwd: Path) -> Path:
    return Path(cwd) / "errors" / "log.md"


def read_errors(cwd: Path) -> str:
    p = errors_path(cwd)
    if not p.exists():
        return ""
    try:
        return p.read_text(encoding="utf-8", errors="replace")
    except OSError:
        return ""


def has_entries(text: str) -> bool:
    return bool(_ENTRY_RX.search(text))


def mock_was_graded(text: str) -> bool:
    return bool(_MOCK_SOURCE_RX.search(text) or _MOCK_ID_RX.search(text))


def pattern_counts(text: str) -> dict[str, int]:
    counts: dict[str, int] = {}
    for m in PATTERN_RX.finditer(text):
        counts[m.group(1)] = counts.get(m.group(1), 0) + 1
    return counts


def top_pattern(cwd: Path) -> str | None:
    counts = pattern_counts(read_errors(cwd))
    return max(counts, key=counts.get) if counts else None


def _yaml_escape(s: str) -> str:
    return str(s).replace('"', '\\"').replace("\n", " ").strip()


def append_error(
    cwd: Path,
    *,
    problem_id: str,
    pattern: str,
    error_type: str,
    summary: str,
    source: str,
    date: str | None = None,
) -> Path:
    """Append one canonical YAML entry to ``errors/log.md`` (creating it if needed)."""
    p = errors_path(cwd)
    if not p.exists():
        from . import pd_workspace
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(pd_workspace.ERRORS_LOG_SEED, encoding="utf-8")
    iso = date or datetime.datetime.now(datetime.timezone.utc).replace(
        microsecond=0
    ).isoformat().replace("+00:00", "Z")
    block = (
        f"- problem_id: {_yaml_escape(problem_id)}\n"
        f"  pattern: {_yaml_escape(pattern)}\n"
        f"  error_type: {_yaml_escape(error_type)}\n"
        f'  summary: "{_yaml_escape(summary)}"\n'
        f"  source: {_yaml_escape(source)}\n"
        f"  date: {iso}\n"
    )
    with p.open("a", encoding="utf-8") as fh:
        fh.write("\n" + block)
    return p
