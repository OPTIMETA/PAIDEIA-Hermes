"""Weakmap helpers — locate the latest report, its verdict, and the top-miss
pattern. Mirrors upstream PAIDEIA's statusline/session-start logic.
"""
from __future__ import annotations

import glob
import re
from pathlib import Path

from . import pd_errlog

_VERDICT_RX = re.compile(r"##\s*One-line verdict\s*\n+\s*(.+?)(?:\n|$)")


def latest_weakmap(cwd: Path) -> Path | None:
    matches = sorted(
        glob.glob(str(Path(cwd) / "weakmap" / "weakmap_*.md")), reverse=True
    )
    return Path(matches[0]) if matches else None


def latest_verdict(cwd: Path) -> str | None:
    wm = latest_weakmap(cwd)
    if not wm:
        return None
    try:
        text = wm.read_text(encoding="utf-8", errors="replace")
    except OSError:
        return None
    m = _VERDICT_RX.search(text)
    return m.group(1).strip() if m else None


def top_miss(cwd: Path) -> str | None:
    """Top-miss pattern: prefer the newest weakmap, else fall back to the error log."""
    wm = latest_weakmap(cwd)
    if wm:
        try:
            text = wm.read_text(encoding="utf-8", errors="replace")
        except OSError:
            text = ""
        m = pd_errlog.PATTERN_RX.search(text)
        if m:
            return m.group(1)
        m = re.search(r"\bP(\d+)\b", text)
        if m:
            return f"P{m.group(1)}"
    return pd_errlog.top_pattern(cwd)
