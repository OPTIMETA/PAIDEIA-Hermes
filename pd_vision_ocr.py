"""Vision-OCR pipeline for hand-written math answer PDFs (local-inference tiers).

The default `/paideia grade` path uses the hermes agent's own native vision (no
external model). This script covers the optional offline tiers and is invoked
only when ``OCR_ENGINE=ollama`` or ``OCR_ENGINE=tesseract``.

Engines:
    ollama     - local Qwen3-VL 8B via ollama, falls back to tesseract on error.
    tesseract  - skip ollama, go straight to pytesseract (lang derived from
                 INTERFACE_LANG: en->`eng`, ko->`eng+kor`).

Usage:
    python pd_vision_ocr.py <input.pdf> <output.md>
    python pd_vision_ocr.py --engine=ollama    <input.pdf> <output.md>
    python pd_vision_ocr.py --engine=tesseract <input.pdf> <output.md>
    python pd_vision_ocr.py --engine=ollama \\
        --course-name="Quantum Mechanics" --lang=en <input.pdf> <output.md>

Self-contained (no intra-package imports) so the agent can run it via the
`terminal` tool. `--course-name` / `--lang` override `.course-meta` in CWD.
"""
from __future__ import annotations

import base64
import io
import json
import re
import sys
import urllib.request
from pathlib import Path

OLLAMA_MODEL = "qwen3-vl:8b"
DPI = 300
MAX_IMG_WIDTH = 1200
PER_PAGE_TIMEOUT = 1800
WARMUP_TIMEOUT = 60
MAX_TOKENS = 6000

DEFAULT_COURSE = "math / physics"
DEFAULT_LANG = "en"

_PROSE_RULE = {
    "en": "- Prose stays in its original language (English, Korean, etc.) — do not translate.",
    "ko": "- Korean prose stays as Korean prose.",
}

PROMPT_TEMPLATE = """You are transcribing a hand-written student answer for a {course} exam.

Rules:
{prose_rule}
- Math expressions must become LaTeX: $...$ inline, $$...$$ display.
- Preserve problem numbering (P1, P2, (1), (2), (a), (b), etc.).
- Do NOT interpret or grade. Just transcribe what is written.
- If a symbol is ambiguous, write [?] instead of guessing.
- If a page has crossed-out work, ignore the strikethrough content.
- Return ONLY markdown, no commentary, no <think>.
"""

ENG_NOISE_PREFIXES = (
    "wait,", "wait.", "hmm,", "actually,",
    "but the hand-written", "the image shows", "the image has",
    "got it", "let's check", "let's look",
    "on second thought", "looking at this again",
)

KOR_NOISE_PREFIXES = (
    "잠깐", "잠시만", "음,", "음...", "어,", "어...",
    "다시 보면", "다시 확인", "확인해보면", "생각해보면",
    "근데 이 이미지", "그런데 이 이미지",
    "이미지를 보면", "이미지에는", "손글씨를 보면",
    "한 번 더 보면", "써보면",
)


def build_prompt(course: str | None = None, lang: str | None = None) -> str:
    course_text = (course or DEFAULT_COURSE).strip() or DEFAULT_COURSE
    lang_key = (lang or DEFAULT_LANG).strip().lower()
    if lang_key not in _PROSE_RULE:
        lang_key = DEFAULT_LANG
    return PROMPT_TEMPLATE.format(course=course_text, prose_rule=_PROSE_RULE[lang_key])


# Byte-identical copy of pd_meta._META_COMMENT_RX (this module stays standalone
# so the agent can run it from any cwd). A bare `#` split would read
# `COURSE_NAME: C# Programming` as `C`; tests/ pins every copy to one behaviour.
_META_COMMENT_RX = re.compile(r"(?:^|\s)#")


def read_course_name(cwd: Path | None = None) -> str | None:
    cwd = cwd or Path.cwd()
    meta_path = cwd / ".course-meta"
    if not meta_path.exists():
        return None
    try:
        for line in meta_path.read_text(encoding="utf-8", errors="replace").splitlines():
            m = re.match(r"^\s*COURSE_NAME\s*:\s*(.+?)\s*$", line)
            if m:
                return _META_COMMENT_RX.split(m.group(1), maxsplit=1)[0].strip() or None
    except OSError:
        pass
    return None


def read_interface_lang(cwd: Path | None = None) -> str:
    cwd = cwd or Path.cwd()
    meta_path = cwd / ".course-meta"
    if not meta_path.exists():
        return DEFAULT_LANG
    try:
        for line in meta_path.read_text(encoding="utf-8", errors="replace").splitlines():
            m = re.match(r"^\s*INTERFACE_LANG\s*:\s*(.+?)\s*$", line)
            if m:
                v = _META_COMMENT_RX.split(m.group(1), maxsplit=1)[0].strip().lower()
                if v in _PROSE_RULE:
                    return v
    except OSError:
        pass
    return DEFAULT_LANG


