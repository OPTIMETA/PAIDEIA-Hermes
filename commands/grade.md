---
description: "Grade user's answer PDF (hand-written, scanned) against reference solution. OCR engine is selectable: claude (default, no extra install), ollama (Qwen3-VL local), or tesseract. Then strategy-based grade."
argument-hint: "[--ocr=claude|ollama|tesseract] [optional path to answer file; default = most recent in answers/]"
---

## Output language

Read `INTERFACE_LANG` from `.course-meta` (default `en`). All user-facing prose — chat output, grade-table commentary, the OCR quality escape-hatch menu — must be in that language. Keep in English regardless: file paths, slash command names (`/paideia grade`, `/paideia blind`, …), pattern IDs (P1, P2…), YAML keys, LaTeX, OCR engine names (`claude`, `ollama`, `tesseract`), and the grade table's column headers (`P#`, `Pattern`, `Vars`, `End form`, `Overall`). `pd_vision_ocr.py` reads `INTERFACE_LANG` from `.course-meta` on its own to set the VLM's prose-language rule and the tesseract `lang=` code, so the bash invocations below don't need to pass it explicitly.

Load `skills/paideia-vision-ocr/SKILL.md`, `skills/paideia-pdf/SKILL.md`, and `skills/paideia-answer-processing/SKILL.md`.

Arguments: the arguments provided above

If `the arguments provided above` contains `--ocr=<engine>`, that overrides the default for this call. Otherwise read `OCR_ENGINE` from `.course-meta` in CWD (one line of the form `OCR_ENGINE: <engine>`). If `.course-meta` is absent or the key is missing, default to `claude`.

Target answer file: the non-flag positional in `the arguments provided above`. If no positional, find the most recently modified file in `answers/` (not `answers/converted/`).

Follow the answer-processing skill pipeline:

1. **Identify.** Is target a `.pdf` or `.md`?
   - `.pdf` → proceed to step 2
   - `.md` → skip step 2, go to 3

