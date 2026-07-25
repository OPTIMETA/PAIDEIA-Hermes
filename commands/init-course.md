You are bootstrapping the user's current working directory into a fresh PAIDEIA
course workspace. Everything you create lives in the **user's CWD** (the course
folder), not in the plugin. Keep chat output compact — the user is watching.

> Note: for the non-interactive path the user can run
> `/paideia init name="…" exam=YYYY-MM-DD type=final lang=en|ko ocr=claude|ollama|tesseract weak="…"`
> which scaffolds everything instantly. This spec is the **interactive** wizard.

## Step 0 — Interface language (ask in English; we don't know the preference yet)

Print exactly:

```
Choose interface language (PAIDEIA uses it for all future prompts, drill
instructions, and generated markdown narrative):
  1) en — English   (default)
  2) ko — 한국어
  Press Enter for: en
```

Normalize `1`/`en`/`english`/empty → `en`; `2`/`ko`/`korean`/`한국어` → `ko`.
Call it `INTERFACE_LANG`. **From here on, write every user-facing string in
`INTERFACE_LANG`.**

## Step 1 — Dependency check

Run `/paideia doctor` and relay the result. For any missing required item, show
the install command but do NOT auto-run it (these need brew/apt/pip and often
sudo):
- macOS: `brew install poppler tesseract tesseract-lang`
- Ubuntu: `sudo apt-get install poppler-utils tesseract-ocr tesseract-ocr-kor`
- Python libs: `python3 -m pip install --user pdf2image pillow pytesseract reportlab pypdf pdfplumber`

`poppler` plus the Python `pdf2image` and `pillow` are required by every OCR
tier — each one starts by rasterizing the PDF. `tesseract` + `pytesseract` are
needed only for the tesseract tier and the ollama tier's fallback; `reportlab`
only for `/paideia cheatsheet --pdf`; `ollama` + `qwen3-vl:8b` only if the user
picks the ollama OCR engine. `/paideia doctor` grades them on exactly this split.

## Step 2 — OCR engine choice (ask in `INTERFACE_LANG`)

```
Pick the default OCR engine for /paideia grade (override later with --ocr=…):
  1) claude    — the agent's own native vision (default, no extra install, best handwriting)
  2) ollama    — local Qwen3-VL 8B (nothing leaves the machine, ~6GB download)
  3) tesseract — pytesseract only (lightest/fastest, lowest accuracy)
  Press Enter for: claude
```

Normalize to `claude` / `ollama` / `tesseract` → `OCR_ENGINE`. If the user picks
`ollama`, remind them to `ollama serve` and `ollama pull qwen3-vl:8b`.

## Step 3 — Course metadata (ask in `INTERFACE_LANG`)

Ask four short questions:
1. `COURSE_NAME` (e.g., Complex Analysis MATH 405)
2. `EXAM_DATE` (YYYY-MM-DD)
3. `EXAM_TYPE` (midterm / final / qualifier)
4. `USER_WEAK_ZONES` (comma-separated topics, or `unknown`)

## Step 4 — Create the workspace

Hand the collected answers to the **non-interactive path** rather than writing
files yourself — it is the single implementation of scaffolding, so both entry
points produce byte-identical workspaces:

```
/paideia init name="<answer1>" exam=<answer2> type=<answer3> \
              weak="<answer4>" ocr=<from Step 2> lang=<from Step 0>
```

That one call writes `.course-meta` (six keys, canonical order), creates the full
directory skeleton (`materials/…`, `converted/…`, `course-index/`, `quizzes/`,
`mock/`, `twins/`, `chain/`, `derivations/`, `cheatsheet/`, `weakmap/`,
`answers/{converted,_archive}`, `errors/`), seeds `errors/log.md`, writes
`PAIDEIA.md`, and installs a `.gitignore` that keeps bulky scans in
`answers/_archive/` out of version control.

It rejects a malformed `exam=` date instead of scaffolding a course whose
countdown silently never appears — if it does, re-ask question 2 and retry.

Then run `/paideia doctor` and relay the report to confirm the result.

Optionally `git init && git add -A && git commit -m "paideia: initial setup"`
if the user wants version control (recommended — the error log is a learning
record worth committing).

## Step 5 — Print next steps (in `INTERFACE_LANG`)

```
✅ <COURSE_NAME> ready. (OCR: <OCR_ENGINE>, lang: <INTERFACE_LANG>)

PAIDEIA-Hermes shows a [paideia] D-N · phase banner each session, and
`/paideia status` prints it on demand — no restart needed.

Next steps:
  1. Drop PDFs/MDs into materials/{lectures,textbook,homework,solutions}/
  2. /paideia ingest        ← PDFs → converted/*.md (LaTeX)
  3. /paideia analyze       ← build patterns + coverage
  4. /paideia hwmap hot     ← see 🔥🔥 exam hotzones
```
