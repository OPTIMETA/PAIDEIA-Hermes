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

# Rendering a PDF to page images is the first step of *every* OCR tier, so these
# rank alongside poppler: without them nothing ingests and nothing grades.
REQUIRED_PY_DEPS = {
    "pdf2image": "pdf2image",
    "PIL": "pillow",
}
# Everything else is tier- or command-specific; missing them degrades one path.
OPTIONAL_PY_DEPS = {
    "pytesseract": ("pytesseract", "tesseract tier + the ollama tier's fallback"),
    "reportlab": ("reportlab", "/paideia cheatsheet --pdf"),
    "pypdf": ("pypdf", "ad-hoc merge/split in the pdf skill"),
    "pdfplumber": ("pdfplumber", "ad-hoc text dumps in the pdf skill"),
}

# The plugin's own payload. A half-finished `git clone`, a partial copy, or a
# stale symlink otherwise passes every other check and only fails later, in the
# middle of a command, as "no command spec file found".
PAYLOAD_SCRIPTS = ("pd_render.py", "pd_vision_ocr.py", "pd_doctor.py")
PAYLOAD_COMMANDS = (
    "alt", "analyze", "blind", "chain", "cheatsheet", "derive", "grade", "hwmap",
    "ingest", "init-course", "mock", "pattern", "quiz", "twin", "weakmap",
)
PAYLOAD_SKILLS = (
    "paideia-alt-import", "paideia-answer-processing", "paideia-course-builder",
    "paideia-exam-drill", "paideia-pdf", "paideia-vision-ocr",
)

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
    # Byte-identical copy of pd_meta._META_COMMENT_RX (this module stays
    # standalone). Looser splits eat real text: a bare `#` reads
    # `COURSE_NAME: C# Programming` as `C`, and a single space reads
    # `Complex Analysis #2` as `Complex Analysis`. tests/ pins every copy.
    comment_rx = re.compile(r"(?:^|\t|[ ]{2,})#")
    try:
        for line in p.read_text(encoding="utf-8", errors="replace").splitlines():
            m = rx.match(line)
            if m:
                meta[m.group(1)] = comment_rx.split(m.group(2), maxsplit=1)[0].strip()
    except OSError:
        pass
    return meta


_PROBE_SRC = (
    "import sys\n"
    "for n in sys.argv[1:]:\n"
    "    try:\n"
    "        __import__(n)\n"
    "        print(n, 1)\n"
    "    except Exception:\n"
    "        print(n, 0)\n"
)


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


def probe_modules(names: tuple[str, ...]) -> dict[str, bool]:
    """Probe every dependency in ONE interpreter launch.

    Doctor is interactive — `/paideia init`'s wizard runs it, and it's the first
    thing you reach for when something breaks. One `python3 -c` per dependency
    spent ~0.7s of a ~0.9s run on interpreter startup alone.

    A real `__import__` rather than `find_spec`, because a package can have a
    findable spec and still fail to import. Any name the batch doesn't report on
    (it died partway, or the launch failed outright) falls back to its own
    subprocess, so one pathological module can't hide the rest.
    """
    found: dict[str, bool] = {}
    try:
        r = subprocess.run(
            [AGENT_PY, "-c", _PROBE_SRC, *names],
            capture_output=True, text=True, timeout=60,
        )
        for line in r.stdout.splitlines():
            parts = line.split()
            if len(parts) == 2 and parts[0] in names:
                found[parts[0]] = parts[1] == "1"
    except Exception:
        pass
    for n in names:
        if n not in found:
            found[n] = _has_module(n)
    return found


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
    # Keyed on the file existing, not on it parsing. A `.course-meta` that is
    # present but empty is a *broken* course, and skipping the workspace checks
    # there means doctor answers "all clear" about exactly the folder it was run
    # to diagnose — while /paideia status calls it "not a course folder" and the
    # LLM subcommands go ahead and run.
    course_mode = (cwd / ".course-meta").exists()
    ocr_engine = meta.get("OCR_ENGINE", "claude").strip().lower()
    lang = meta.get("INTERFACE_LANG", "en").strip().lower()

    # --- Python deps (probed in the agent's terminal python, not hermes' venv) ---
    r.add(OK, "python (agent terminal)", AGENT_PY)
    present = probe_modules(tuple(REQUIRED_PY_DEPS) + tuple(OPTIONAL_PY_DEPS))
    for dep, pkg in REQUIRED_PY_DEPS.items():
        r.add(OK if present[dep] else FAIL, f"py:{dep}",
              "" if present[dep] else f"required by every OCR tier — pip install {pkg}")
    for dep, (pkg, why) in OPTIONAL_PY_DEPS.items():
        r.add(OK if present[dep] else WARN, f"py:{dep}",
              "" if present[dep] else f"{why} — pip install {pkg}")

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

    # --- plugin payload (scripts + command specs + skills all shipped?) ---
    here = Path(__file__).resolve().parent
    missing_payload = [s for s in PAYLOAD_SCRIPTS if not (here / s).is_file()]
    missing_payload += [
        f"commands/{c}.md" for c in PAYLOAD_COMMANDS
        if not (here / "commands" / f"{c}.md").is_file()
    ]
    missing_payload += [
        f"skills/{s}/SKILL.md" for s in PAYLOAD_SKILLS
        if not (here / "skills" / s / "SKILL.md").is_file()
    ]
    n_payload = len(PAYLOAD_SCRIPTS) + len(PAYLOAD_COMMANDS) + len(PAYLOAD_SKILLS)
    r.add(OK if not missing_payload else FAIL, "plugin:payload",
          f"{n_payload} files" if not missing_payload
          else f"{len(missing_payload)} missing: " + ", ".join(missing_payload[:3])
               + ("…" if len(missing_payload) > 3 else ""))

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
        if not meta:
            r.add(FAIL, "meta:.course-meta",
                  "present but has no readable KEY: value lines — restore it or "
                  "re-run `/paideia init name=… exam=YYYY-MM-DD`")

        missing = [d for d in SKELETON if not (cwd / d).is_dir()]
        if missing and fix:
            for d in missing:
                try:
                    (cwd / d).mkdir(parents=True, exist_ok=True)
                except OSError:
                    pass  # re-listed as missing below; --fix never raises
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
            try:
                log.parent.mkdir(parents=True, exist_ok=True)
                log.write_text(_ERRORS_LOG_SEED, encoding="utf-8")
            except OSError:
                pass  # reported below as still-missing; --fix never raises
        r.add(OK if log.exists() else (WARN if not fix else FAIL), "workspace:errors/log.md",
              "" if log.exists() else "missing — rerun with --fix")

        writable = os.access(cwd, os.W_OK)
        r.add(OK if writable else FAIL, "workspace:writable", "" if writable else "CWD is read-only")

    # --- fix: chmod +x bundled scripts ---
    if fix:
        for script in PAYLOAD_SCRIPTS:
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
