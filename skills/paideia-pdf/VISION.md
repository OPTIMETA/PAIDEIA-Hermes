# Vision-based PDF extraction (default for all course materials)

Supplemental to `SKILL.md`. **This is the pipeline `/paideia ingest` uses for every PDF in `materials/**`** — lectures, textbook, homework, and solutions alike.

`pdfplumber` was tried first as a "fast path" for prose-heavy material but proved unreliable on course content: even textbook pages that look like plain prose silently word-salad when they mix in equations, figures, multi-column layouts, or margin notes. Instead of maintaining a per-category heuristic with fallbacks that we'd need to retune for every course, we route everything through the same vision pipeline. It's slower, but reliable, and the wall-time cost is absorbed by parallelism (one agent per PDF).

## What `pdfplumber` gets wrong

Typical failure modes, any one of which is enough to justify skipping digital extraction:
- Equations fragmented: operators on one line, operands on the next
- Variables and subscripts on separate lines
- Multi-column content interleaved into alternating rows
- Greek letters preserved but structure (fractions, integrals, bras/kets, sums, vectors) lost
- Figure captions fused into adjacent body text
- Margin notes or headers/footers injected mid-paragraph
- Markdown looks like a bag-of-tokens dump despite the PDF being "digital"

These failures are silent — the extraction completes, the file gets written, and you only notice when `/paideia analyze` tries to build patterns out of garbage. By the time you catch it, the downstream course-index is already poisoned. Vision avoids the failure mode entirely.

## Pipeline

```
materials/<cat>/X.pdf
    ├─(pd_render.py: dpi=160, ≤1800px, one page at a time)
    │      → converted/<cat>/_pages/X/p01..pNN.png
    └─(parallel Agent per file, vision Read of PNGs)→ converted/<cat>/X.md
```

One agent per PDF, spawned in parallel. Each agent handles only its own file's page images — no cross-file writes — so they don't step on each other. For a 13-lecture course this gives ~4–7 min wall time instead of hours of serial work.

## Step 1 — Render pages to PNG

```bash
python3 "${PAIDEIA_PLUGIN_ROOT}/pd_render.py" \
  materials/lectures/Lecture1.pdf converted/lectures/_pages/Lecture1
```

One command does rasterize **and** downscale. It prints one PNG path per line.
Do not hand-roll this in inline Python — the script is the single source of
truth for three constraints that are easy to get subtly wrong:

**`dpi=160`** is the sweet spot: readable math, reasonable file size. Lower and sub/superscripts blur; higher just burns disk.

**Streaming, one page at a time.** `convert_from_path()` without `first_page`/`last_page` decodes the entire PDF into memory first: a 120-page chapter at `dpi=160` peaks at ~3 GB, versus ~47 MB streaming. Textbook chapters are exactly the case that OOMs.

**Padding sized to the page count.** A fixed `p{i:02d}` sorts `p100` between `p10` and `p11`, and the agent reads pages in sorted order — the transcript comes out scrambled with nothing to flag it. The script pads to the width of the total instead (`p001.png … p120.png`).

## Step 2 — The 2000px ceiling (already enforced by Step 1)

**Critical constraint.** Claude's many-image requests reject any image whose long edge exceeds ~2000 px with:

> An image in the conversation exceeds the dimension limit for many-image requests (2000px). Run /compact to remove old images from context, or start a new session.

Slide decks at `dpi=160` rendered from 16:9 PDFs routinely produce 4267×2400 PNGs, which blows past that. `pd_render.py` caps every page at 1800 px on the long edge (LANCZOS, safety margin under 2000) **as it writes it**, so an oversized PNG never lands on disk in the first place.

This ordering is the point: an agent that starts reading before a separate resize pass has run captures the oversized image into its context, and the request dies on the way to the model — the whole agent-run wastes. Rendering and resizing in one pass removes the window entirely. If you ever bypass the script, resize first, agents second.

## Step 3 — Parallel agents, one per file

Spawn a separate `general-purpose` agent per PDF, in parallel, backgrounded. Each agent handles only its own file's page images — no cross-file work — so they don't race on writes.

### Prompt template

```
You are transcribing a <domain> PDF to clean markdown using vision.
pdfplumber is unreliable on course materials (it splits equations
across lines and interleaves columns), so we render each page and
read it visually.

Input: the page images in <abs_path>/_pages/<stem>/ — read them in
       sorted filename order (p01.png, p02.png, … ; padding width
       depends on the page count). NN pages, each ≤1800px long edge.
Output: overwrite <abs_path>/<stem>.md

Procedure:
1. Read each page image with the read_file tool — **one at a time**, not in
   parallel batches, to stay under the per-request image-dimension budget.
   After reading and transcribing a page, move to the next.
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

**Sequential read is non-negotiable.** Even though individual images are under the per-image ceiling, reading many in parallel batches the agent's request and trips the many-image dimension limit again. Instruct the agent explicitly to read → transcribe → next.

## Step 4 — Cleanup

After all agents report done and you've spot-checked the markdown, delete the `_pages/` scratch dirs. These are ~5–25 MB per PDF; they have no downstream use.

```bash
rm -rf converted/*/_pages
```

Leave `_pages/` around only while a re-run is possible — once the markdown is verified, the PNGs are waste.

## Quality notes (from a real course run)

Validated on a 13-lecture Quantum Mechanics course, ~208 pages re-extracted:

- **0 `[?]` markers needed.** At `dpi=160` every equation, subscript, bra-ket, partial derivative, operator hat, and Greek letter was legible.
- Two of the initial agents failed on the oversized-image error because they started reading before the separate resize pass had run. That race is what motivated folding the resize into `pd_render.py` itself, so no oversized PNG ever exists on disk.
- Output quality vs `pdfplumber`: equations render as `$$\hat H = -\frac{\hbar^2}{2m}\partial_x^2 + V(x)$$` instead of `ℏ ∂ p2 ℏ 2 ∂ 2 p ̂ =  H  = + V ( x )  Ĥ = − + V ( x )`. Night and day.
- Blank final pages are common (title separators, thank-you slides). Agents correctly mark them `*[blank]*`.

Equivalent wins are expected across any math/physics course: linear algebra (matrices, tensor products), E&M (vector calculus, Maxwell's equations), statistical mechanics (partition functions, integrals), discrete math (summations, recurrences, binomial identities), real analysis (limits, ε-δ proofs), complex analysis (contour integrals, residues). Textbook chapters ingest equally cleanly — `pdfplumber`'s "prose is fine" turned out to be false once equations, figures, or multi-column layouts entered the page.

The `<domain>` placeholder in the prompt is the only thing that changes per course — fill it with whatever the course is about (e.g., "quantum mechanics", "discrete mathematics", "real analysis").

## When NOT to use this pipeline

- **Hand-written answer PDFs** — use the `vision-ocr` skill instead. It's tuned for noisy ink, variable layouts, and the error-tolerant strategy-grading downstream. Hand-writing is a different noise profile than printed slides/books.
- **Arbitrary PDFs outside the plugin's scope** (e.g., the user wants a quick text dump, or is merging/splitting PDFs) — use `pdfplumber` / `pypdf` / `pytesseract` per `SKILL.md` for ad-hoc work; the vision pipeline exists specifically for *course-material ingestion into a faithful LaTeX knowledge base*.

## TL;DR

Every `materials/**/*.pdf` → `pd_render.py` (renders at `dpi=160` and caps at ≤1800 px in one streaming pass) → one agent per PDF in parallel → each agent reads images **sequentially, in sorted filename order** → clean LaTeX markdown out → `rm -rf converted/*/_pages`.