def image_to_b64(img) -> str:
    if img.width > MAX_IMG_WIDTH:
        ratio = MAX_IMG_WIDTH / img.width
        img = img.resize((MAX_IMG_WIDTH, int(img.height * ratio)))
    buf = io.BytesIO()
    img.save(buf, format="JPEG", quality=90)
    return base64.b64encode(buf.getvalue()).decode()


def warmup_ollama() -> None:
    payload = {
        "model": OLLAMA_MODEL,
        "prompt": "ping",
        "stream": False,
        "keep_alive": "15m",
        "options": {"num_predict": 1},
    }
    req = urllib.request.Request(
        "http://localhost:11434/api/generate",
        data=json.dumps(payload).encode(),
        headers={"Content-Type": "application/json"},
    )
    with urllib.request.urlopen(req, timeout=WARMUP_TIMEOUT) as resp:
        resp.read()


def call_ollama_vision(img_b64: str, prompt: str) -> str:
    payload = {
        "model": OLLAMA_MODEL,
        "prompt": prompt,
        "images": [img_b64],
        "stream": False,
        "think": False,
        "keep_alive": "15m",
        "options": {
            "temperature": 0.1,
            "num_ctx": 4096,
            "num_predict": MAX_TOKENS,
            "repeat_penalty": 1.3,
            "repeat_last_n": 256,
        },
    }
    req = urllib.request.Request(
        "http://localhost:11434/api/generate",
        data=json.dumps(payload).encode(),
        headers={"Content-Type": "application/json"},
    )
    with urllib.request.urlopen(req, timeout=PER_PAGE_TIMEOUT) as resp:
        body = resp.read().decode()
    response = json.loads(body)
    text = response.get("response", "") or response.get("thinking", "")
    text = text.replace("<think>", "").replace("</think>", "").strip()
    return dedupe_loops(text)


def _is_noise_sentence(s: str) -> bool:
    lower = s.lower()
    if lower.startswith(ENG_NOISE_PREFIXES):
        return True
    stripped = s.lstrip()
    for prefix in KOR_NOISE_PREFIXES:
        if stripped.startswith(prefix):
            return True
    return False


def _strip_ngram_tail(text: str, n: int = 5, max_repeats: int = 3) -> str:
    tokens = text.split()
    if len(tokens) < n * max_repeats:
        return text
    tail = tokens[-n * max_repeats:]
    window = tuple(tail[:n])
    if all(tuple(tail[i * n:(i + 1) * n]) == window for i in range(max_repeats)):
        return " ".join(tokens[: -n * (max_repeats - 1)])
    return text


def dedupe_loops(text: str) -> str:
    sentences = re.split(r"(?<=[.?!])\s+", text)
    kept: list[str] = []
    seen: set[str] = set()
    for s in sentences:
        s = s.strip()
        if not s:
            continue
        if _is_noise_sentence(s):
            continue
        key = re.sub(r"\s+", " ", s[:100])
        if key in seen:
            continue
        seen.add(key)
        kept.append(s)
    return _strip_ngram_tail(" ".join(kept))


_TESS_LANG = {"en": "eng", "ko": "eng+kor"}


def page_count(pdf_path: Path) -> int:
    """Number of pages in *pdf_path* (0 if poppler can't report it)."""
    from pdf2image import pdfinfo_from_path

    try:
        return int(pdfinfo_from_path(str(pdf_path))["Pages"])
    except Exception:
        return 0


def iter_pages(pdf_path: Path, total: int | None = None):
    """Yield ``(page_number, PIL.Image)`` one page at a time.

    ``convert_from_path`` without ``first_page``/``last_page`` decodes the whole
    PDF into memory: at ``DPI=300`` a 40-page hand-written scan is roughly a
    gigabyte of RGB bitmaps, on top of whatever the local VLM is already holding.
    Rendering one page per call keeps peak memory at a single page.

    Deliberately a local copy of the same loop in the sibling ``pd_render.py``:
    this module's contract is that ``python3 <abspath>/pd_vision_ocr.py`` runs
    from any working directory with zero import assumptions. ``tests/`` pins the
    two implementations to the same page ordering so they can't drift apart.
    """
    from pdf2image import convert_from_path

    if total is None:
        total = page_count(pdf_path)
    if total <= 0:
        for i, img in enumerate(convert_from_path(str(pdf_path), dpi=DPI), 1):
            yield i, img
        return
    for i in range(1, total + 1):
        imgs = convert_from_path(str(pdf_path), dpi=DPI, first_page=i, last_page=i)
        if not imgs:
            continue
        img = imgs[0]
        try:
            yield i, img
        finally:
            img.close()