2. **Convert PDF → MD.** Dispatch on the selected OCR engine:

   ### 2a. `claude` (default) — native the model's vision, no external model

   ```bash
   STEM=$(basename "answers/<stem>.pdf" .pdf)
   TMPDIR="answers/converted/.tmp-${STEM}"
   python3 "${PAIDEIA_PLUGIN_ROOT}/pd_render.py" --dpi=200 \
     "answers/${STEM}.pdf" "$TMPDIR"
   ```

   The same renderer `/paideia ingest` uses — rasterize and downscale in one
   streaming pass. It caps each page at 1800 px on the long edge, which matters
   here for cost as much as for limits: 200-DPI letter pages come out
   ~1700–2200 px and each one costs ~0.5–1.0 MB of image tokens, fine for 2
   pages and brutal for 10. Page numbers are zero-padded to the page count, so
   **sorted filename order is page order** even past 99 pages.

   This produces `$TMPDIR/p01.png`, `$TMPDIR/p02.png`, ... Now **use the read_file tool on each PNG in sorted order** and synthesize clean markdown yourself, following the transcription prompt contract from `skills/paideia-vision-ocr/SKILL.md`:

   - Prose stays in its original language (English, Korean, etc.) — do not translate.
   - Math as `$...$` / `$$...$$`.
   - Preserve problem numbering (P1, (1), (a), ...).
   - Do NOT interpret or grade — pure transcription.
   - `[?]` for ambiguous glyphs.
   - Skip crossed-out work.
   - Markdown only.

   Write the synthesized result to `answers/converted/<stem>.md` with header:

   ```markdown
   # Vision-OCR transcription

   <!-- SOURCE: <stem>.pdf, claude-vision (native), N pages -->

   ## Page 1

   <transcription>

   ## Page 2

   <transcription>
   ```

   Clean up: `rm -rf "$TMPDIR"`.

   ### 2b. `ollama` — local Qwen3-VL 8B

   ```bash
   python3 "${PAIDEIA_PLUGIN_ROOT}/pd_vision_ocr.py" --engine=ollama \
     "answers/<stem>.pdf" "answers/converted/<stem>.md"
   ```

   Uses `qwen3-vl:8b` via ollama. The script reads `INTERFACE_LANG` from `.course-meta` in CWD so the prose-language rule in the VLM prompt matches the course's language. Auto-falls back to tesseract on any exception (timeout / ollama down / model missing). Tier is recorded in the file header. See `skills/paideia-vision-ocr/SKILL.md` for details.

   ### 2c. `tesseract` — explicit, skip ollama

   ```bash
   python3 "${PAIDEIA_PLUGIN_ROOT}/pd_vision_ocr.py" --engine=tesseract \
     "answers/<stem>.pdf" "answers/converted/<stem>.md"
   ```

   Pure pytesseract (`eng` if the course's `INTERFACE_LANG=en`, `eng+kor` if `ko` — also read from `.course-meta`). Fastest, lowest fidelity on handwriting.

3. **Identify reference solution.** Based on the answer filename stem:
   - `hw3.pdf` → `converted/solutions/hw3_sol.md` (or `converted/solutions/hw3.md`)
   - `diagnostic.pdf` → `quizzes/diagnostic_answers.md`
   - `mock_<ts>.pdf` (or `exam_<ts>.pdf`) → `mock/exam_<ts>_sol.md`. The scan is
     usually timestamped later than the exam, so the `<ts>` rarely matches —
     if there is no exact match, fall back to the most recent `mock/exam_*_sol.md`.
   - `<topic>_<ts>.pdf` → `quizzes/<topic>_<ts>_answers.md` (this generic rule
     fires only after the `mock_`/`twin_`/`chain_` prefixes above are ruled out)
   - `twin_<id>_<ts>.pdf` → `twins/<id>_<ts>_sol.md`; if the `<ts>` doesn't
     match exactly, fall back to the most recent `twins/<id>_*_sol.md`.
   - `chain_<ts>.pdf` → `chain/<ts>_sol.md`; same as mock, the scan `<ts>`
     rarely matches the generated one, so fall back to the most recent
     `chain/*_sol.md`.
   If cannot resolve, ask the user to specify.

4. **Strategy-based grading per problem:**
   - Pattern match (did the user invoke the right pattern from `course-index/patterns.md`?)
   - Variable choice (did they hold the right things fixed?)
   - End form (does their final expression structure match?)
   - Completeness (where did they stop?)

5. **Render compact grade table** (≤ 15 lines in chat):
   ```
   | P# | Pattern | Vars | End form | Overall |
   |---|---|---|---|---|
   ```
   Plus one closing line (in $INTERFACE_LANG): "Dominant issue: <type>. Next drill: /<command> <target>."

6. **Log errors.** Append each non-✅ entry to `errors/log.md` in the YAML format from answer-processing SKILL.md.

7. **Do NOT** print the full reference solution. The user can open it themselves if they want to study.

8. **Archive the graded PDF.** After the grade table and the `errors/log.md` append both succeed, move the original PDF out of `answers/` so the next `/paideia grade` invocation doesn't keep re-picking the same "most recently modified" file when the user uploads a newer scan:

   ```bash
   if [ -f "answers/${STEM}.pdf" ]; then
     mkdir -p answers/_archive
     TS=$(date +%Y%m%d-%H%M%S)
     mv "answers/${STEM}.pdf" "answers/_archive/${STEM}_${TS}.pdf"
     echo "archived: answers/${STEM}.pdf → answers/_archive/${STEM}_${TS}.pdf"
   fi
   ```

   `answers/_archive/` is in `.gitignore` (scans are bulky + personal); the converted `answers/converted/${STEM}.md` stays put and IS committed, so the grade trail is preserved in version control. Skip this archive for the `.md`-only path (step 1's `.md` branch) — there's no original PDF to move.

## OCR quality escape hatch

Inspect the `<!-- SOURCE: ... -->` / `<!-- TIER: ... -->` header comment in `answers/converted/<stem>.md` first.

- **Tier 0 (`claude-vision`)** or **Tier 1 (`qwen3-vl:8b`) succeeded:** grade normally. Quality is usually good enough for strategy matching even on messy handwriting.
- **Tier 1b fallback (`tesseract` auto-fallback)** was used, **Tier 2 (`tesseract` explicit)**, the MD is <100 chars, or mostly garbled — print the menu below in $INTERFACE_LANG, keeping slash commands and paths verbatim:
  ```
  OCR quality is low (grading reliability degraded).
  Options:
    (a) /paideia grade --ocr=claude <pdf>   ← retry with the model's vision (no extra install)
    (b) re-scan brighter / larger, then /paideia grade again
    (c) type the answer into .md and save it to `answers/converted/<stem>.md`, then /paideia grade
    (d) skip grading and use /paideia blind <problem-id> to verbalize the strategy instead
  ```

## When both .pdf and .md exist

If `answers/<stem>.pdf` AND `answers/converted/<stem>.md` both exist and the `.md` is recent (edited within 1 hour), use the `.md` directly (user likely manually cleaned OCR output).
