"""`/paideia <subcommand>` dispatcher.

Deterministic subcommands (init, doctor, status, help) run as pure Python and
return text immediately. The 14 LLM-driven subcommands build an inject prompt
and hand the turn to the agent via ``ctx.inject_message``.
"""
from __future__ import annotations

import shlex
from pathlib import Path

from . import pd_meta, pd_prompts, pd_status, pd_workspace

LLM_SUBS = {
    "ingest", "analyze", "hwmap", "pattern", "derive", "blind", "twin",
    "quiz", "chain", "mock", "grade", "cheatsheet", "weakmap", "alt",
}
DETERMINISTIC = {"init", "doctor", "status", "help"}

_HELP_EN = """\
/paideia — exam-prep from your own course materials (HW-density weighted)

Setup
  init [name="..." exam=YYYY-MM-DD type=final lang=en|ko ocr=claude|ollama|tesseract weak="..."]
       bootstrap a course folder (no args → interactive setup)
  doctor [--fix]      diagnose install + workspace (repair safe issues)
  status              one-line: course · D-N · phase · top-miss pattern

Build the index
  ingest              transcribe materials/*.pdf → converted/*.md (LaTeX)
  analyze             build course-index/ (summary, patterns, coverage)
  hwmap [hot|§N|all]  exam-hot sections ranked by HW density
  pattern [§/Pk/kw]   show solution-pattern cards

Drill (you solve on paper, scan, then /paideia grade)
  quiz <topic|weakmap> [N]   N practice problems (weakmap → target weaknesses)
  blind <id>                 strategy-only blind drill (no math typing)
  twin <id>                  same-technique variant
  chain                      multi-pattern integration problem
  mock                       full HW-weighted mock exam
  derive <topic>             save a clean reference derivation

Close the loop
  grade [--ocr=…] [path]     OCR a scanned answer PDF + strategy-grade it
  weakmap [concept]          priority-ranked weakness report
  cheatsheet [--pdf]         one-page error-driven cheatsheet
  alt [path]                 import Exam Radar (Alt) lecture-emphasis signal
"""

_HELP_KO = """\
/paideia — 내 강의 자료로 만드는 시험 대비 (숙제 빈도 가중)

설정
  init [name="..." exam=YYYY-MM-DD type=final lang=en|ko ocr=claude|ollama|tesseract weak="..."]
       코스 폴더 부트스트랩 (인자 없으면 대화형 설정)
  doctor [--fix]      설치/워크스페이스 진단 (안전한 항목 자동 수정)
  status              한 줄 요약: 코스 · D-N · 단계 · 최다 실수 패턴

인덱스 구축
  ingest              materials/*.pdf → converted/*.md (LaTeX) 변환
  analyze             course-index/ 생성 (summary, patterns, coverage)
  hwmap [hot|§N|all]  숙제 빈도순 시험 핵심 섹션
  pattern [§/Pk/kw]   풀이 패턴 카드 보기

드릴 (종이에 풀고 스캔 후 /paideia grade)
  quiz <topic|weakmap> [N]   연습문제 N개 (weakmap → 약점 집중)
  blind <id>                 전략만 점검하는 블라인드 드릴
  twin <id>                  같은 기법, 새 표면의 변형문제
  chain                      여러 패턴 통합문제
  mock                       숙제 가중 모의고사
  derive <주제>              깔끔한 참조 유도 저장

마무리 루프
  grade [--ocr=…] [path]     스캔 답안 PDF OCR + 전략 채점
  weakmap [개념]             우선순위 약점 리포트
  cheatsheet [--pdf]         오류 기반 한 페이지 치트시트
  alt [path]                 Exam Radar(Alt) 강의 강조 신호 가져오기
"""


def _help(cwd: Path) -> str:
    return _HELP_KO if pd_meta.read_lang(cwd) == "ko" else _HELP_EN


def _ack(sub: str, cwd: Path, lang: str) -> str:
    if lang == "ko":
        return f"▶ /paideia {sub} — 에이전트(codex)에 전달했습니다 · 작업 디렉터리: {cwd}"
    return f"▶ /paideia {sub} — handed to the agent (codex) · working dir: {cwd}"


