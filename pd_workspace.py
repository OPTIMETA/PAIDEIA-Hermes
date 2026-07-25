"""Course-folder layout + scaffolding for PAIDEIA-Hermes.

The on-disk data model is identical to upstream PAIDEIA so artifacts are
portable between the Claude Code plugin and this hermes-agent port.
"""
from __future__ import annotations

from pathlib import Path

from . import pd_meta

# Directory skeleton created by `/paideia init`.
SKELETON = (
    "materials/lectures",
    "materials/textbook",
    "materials/homework",
    "materials/solutions",
    "converted/lectures",
    "converted/textbook",
    "converted/homework",
    "converted/solutions",
    "course-index",
    "quizzes",
    "mock",
    "twins",
    "chain",
    "derivations",
    "cheatsheet",
    "weakmap",
    "answers/converted",
    "answers/_archive",
    "errors",
)

ERRORS_LOG_SEED = """\
# Error log

<!-- Append-only YAML entries. Schema:
- problem_id: <id>
  pattern: <Pk>
  error_type: pattern-missed | wrong-variable | wrong-end-form | algebraic | sign | definition
  summary: "<1 line>"
  source: <answers/converted/<name>.md | blind/<id> | chain/<ts>>
  date: <ISO8601>
-->
"""

# Patterns the course folder must ignore. `answers/_archive/` is load-bearing:
# `/paideia grade` moves every graded scan there, and the grade spec promises the
# user those bulky, personal PDFs stay out of version control while the converted
# markdown trail is committed.
GITIGNORE_PATTERNS = (
    "**/_pages/",
    "**/.tmp-*/",
    "*.tmp",
    "answers/_archive/",
    "__pycache__/",
    "*.pyc",
    ".DS_Store",
)

GITIGNORE = "# PAIDEIA-Hermes\n" + "".join(f"{p}\n" for p in GITIGNORE_PATTERNS)

_CONTEXT_TEMPLATE = """\
# {course} — PAIDEIA-Hermes workspace

This folder is a PAIDEIA exam-prep workspace driven by the `/paideia` plugin
for hermes-agent. Exam: **{exam}** ({etype}). Language: **{lang}**.

## Workflow
1. Drop course PDFs into `materials/{{lectures,textbook,homework,solutions}}/`.
2. `/paideia ingest`  — transcribe PDFs to LaTeX markdown in `converted/`.
3. `/paideia analyze` — build `course-index/` (summary, patterns, coverage).
4. Drill: `/paideia quiz <topic> N`, `/paideia blind <id>`, `/paideia twin <id>`,
   `/paideia chain`, `/paideia mock`.
5. Solve on paper, scan to `answers/`, then `/paideia grade`.
6. `/paideia weakmap` → `/paideia quiz weakmap` → `/paideia cheatsheet --pdf`.

`/paideia status` shows D-N + phase + top-miss pattern at any time.
`/paideia doctor` diagnoses the install and this workspace.

HW density is the primary exam-probability signal: drill 🔥🔥/🔥 sections,
not ⚪ low-risk ones.
"""


def is_course(cwd: Path) -> bool:
    """True iff *cwd* is a PAIDEIA course folder (has ``.course-meta``)."""
    return (Path(cwd) / ".course-meta").exists()


def ensure_dirs(cwd: Path) -> list[str]:
    """Create the skeleton; return the relative paths that were newly created."""
    created: list[str] = []
    for rel in SKELETON:
        d = Path(cwd) / rel
        if not d.exists():
            d.mkdir(parents=True, exist_ok=True)
            created.append(rel)
    return created


def ensure_gitignore(cwd: Path) -> list[str]:
    """Append any missing :data:`GITIGNORE_PATTERNS` to ``.gitignore``.

    Appending rather than skipping-if-present matters because scaffolding is
    re-runnable: a course created before a pattern existed would otherwise never
    pick it up, and the user would commit scans that the grade spec told them
    were ignored. Existing lines are left untouched.
    """
    gi = Path(cwd) / ".gitignore"
    if not gi.exists():
        pd_meta.atomic_write_text(gi, GITIGNORE)
        return list(GITIGNORE_PATTERNS)
    try:
        current = gi.read_text(encoding="utf-8", errors="replace")
    except OSError:
        return []
    have = {line.strip() for line in current.splitlines()}
    missing = [p for p in GITIGNORE_PATTERNS if p not in have]
    if missing:
        parts = []
        if current and not current.endswith("\n"):
            parts.append("\n")
        if current.strip():
            parts.append("\n")          # blank line between their rules and ours
        parts.append("# PAIDEIA-Hermes\n")
        parts.extend(f"{p}\n" for p in missing)
        pd_meta.atomic_write_text(gi, current + "".join(parts))
    return missing


def scaffold_course(cwd: Path, meta: dict[str, str]) -> dict[str, object]:
    """Idempotently create the course skeleton, ``.course-meta`` and seeds.

    Returns a small report dict for the caller to render.
    """
    cwd = Path(cwd)
    created = ensure_dirs(cwd)

    pd_meta.write_meta(cwd, meta)

    log = cwd / "errors" / "log.md"
    seeded_log = False
    if not log.exists():
        pd_meta.atomic_write_text(log, ERRORS_LOG_SEED)
        seeded_log = True

    ignored = ensure_gitignore(cwd)

    ctx = cwd / "PAIDEIA.md"
    if not ctx.exists():
        pd_meta.atomic_write_text(
            ctx,
            _CONTEXT_TEMPLATE.format(
                course=meta.get("COURSE_NAME", "course"),
                exam=meta.get("EXAM_DATE", "?"),
                etype=meta.get("EXAM_TYPE", "exam"),
                lang=meta.get("INTERFACE_LANG", "en"),
            ),
        )

    return {
        "created_dirs": created,
        "seeded_log": seeded_log,
        "gitignore_added": ignored,
        "meta_path": str(cwd / ".course-meta"),
    }
