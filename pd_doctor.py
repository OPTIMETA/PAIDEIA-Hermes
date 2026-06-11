"""PAIDEIA-Hermes install + workspace doctor (stdlib-only, self-contained).

Two modes, auto-detected:
  global  - no .course-meta in CWD → check deps + hermes wiring only
  course  - .course-meta present   → also check the workspace

`--fix` performs permission-free repairs (create dirs, seed errors/log.md,
chmod +x scripts). It never runs brew/apt/pip and never guesses .course-meta.

Exit code: 0 = all clear, 1 = warnings, 2 = blocking problems.

Runnable standalone (the agent invokes it via the `terminal` tool):
    python pd_doctor.py [--fix]
or imported by the plugin: ``pd_doctor.run(cwd, fix=False) -> (code, report)``.
"""
from __future__ import annotations

import importlib.util
import os
import re
import shutil
import stat
import subprocess
import sys
import urllib.request
from pathlib import Path

# The interpreter the agent's `terminal` tool / OCR+render scripts actually use
# (PATH python3), NOT this embedding interpreter (hermes runs in its own venv).
# Doctor must probe THIS python or it misreports dep availability.
AGENT_PY = shutil.which("python3") or shutil.which("python") or sys.executable

OK, WARN, FAIL = "ok", "warn", "fail"
_SYMBOL = {OK: "✓", WARN: "•", FAIL: "✗"}
_RANK = {OK: 0, WARN: 1, FAIL: 2}

PY_DEPS = ("pypdf", "pdfplumber", "pytesseract", "pdf2image", "PIL", "reportlab")
SKELETON = (
    "materials/lectures", "materials/textbook", "materials/homework", "materials/solutions",
    "converted/lectures", "converted/textbook", "converted/homework", "converted/solutions",
    "course-index", "quizzes", "mock", "twins", "chain", "derivations", "cheatsheet",
    "weakmap", "answers/converted", "answers/_archive", "errors",
)
META_KEYS = ("COURSE_NAME", "EXAM_DATE", "EXAM_TYPE", "USER_WEAK_ZONES", "OCR_ENGINE", "INTERFACE_LANG")

_ERRORS_LOG_SEED = """\
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


class Report:
    def __init__(self) -> None:
        self.rows: list[tuple[str, str, str]] = []  # (status, label, detail)

    def add(self, status: str, label: str, detail: str = "") -> None:
        self.rows.append((status, label, detail))

    @property
    def code(self) -> int:
        worst = max((_RANK[s] for s, _, _ in self.rows), default=0)
        return worst

    def render(self) -> str:
        lines = ["paideia doctor", "─" * 40]
        for status, label, detail in self.rows:
            tail = f"  ({detail})" if detail else ""
            lines.append(f"  {_SYMBOL[status]} {label}{tail}")
        verdict = {0: "all clear", 1: "warnings (non-blocking)", 2: "blocking problems"}[self.code]
        lines.append("─" * 40)
        lines.append(f"  → {verdict}")
        return "\n".join(lines)


def _parse_meta(cwd: Path) -> dict[str, str]:
    meta: dict[str, str] = {}
    p = cwd / ".course-meta"
    if not p.exists():
        return meta
    rx = re.compile(r"^\s*([A-Z_][A-Z0-9_]*)\s*:\s*(.+?)\s*$")
    try:
        for line in p.read_text(encoding="utf-8", errors="replace").splitlines():
            m = rx.match(line)
            if m:
                meta[m.group(1)] = m.group(2).split("#", 1)[0].strip()
    except OSError:
        pass
    return meta


def _has_module(name: str) -> bool:
    """Probe the *agent's* python (PATH python3), where the OCR/render scripts run."""
    try:
        r = subprocess.run(
            [AGENT_PY, "-c", f"import {name}"],
            capture_output=True,
            timeout=10,
        )
        return r.returncode == 0
    except Exception:
        try:
            return importlib.util.find_spec(name) is not None
        except (ImportError, ValueError):
            return False


def _ollama_has_model(model: str) -> bool | None:
    try:
        with urllib.request.urlopen("http://localhost:11434/api/tags", timeout=2) as r:
            body = r.read().decode("utf-8", "replace")
        return model.split(":")[0] in body
    except Exception:
        return None


def _hermes_home() -> Path:
    env = os.environ.get("HERMES_HOME")
    return Path(env) if env else Path.home() / ".hermes"