def _parse_kv(rest: str) -> dict[str, str]:
    """Parse ``name="A B" exam=2026-07-01 lang=ko`` into a dict."""
    out: dict[str, str] = {}
    try:
        tokens = shlex.split(rest)
    except ValueError:
        tokens = rest.split()
    for tok in tokens:
        if "=" in tok:
            k, v = tok.split("=", 1)
            out[k.strip().lower()] = v.strip()
    return out


def _init_summary(report: dict, meta: dict[str, str], lang: str) -> str:
    n = len(report.get("created_dirs", []))
    if lang == "ko":
        return (
            f"✓ PAIDEIA 코스 생성: {meta['COURSE_NAME']} (시험 {meta['EXAM_DATE']}, "
            f"{meta['INTERFACE_LANG']}, OCR={meta['OCR_ENGINE']})\n"
            f"  디렉터리 {n}개 생성, .course-meta + errors/log.md 작성\n"
            f"  다음: materials/ 에 PDF를 넣고 `/paideia ingest` → `/paideia analyze`"
        )
    return (
        f"✓ PAIDEIA course created: {meta['COURSE_NAME']} (exam {meta['EXAM_DATE']}, "
        f"{meta['INTERFACE_LANG']}, OCR={meta['OCR_ENGINE']})\n"
        f"  created {n} dirs, wrote .course-meta + errors/log.md\n"
        f"  next: drop PDFs into materials/ then `/paideia ingest` → `/paideia analyze`"
    )


def _do_init(rest: str, cwd: Path, ctx) -> str:
    kv = _parse_kv(rest)
    name, exam = kv.get("name"), kv.get("exam")
    if name and exam:
        lang = kv.get("lang", "en").lower()
        if lang not in pd_meta.VALID_LANG:
            lang = "en"
        ocr = kv.get("ocr", "claude").lower()
        if ocr not in pd_meta.VALID_OCR:
            ocr = "claude"
        meta = {
            "COURSE_NAME": name,
            "EXAM_DATE": exam,
            "EXAM_TYPE": kv.get("type", "final"),
            "USER_WEAK_ZONES": kv.get("weak", "unknown"),
            "OCR_ENGINE": ocr,
            "INTERFACE_LANG": lang,
        }
        report = pd_workspace.scaffold_course(cwd, meta)
        return _init_summary(report, meta, lang)
    # Not enough args → let the agent run the interactive setup wizard.
    lang = kv.get("lang", pd_meta.read_lang(cwd))
    msg = pd_prompts.build_inject("init-course", rest, cwd, lang)
    if ctx is not None and ctx.inject_message(msg, role="user"):
        return _ack("init", cwd, lang)
    return msg


def _not_a_course() -> str:
    return (
        "✗ not a PAIDEIA course folder — run `/paideia init` here first.\n"
        "✗ PAIDEIA 코스 폴더가 아닙니다 — 먼저 `/paideia init` 을 실행하세요."
    )


def dispatch(raw_args: str, ctx=None) -> str | None:
    try:
        raw = (raw_args or "").strip()
        parts = raw.split(None, 1)
        sub = parts[0].lower() if parts else "help"
        rest = parts[1] if len(parts) > 1 else ""
        cwd = Path.cwd()

        if sub in ("help", "-h", "--help", ""):
            return _help(cwd)
        if sub == "status":
            return pd_status.render_status(cwd)
        if sub == "doctor":
            from . import pd_doctor
            _, report = pd_doctor.run(cwd, fix=("--fix" in rest.split()))
            return report
        if sub == "init":
            return _do_init(rest, cwd, ctx)

        if sub not in LLM_SUBS:
            return f"[paideia] unknown subcommand '{sub}'. Try `/paideia help`."

        if not pd_workspace.is_course(cwd):
            return _not_a_course()

        lang = pd_meta.read_lang(cwd)
        msg = pd_prompts.build_inject(sub, rest, cwd, lang)
        if ctx is not None and ctx.inject_message(msg, role="user"):
            return _ack(sub, cwd, lang)
        # Gateway mode / no CLI ref: return the spec so the turn still happens.
        return msg
    except Exception as e:  # never crash the host CLI
        return f"[paideia] error: {type(e).__name__}: {e}"
