"""Session-start banner (D-N · phase · top-miss/verdict), bilingual en/ko.

Printed to stderr by the ``on_session_start`` hook when the agent opens a
session inside a PAIDEIA course folder. Silent (None) when CWD is not a course.
Replaces upstream PAIDEIA's Claude Code SessionStart hook.
"""
from __future__ import annotations

from pathlib import Path

from . import pd_errlog, pd_meta, pd_status, pd_weakmap

_MSG: dict[str, dict[str, str]] = {
    "exam_day":  {"en": " — exam day", "ko": " — 시험 당일"},
    "exam_past": {"en": " — D+{n} (past exam)", "ko": " — D+{n} (시험 지남)"},
    "top_miss":  {"en": "  top-miss pattern: {p} — /paideia blind  or  /paideia pattern {p}",
                  "ko": "  최다 실수 패턴: {p} — /paideia blind  또는  /paideia pattern {p}"},
    "next_setup": {"en": "  next: fill materials/ then /paideia ingest → /paideia analyze",
                   "ko": "  다음: materials/ 채우고 /paideia ingest → /paideia analyze"},
    "next_diag":  {"en": "  next: run a diagnostic with /paideia quiz all 20",
                   "ko": "  다음: /paideia quiz all 20 으로 진단 돌리기"},
    "next_drill": {"en": "  next: /paideia weakmap, then /paideia quiz weakmap",
                   "ko": "  다음: /paideia weakmap 후 /paideia quiz weakmap"},
    "next_mock":  {"en": "  next: /paideia cheatsheet --pdf to start the summary",
                   "ko": "  다음: /paideia cheatsheet --pdf 로 요약 시작"},
    "next_cram":  {"en": "  next: re-read /paideia weakmap; don't learn anything new",
                   "ko": "  다음: /paideia weakmap 재열람, 새로운 건 배우지 말 것"},
}


def t(key: str, lang: str, **kw: object) -> str:
    bundle = _MSG.get(key, {})
    template = bundle.get(lang) or bundle.get("en", key)
    return template.format(**kw) if kw else template


def _format_d(days: int | None, lang: str) -> str:
    if days is None:
        return ""
    if days == 0:
        return t("exam_day", lang)
    if days > 0:
        return f" — D-{days}"
    return t("exam_past", lang, n=-days)


def render_banner(cwd: Path) -> str | None:
    cwd = Path(cwd)
    meta = pd_meta.parse_meta(cwd)
    if not meta:
        return None

    name = meta.get("COURSE_NAME", "course")
    lang = meta.get("INTERFACE_LANG", "en").strip().lower()
    if lang not in ("en", "ko"):
        lang = "en"
    days = pd_meta.days_until(meta.get("EXAM_DATE", ""))
    phase = pd_status.detect_phase(cwd, days)
    verdict = pd_weakmap.latest_verdict(cwd)

    lines = [f"[paideia] {name}{_format_d(days, lang)} · phase={phase}"]
    if verdict:
        lines.append(f"  weakmap verdict: {verdict}")
    else:
        top = pd_errlog.top_pattern(cwd)
        if top:
            lines.append(t("top_miss", lang, p=top))
        else:
            key = {
                "setup": "next_setup", "diag": "next_diag", "drill": "next_drill",
                "mock": "next_mock", "cram": "next_cram",
            }.get(phase)
            if key:
                lines.append(t(key, lang))
    return "\n".join(lines)
