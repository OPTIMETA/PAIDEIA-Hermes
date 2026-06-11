"""Phase detection + the one-line status string for `/paideia status`.

Phases (artifact/activity-derived, not time-derived):
  setup - course-index/patterns.md absent
  diag  - patterns exist, but no quiz problems yet or no graded error yet
  drill - quiz problems exist AND errors/log.md has >=1 graded entry
  mock  - a mock exam has been graded
  cram  - cheatsheet/final.{md,pdf} present
  cool  - D-0 (exam day) overrides all
"""
from __future__ import annotations

import glob
from pathlib import Path

from . import pd_errlog, pd_meta, pd_weakmap


def _quiz_problems_exist(cwd: Path) -> bool:
    for p in glob.glob(str(Path(cwd) / "quizzes" / "*.md")):
        if not p.endswith("_answers.md"):
            return True
    return False


def detect_phase(cwd: Path, days: int | None) -> str:
    cwd = Path(cwd)
    if days == 0:
        return "cool"
    cheat = cwd / "cheatsheet"
    if (cheat / "final.pdf").exists() or (cheat / "final.md").exists():
        return "cram"
    log_text = pd_errlog.read_errors(cwd)
    if pd_errlog.mock_was_graded(log_text):
        return "mock"
    if not (cwd / "course-index" / "patterns.md").exists():
        return "setup"
    if _quiz_problems_exist(cwd) and pd_errlog.has_entries(log_text):
        return "drill"
    return "diag"


def _truncate(name: str, limit: int = 28) -> str:
    name = name.strip()
    return name if len(name) <= limit else name[: limit - 1].rstrip() + "…"


def render_status(cwd: Path) -> str:
    """One-line status, e.g. ``paideia · Complex Analysis · D-12 · drill · P5 ↑``."""
    cwd = Path(cwd)
    meta = pd_meta.parse_meta(cwd)
    if not meta:
        return "paideia · (not a course folder — run `/paideia init` here)"
    name = _truncate(meta.get("COURSE_NAME", "course") or "course")
    days = pd_meta.days_until(meta.get("EXAM_DATE", ""))
    phase = detect_phase(cwd, days)
    miss = pd_weakmap.top_miss(cwd)

    parts = ["paideia", name]
    d = pd_meta.fmt_days(days)
    if d:
        parts.append(d)
    parts.append(phase)
    if miss:
        parts.append(f"{miss} ↑")
    return " · ".join(parts)