def tesseract_fallback(pages, lang: str = DEFAULT_LANG) -> str:
    """Transcribe an iterable of ``(page_number, image)`` with pytesseract."""
    import pytesseract

    tess_lang = _TESS_LANG.get(lang, "eng")
    out = []
    for i, img in pages:
        out.append(f"## Page {i}\n\n{pytesseract.image_to_string(img, lang=tess_lang)}\n")
    return "\n".join(out)


def ocr_pdf(
    pdf_path: Path,
    out_path: Path,
    engine: str = "ollama",
    course_name: str | None = None,
    lang: str | None = None,
) -> None:
    pdf_path = Path(pdf_path)
    out_path = Path(out_path)
    n_pages = page_count(pdf_path)
    pages_label = n_pages if n_pages > 0 else "?"

    effective_course = course_name or read_course_name(Path.cwd()) or DEFAULT_COURSE
    effective_lang = (lang or read_interface_lang(Path.cwd()) or DEFAULT_LANG).strip().lower()
    if effective_lang not in _PROSE_RULE:
        effective_lang = DEFAULT_LANG
    prompt = build_prompt(effective_course, effective_lang)
    tess_lang = _TESS_LANG.get(effective_lang, "eng")

    if engine == "tesseract":
        header = (
            f"# Vision-OCR transcription\n\n"
            f"<!-- SOURCE: {pdf_path.name}, tesseract {tess_lang} @ {DPI}dpi, "
            f"{pages_label} pages -->\n"
            f"<!-- TIER: tesseract (explicit) -->\n\n"
        )
        body = tesseract_fallback(iter_pages(pdf_path, n_pages), effective_lang)
    else:
        header = (
            f"# Vision-OCR transcription\n\n"
            f"<!-- SOURCE: {pdf_path.name}, "
            f"{OLLAMA_MODEL} @ {DPI}dpi, {pages_label} pages, "
            f"course: {effective_course}, lang: {effective_lang} -->\n\n"
        )
        try:
            sys.stderr.write(f"[vision-ocr] warming up {OLLAMA_MODEL} ...\n")
            warmup_ollama()
            pages_md = []
            for i, img in iter_pages(pdf_path, n_pages):
                sys.stderr.write(f"[vision-ocr] page {i}/{pages_label} ...\n")
                sys.stderr.flush()
                md = call_ollama_vision(image_to_b64(img), prompt)
                pages_md.append(f"## Page {i}\n\n{md}\n")
            body = "\n".join(pages_md)
        except Exception as e:
            sys.stderr.write(f"[vision-ocr] ollama tier failed: {e}\n")
            sys.stderr.write("[vision-ocr] falling back to tesseract...\n")
            # Re-render from the PDF: the ollama iterator is spent, and the whole
            # file is stamped with one tier, so partial ollama output is dropped.
            body = "<!-- TIER: tesseract fallback -->\n\n" + tesseract_fallback(
                iter_pages(pdf_path, n_pages), effective_lang
            )

    out_path.parent.mkdir(parents=True, exist_ok=True)
    # encoding is explicit: without it Python uses the locale encoding, which
    # mangles (or hard-fails on) Korean transcriptions under a C/POSIX locale.
    out_path.write_text(header + body, encoding="utf-8")
    sys.stderr.write(f"[vision-ocr] wrote {out_path} ({len(header + body)} chars)\n")


def _parse_args(argv: list[str]) -> tuple[str, Path, Path, str | None, str | None]:
    engine = "ollama"
    course_name: str | None = None
    lang: str | None = None
    positional: list[str] = []
    for arg in argv[1:]:
        if arg.startswith("--engine="):
            engine = arg.split("=", 1)[1].strip().lower()
        elif arg.startswith("--course-name="):
            course_name = arg.split("=", 1)[1].strip() or None
        elif arg.startswith("--lang="):
            lang = arg.split("=", 1)[1].strip().lower() or None
        else:
            positional.append(arg)
    if engine not in {"ollama", "tesseract"}:
        print(f"error: --engine must be 'ollama' or 'tesseract' (got '{engine}')", file=sys.stderr)
        sys.exit(2)
    if lang is not None and lang not in _PROSE_RULE:
        print(f"error: --lang must be 'en' or 'ko' (got '{lang}')", file=sys.stderr)
        sys.exit(2)
    if len(positional) != 2:
        print(
            "usage: python pd_vision_ocr.py [--engine=ollama|tesseract] "
            "[--course-name=<name>] [--lang=en|ko] <input.pdf> <output.md>",
            file=sys.stderr,
        )
        sys.exit(2)
    return engine, Path(positional[0]), Path(positional[1]), course_name, lang


if __name__ == "__main__":
    engine, pdf, out, course, lang = _parse_args(sys.argv)
    if not pdf.is_file():
        print(f"error: no such PDF: {pdf}", file=sys.stderr)
        sys.exit(2)
    ocr_pdf(pdf, out, engine=engine, course_name=course, lang=lang)
