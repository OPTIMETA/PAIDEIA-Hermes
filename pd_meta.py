"""``.course-meta`` parsing/writing for PAIDEIA-Hermes.

A course folder is identified by a ``.course-meta`` file at its root. The
format is one ``KEY: value`` pair per line (six canonical keys). A trailing
``# comment`` on any value is stripped — every parser in this plugin
(:mod:`pd_status`, :mod:`pd_banner`, :mod:`pd_doctor`, :mod:`pd_vision_ocr`)
must agree on this, so the regex lives here and the standalone scripts keep a
byte-identical copy.
"""
from __future__ import annotations

import datetime
import re
from pathlib import Path

# Canonical key order — write_meta() emits keys in exactly this order.
META_KEYS = (
    "COURSE_NAME",
    "EXAM_DATE",
    "EXAM_TYPE",
    "USER_WEAK_ZONES",
    "OCR_ENGINE",
    "INTERFACE_LANG",
)

VALID_OCR = ("claude", "ollama", "tesseract")
VALID_LANG = ("en", "ko")

_META_LINE_RX = re.compile(r"^\s*([A-Z_][A-Z0-9_]*)\s*:\s*(.+?)\s*$")


def parse_meta(cwd: Path) -> dict[str, str]:
    """Parse ``.course-meta`` in *cwd*. Returns {} if absent/unreadable."""
    meta: dict[str, str] = {}
    p = Path(cwd) / ".course-meta"
    if not p.exists():
        return meta
    try:
        for line in p.read_text(encoding="utf-8", errors="replace").splitlines():
            m = _META_LINE_RX.match(line)
            if m:
                # Strip a trailing `# comment` so a hand-edited
                # `COURSE_NAME: Complex Analysis  # main` doesn't leak the note.
                meta[m.group(1)] = m.group(2).split("#", 1)[0].strip()
    except OSError:
        pass
    return meta


def write_meta(cwd: Path, meta: dict[str, str]) -> Path:
    """Write ``.course-meta`` with canonical keys in canonical order.

    Unknown keys are appended after the canonical block so a hand-added field
    survives a rewrite.
    """
    lines: list[str] = []
    for k in META_KEYS:
        lines.append(f"{k}: {meta.get(k, '').strip()}")
    for k, v in meta.items():
        if k not in META_KEYS:
            lines.append(f"{k}: {str(v).strip()}")
    p = Path(cwd) / ".course-meta"
    p.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return p


def read_lang(cwd: Path) -> str:
    """Return INTERFACE_LANG ('en'|'ko'), defaulting to 'en'."""
    lang = parse_meta(cwd).get("INTERFACE_LANG", "en").strip().lower()
    return lang if lang in VALID_LANG else "en"


def read_ocr_engine(cwd: Path) -> str:
    eng = parse_meta(cwd).get("OCR_ENGINE", "claude").strip().lower()
    return eng if eng in VALID_OCR else "claude"


def days_until(exam_date: str) -> int | None:
    """Days from today until *exam_date* (YYYY-MM-DD). None if unparseable."""
    try:
        d = datetime.datetime.strptime((exam_date or "").strip(), "%Y-%m-%d").date()
    except (ValueError, AttributeError):
        return None
    return (d - datetime.date.today()).days


def fmt_days(days: int | None) -> str | None:
    """'D-5' / 'D-0' / 'D+3' (or None)."""
    if days is None:
        return None
    if days == 0:
        return "D-0"
    if days > 0:
        return f"D-{days}"
    return f"D+{-days}"
