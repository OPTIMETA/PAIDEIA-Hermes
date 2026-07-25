---
description: Convert all course-material PDFs (lectures, textbook, homework, solutions) to markdown via the vision pipeline — one parallel agent per file, LaTeX-faithful transcription. Idempotent — skips already-converted files.
argument-hint: [--force to reconvert everything]
---

## Output language

Read `INTERFACE_LANG` from `.course-meta` (default `en`). All user-facing prose must be in that language. Keep in English regardless: file paths, slash command names, table column headers (`Category`, `Converted`, `Skipped (already done)`, `Failed`), and provenance comments.

Load `skills/paideia-pdf/SKILL.md`, `skills/paideia-pdf/VISION.md`, and `skills/paideia-course-builder/SKILL.md`.

Arguments: the arguments provided above

## Routing rule

**Every PDF in `materials/**` goes through the vision pipeline.** `pdfplumber` is unreliable in practice on course materials — even prose-heavy textbook pages mix in equations, figures, and multi-column layouts that break digital extraction silently. Rather than maintaining a routing heuristic and a fallback that we'd need to keep tuning per course, we route everything through the same pipeline: render → resize → parallel vision agents → clean LaTeX markdown.

| Source | Method |
|---|---|
| `materials/**/*.pdf` | **Vision pipeline** (`pd_render.py` → `dpi=160`, ≤1800 px, one parallel `general-purpose` agent per PDF, sequential `Read` inside the agent) |
| `materials/**/*.md` | Copy-through with provenance header |

Hand-written answer PDFs (`answers/*.pdf`) are a separate path — handled by `/paideia grade`, not `/paideia ingest`.

## Procedure

### Step 1 — Discovery

Scan `materials/` recursively for `.pdf` and `.md`. Classify by subfolder: `lectures`, `textbook`, `homework`, `solutions`. Ambiguous files (PDFs sitting in `materials/` root) get one prompt to categorize.

Apply idempotence: if `converted/<cat>/<stem>.md` exists and is newer than the source, skip — unless `--force` is in `the arguments provided above`. Log skip count.

### Step 2 — Copy-through for `.md` sources

For each `.md` already in `materials/`: mirror to `converted/<cat>/<stem>.md` verbatim, adding:

```
<!-- SOURCE: materials/<cat>/<stem>.md, copied <YYYY-MM-DD>, method: passthrough -->
```

### Step 3 — Render each PDF to page PNGs (dpi=160, ≤1800 px long edge)

Run the bundled renderer once per PDF. It rasterizes **and** downscales in a
single streaming pass — do not hand-roll this in inline Python:

```bash
python3 "${PAIDEIA_PLUGIN_ROOT}/pd_render.py" \
  "materials/<cat>/<stem>.pdf" "converted/<cat>/_pages/<stem>"
```

It prints one PNG path per line (`p01.png`, `p02.png`, … zero-padded to the page
count, so a 120-page chapter yields `p001.png … p120.png` and sorted order stays
page order).

Three things it guarantees that an inline loop does not:

- **Memory.** It renders one page at a time. Decoding a whole PDF at once costs
  ~3 GB for a 120-page chapter at `dpi=160`; streaming holds ~47 MB. That is the
  difference between ingesting a textbook and being told to split the file.
- **The 2000 px ceiling.** Every page is capped at 1800 px on the long edge
  before it is written, so no oversized PNG ever reaches disk for an agent to
  read. 16:9 slides at `dpi=160` render at ~4267×2400 and would otherwise
  hard-fail the many-image request — and an agent that already pulled the
  oversized image into context wastes its entire run.
- **Page order.** Padding is sized to the page count, so `p100` can never sort
  between `p10` and `p11`.

`dpi=160` is the sweet spot: math stays legible, file sizes stay reasonable.
Override with `--dpi=` / `--max-px=` only if you have a specific reason.

### Step 4 — Confirm the render before spawning agents

`pd_render.py` exits non-zero on a missing/unreadable PDF. Check each render
produced the expected page count before moving on; a PDF that failed here must
be reported in the summary table's `Failed` column, not silently skipped.

### Step 5 — Spawn one `general-purpose` agent per PDF, in parallel, backgrounded

Each agent touches only its own file's `_pages/<stem>/` directory, so writes don't race. Use this prompt template (fill in the bracketed values):

```
You are transcribing a <domain> PDF to clean markdown using vision.
pdfplumber is unreliable on course materials (it splits equations
across lines and interleaves columns), so we render each page and
read it visually.

Input: the page images in <abs_path>/_pages/<stem>/ — read them in
       sorted filename order (p01.png, p02.png, … ; padding width
       depends on the page count). NN pages, each ≤1800 px long edge.
Output: overwrite <abs_path>/<stem>.md

Procedure:
1. Read each page image with the read_file tool — one at a time, not in
   parallel batches, to stay under the per-request image-dimension
   budget. After reading and transcribing a page, move to the next.
2. Transcribe each page into markdown, preserving the page's reading
   order (not raw column order).
3. Format math in LaTeX: inline $...$, display $$...$$. Render hats,
   hbars, partials, bras/kets, sums, vectors, operators faithfully.
   If a symbol is genuinely unreadable, write [?] — do not guess.
4. Use ## for section/slide titles. Prepend ### Page N anchors so
   downstream tools can cite pages.
5. Preserve bullet hierarchy, numbered postulates/theorems/definitions,
   labeled equations, tables.
6. Skip-mark truly empty pages as *[blank]*.
7. Do NOT summarize — faithfully transcribe only what is on the page.
8. For heavy diagrams, write one italic line *Figure: [description]*
   rather than pixel-wise transcription.

Top of file must be:
<!-- SOURCE: materials/<cat>/<stem>.pdf, extracted <YYYY-MM-DD>, method: vision -->

# <Title>

Write the full file once at the end. Report: page count handled and
any [?] symbols you marked.
```

`<domain>` should be whatever the course is about (quantum mechanics, linear algebra, discrete math, real analysis, E&M, etc.) — infer from the materials or ask the user once if unclear.

**Sequential `Read` inside the agent is non-negotiable.** Parallel batches of `Read` calls trip the many-image dimension limit again even though each individual PNG is under the per-image ceiling.

Wait for all agents to report done. Spot-check one or two output files before moving on (equations should read top-to-bottom as coherent LaTeX; page anchors should be present).

### Step 6 — Cleanup

After all agents finish and outputs look sane, delete the `_pages/` scratch directories:

```bash
rm -rf converted/*/_pages
```

These are ~5–25 MB per PDF and have no downstream use. Keep them only if you plan to re-run immediately.

## Summary output

After ingest completes, print:

| Category | Converted | Skipped (already done) | Failed |
|---|---|---|---|
| lectures | N | M | F |
| textbook | ... | ... | ... |
| homework | ... | ... | ... |
| solutions | ... | ... | ... |

End with (in $INTERFACE_LANG):
"Next: run `/paideia analyze` to generate patterns.md, coverage.md, summary.md."

If any file failed (encryption, corrupted PDF, agent timeout), list at the end with the specific failure reason and suggested workaround:
- Password-protected PDF → `qpdf --password=... --decrypt in.pdf out.pdf` first
- Agent crashed mid-run → `/paideia ingest --force` to retry just that file
- `pd_render.py` reports 0 pages → poppler can't read the file; confirm `pdfinfo <pdf>` works
