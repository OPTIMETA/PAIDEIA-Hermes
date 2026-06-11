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

GITIGNORE = """\
# PAIDEIA-Hermes
**/_pages/
**/.tmp-*/
*.tmp
__pycache__/
*.pyc
.DS_Store
"""

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
        log.parent.mkdir(parents=True, exist_ok=True)
        log.write_text(ERRORS_LOG_SEED, encoding="utf-8")
        seeded_log = True

    gi = cwd / ".gitignore"
    if not gi.exists():
        gi.write_text(GITIGNORE, encoding="utf-8")

    ctx = cwd / "PAIDEIA.md"
    if not ctx.exists():
        ctx.write_text(
            _CONTEXT_TEMPLATE.format(
                course=meta.get("COURSE_NAME", "course"),
                exam=meta.get("EXAM_DATE", "?"),
                etype=meta.get("EXAM_TYPE", "exam"),
                lang=meta.get("INTERFACE_LANG", "en"),
            ),
            encoding="utf-8",
        )

    return {
        "created_dirs": created,
        "seeded_log": seeded_log,
        "meta_path": str(cwd / ".course-meta"),
    }