def run(cwd: Path, fix: bool = False) -> tuple[int, str]:
    cwd = Path(cwd)
    r = Report()
    meta = _parse_meta(cwd)
    course_mode = bool(meta)
    ocr_engine = meta.get("OCR_ENGINE", "claude").strip().lower()
    lang = meta.get("INTERFACE_LANG", "en").strip().lower()

    # --- Python deps (probed in the agent's terminal python, not hermes' venv) ---
    r.add(OK, "python (agent terminal)", AGENT_PY)
    for dep in PY_DEPS:
        present = _has_module(dep)
        # reportlab only needed for /paideia cheatsheet --pdf; pytesseract only
        # for tesseract/ollama OCR tiers → downgrade those to WARN.
        sev = WARN
        r.add(OK if present else sev, f"py:{dep}", "" if present else "pip install " + ("pillow" if dep == "PIL" else dep))

    # --- system binaries ---
    pdftoppm = shutil.which("pdftoppm")
    r.add(OK if pdftoppm else FAIL, "bin:poppler (pdftoppm)",
          "" if pdftoppm else "required for all OCR tiers — brew install poppler")
    tess = shutil.which("tesseract")
    tess_needed = ocr_engine in ("tesseract", "ollama")
    r.add(OK if tess else (FAIL if tess_needed else WARN), "bin:tesseract",
          "" if tess else "brew install tesseract" + (" tesseract-lang" if lang == "ko" else ""))

    # --- ollama (only if selected) ---
    if ocr_engine == "ollama":
        has = _ollama_has_model("qwen3-vl:8b")
        if has is None:
            r.add(FAIL, "ollama:daemon", "not reachable on localhost:11434 — `ollama serve`")
        elif has:
            r.add(OK, "ollama:qwen3-vl:8b")
        else:
            r.add(FAIL, "ollama:qwen3-vl:8b", "ollama pull qwen3-vl:8b")

    # --- hermes wiring ---
    home = _hermes_home()
    plug = home / "plugins" / "paideia"
    r.add(OK if plug.exists() else WARN, "hermes:plugin installed",
          "" if plug.exists() else f"expected {plug} (symlink or `hermes plugins install`)")
    cfg = home / "config.yaml"
    provider = None
    if cfg.exists():
        try:
            m = re.search(r"^\s*provider\s*:\s*(.+?)\s*$", cfg.read_text(errors="replace"), re.MULTILINE)
            provider = m.group(1).strip() if m else None
        except OSError:
            pass
    r.add(OK if provider else WARN, "hermes:model provider",
          provider or "no provider in ~/.hermes/config.yaml (run `hermes model`)")

    # --- workspace (course mode only) ---
    if course_mode:
        missing = [d for d in SKELETON if not (cwd / d).is_dir()]
        if missing and fix:
            for d in missing:
                (cwd / d).mkdir(parents=True, exist_ok=True)
            missing = [d for d in SKELETON if not (cwd / d).is_dir()]
        r.add(OK if not missing else (WARN if not fix else FAIL), "workspace:dirs",
              "" if not missing else f"{len(missing)} missing" + ("" if fix else " — rerun with --fix"))

        for k in META_KEYS:
            if not meta.get(k):
                r.add(WARN, f"meta:{k}", "empty/missing in .course-meta")
        if ocr_engine not in ("claude", "ollama", "tesseract"):
            r.add(FAIL, "meta:OCR_ENGINE", f"invalid '{ocr_engine}' (claude|ollama|tesseract)")
        if lang not in ("en", "ko"):
            r.add(WARN, "meta:INTERFACE_LANG", f"invalid '{lang}' (en|ko)")

        log = cwd / "errors" / "log.md"
        if not log.exists() and fix:
            log.parent.mkdir(parents=True, exist_ok=True)
            log.write_text(_ERRORS_LOG_SEED, encoding="utf-8")
        r.add(OK if log.exists() else (WARN if not fix else FAIL), "workspace:errors/log.md",
              "" if log.exists() else "missing — rerun with --fix")

        writable = os.access(cwd, os.W_OK)
        r.add(OK if writable else FAIL, "workspace:writable", "" if writable else "CWD is read-only")

    # --- fix: chmod +x bundled scripts ---
    if fix:
        here = Path(__file__).resolve().parent
        for script in ("pd_doctor.py", "pd_vision_ocr.py", "pd_render.py"):
            sp = here / script
            if sp.exists():
                try:
                    sp.chmod(sp.stat().st_mode | stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH)
                except OSError:
                    pass

    return r.code, r.render()


if __name__ == "__main__":
    fix_flag = "--fix" in sys.argv[1:]
    code, report = run(Path.cwd(), fix=fix_flag)
    print(report)
    sys.exit(code)
