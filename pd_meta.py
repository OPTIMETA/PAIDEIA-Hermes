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
import itertools
import os
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
# A trailing comment must start the value, or be introduced by a tab or two or
# more spaces. That exact threshold is what makes write→read lossless: _flatten()
# collapses every whitespace run to a single space, so a value this module writes
# can never come back looking like a comment. Anything looser silently eats real
# text — a bare `#` turns `C# Programming` into `C`, and a single space turns
# `Complex Analysis #2` into `Complex Analysis`. Hand-written comments keep the
# documented `NAME: value  # note` form.
# pd_doctor.py and pd_vision_ocr.py keep byte-identical copies of this pattern
# so they can run standalone; tests/ pins all three to the same behaviour.
_META_COMMENT_RX = re.compile(r"(?:^|\t|[ ]{2,})#")


def strip_comment(value: str) -> str:
    """Drop a trailing ``# comment`` from a ``.course-meta`` value."""
    return _META_COMMENT_RX.split(value, maxsplit=1)[0].strip()


# Same scrub pd_errlog applies to error-log values. COURSE_NAME is echoed to the
# terminal by the session banner and the status line, so an escape sequence that
# survives here is written straight to the user's terminal on every session start
# in that folder.
_CTRL_RX = re.compile(r"[\x00-\x1f\x7f]+")


def _flatten(value: object) -> str:
    """Collapse a value to one printable line.

    ``.course-meta`` is line-oriented, so a newline inside a value would write a
    second key the reader treats as real — silently truncating the intended value
    and, depending on order, overriding a later canonical key. Other control
    characters are dropped for the terminal-echo reason above.
    """
    return re.sub(r"\s+", " ", _CTRL_RX.sub(" ", str(value))).strip()


_tmp_counter = itertools.count()


def _create_temp(path: Path) -> tuple[int, Path]:
    """Create a fresh temp file beside *path*, with normal creation permissions.

    Deliberately not ``tempfile.mkstemp``: that hardcodes 0600, which would make
    an atomic write silently privatise files. Restoring the mode afterwards means
    either hardcoding 0644 (overriding a deliberately strict umask) or reading the
    umask, which is process-global and cannot be read without briefly setting it —
    a race against any other thread creating a file. ``os.open`` with mode 0o666
    applies the umask itself, exactly as ordinary file creation does, so there is
    nothing to restore and nothing to race. ``O_EXCL`` keeps the name unique.
    """
    for _ in range(100):
        tmp = path.parent / f".{path.name}.{os.getpid()}.{next(_tmp_counter)}.tmp"
        try:
            return os.open(tmp, os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o666), tmp
        except FileExistsError:
            continue
    raise OSError(f"could not create a temp file beside {path}")


def atomic_write_text(path: Path, text: str, *, encoding: str = "utf-8") -> Path:
    """Write *text* to *path* atomically — temp file in the same dir, then rename.

    A truncate-in-place write that dies mid-flight (SIGINT, full disk, crash)
    leaves a half-written or empty file behind. For ``.course-meta`` that is
    unrecoverable in a specific way: its *existence* is what marks the folder as
    a course, so a zero-byte survivor makes every ``/paideia`` subcommand refuse
    to run while the file still looks present. ``os.replace`` is atomic on POSIX
    and Windows, so a concurrent reader sees either the old file or the new one.
    """
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    # Rewriting an existing file keeps that file's mode; a new one gets whatever
    # ordinary creation would give (see _create_temp).
    try:
        mode = path.stat().st_mode & 0o777
    except OSError:
        mode = None
    fd, tmp = _create_temp(path)
    try:
        with os.fdopen(fd, "w", encoding=encoding, newline="\n") as fh:
            fh.write(text)
            fh.flush()
            os.fsync(fh.fileno())
        if mode is not None:
            os.chmod(tmp, mode)
        os.replace(tmp, path)
    except BaseException:
        try:
            os.unlink(tmp)
        except OSError:
            pass
        raise
    return path


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
                meta[m.group(1)] = strip_comment(m.group(2))
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
        lines.append(f"{k}: {_flatten(meta.get(k, ''))}")
    for k, v in meta.items():
        if k not in META_KEYS:
            lines.append(f"{_flatten(k)}: {_flatten(v)}")
    return atomic_write_text(Path(cwd) / ".course-meta", "\n".join(lines) + "\n")


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
