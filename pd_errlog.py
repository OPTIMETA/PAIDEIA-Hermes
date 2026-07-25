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


_CTRL_RX = re.compile(r"[\x00-\x1f\x7f]+")
# Chars that flip a plain YAML scalar into some other node type when leading.
_PLAIN_LEAD = "\"'&*!|>%@`-?,[]{}#"
# Bare tokens YAML resolves to something that is not a string. `=` is the sharp
# one: it carries the yaml.org,2002:value tag and makes SafeLoader *raise*,
# taking the whole log down with it. `~`/`null` silently become None. None of
# them carry usable identifier information, so they degrade to the same
# placeholder an all-punctuation value gets.
#
# Number- and boolean-shaped tokens (`3`, `no`) are deliberately left alone:
# they parse cleanly, `problem_id: 3` is a realistic entry, and every reader in
# this plugin matches the raw text rather than the resolved type.
_YAML_DEGENERATE = frozenset({"=", "~", "null", "Null", "NULL"})


def _yaml_plain(s: str) -> str:
    """Sanitize a value emitted as a *plain* (unquoted) YAML scalar.

    ``problem_id``/``pattern``/``error_type``/``source`` must stay unquoted:
    :data:`PATTERN_RX` matches ``pattern: P3`` and would miss ``pattern: "P3"``,
    which silently drops the entry from every weakness surface. So sanitize the
    few constructs that would end the scalar early rather than quote it.
    """
    s = _CTRL_RX.sub(" ", str(s))
    s = re.sub(r"\s+", " ", s).strip()
    s = re.sub(r":(?=\s|$)", "-", s)      # `: ` (and a trailing `:`) ends the scalar
    s = re.sub(r"(?<=\s)#", "", s)        # ` #` starts a trailing comment
    # Alternate until stable. A single lstrip-then-strip is not enough: given
    # "' [x", it removes the quote, halts at the space, and the trailing strip
    # then re-exposes "[" as the new first character.
    prev = None
    while prev != s:
        prev = s
        s = s.lstrip(_PLAIN_LEAD).strip()
    if not s or s in _YAML_DEGENERATE:
        return "unknown"
    return s


def _yaml_quoted(s: str) -> str:
    """Escape *s* for a YAML double-quoted scalar.

    Backslash MUST be escaped before the quote. Summaries describe math, so they
    carry LaTeX (``\\int``, ``\\frac``) and YAML rejects unknown escapes like
    ``\\i`` outright — one unescaped summary makes the *whole* ``errors/log.md``
    unparseable, not just its own entry.
    """
    s = _CTRL_RX.sub(" ", str(s))
    s = s.replace("\\", "\\\\").replace('"', '\\"')
    return re.sub(r"\s+", " ", s).strip()


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
        from . import pd_meta, pd_workspace
        pd_meta.atomic_write_text(p, pd_workspace.ERRORS_LOG_SEED)
    iso = date or datetime.datetime.now(datetime.timezone.utc).replace(
        microsecond=0
    ).isoformat().replace("+00:00", "Z")
    block = (
        f"- problem_id: {_yaml_plain(problem_id)}\n"
        f"  pattern: {_yaml_plain(pattern)}\n"
        f"  error_type: {_yaml_plain(error_type)}\n"
        f'  summary: "{_yaml_quoted(summary)}"\n'
        f"  source: {_yaml_plain(source)}\n"
        f"  date: {_yaml_plain(iso)}\n"
    )
    with p.open("a", encoding="utf-8") as fh:
        fh.write("\n" + block)
    return p
