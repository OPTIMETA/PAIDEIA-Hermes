# Changelog

All notable changes to PAIDEIA-Hermes. Versions follow the `plugin.yaml`
`version:` field.

## 0.4.0 — 2026-07-25

Correctness and robustness pass over the whole plugin. No workflow changes: the
same commands produce the same artifacts in the same places. Every fix below is
covered by `tests/` (98 tests, stdlib only — `./tests/run.sh`).

### Fixed — data integrity

- **`errors/log.md` no longer breaks on LaTeX.** A summary containing `\int` or
  `\frac` went into the double-quoted YAML scalar unescaped, so YAML read `\i`
  as an unknown escape and rejected **the entire file** — silently emptying every
  weakness surface (weakmap, status, banner, `/paideia quiz weakmap`) built on
  it. Backslashes and quotes are now escaped; `problem_id`/`pattern`/
  `error_type`/`source` stay unquoted plain scalars so `PATTERN_RX` keeps
  matching them, with colons and `#` sanitized instead.
  Two follow-on holes in the same sanitizer, both found by the seeded fuzz added
  alongside it: stripping YAML indicators before trimming whitespace re-exposed
  the next one (`"' [x"` → `[x`, which reopens the crash), and a bare `=` carries
  YAML's `value` tag, which makes a strict loader raise on the *file* rather than
  the entry. 6000 fuzzed entries now round-trip.
- **A newline in a `.course-meta` value can no longer forge a key.** The file is
  line-oriented, so `weak="x\nEXAM_DATE: 1999-01-01"` wrote a second key the
  reader treated as real while silently truncating the intended value. Values are
  flattened to one line on write.
- **`COURSE_NAME: C# Programming` no longer parses as `C`.** A trailing comment
  now has to be introduced by whitespace, in all three parsers that keep
  standalone copies of the rule (`pd_meta`, `pd_doctor`, `pd_vision_ocr`) — with
  a test pinning them to identical behaviour.
- **Korean OCR output is written as UTF-8.** `pd_vision_ocr.py` wrote its
  transcription with no explicit encoding, falling back to the locale encoding —
  mojibake or a hard failure under a C/POSIX locale.
- **Course folders whose names contain glob metacharacters work.** A folder like
  `Math [2026] Final` made `glob.glob()` match nothing, so quizzes and weakmap
  reports became invisible: the phase silently degraded from `drill` to `diag`
  and the banner lost its verdict. Both call sites now use `Path.glob`.
- **`answers/_archive/` is actually git-ignored.** `commands/grade.md` promised
  graded scans stayed out of version control; the generated `.gitignore` never
  listed the directory. Existing course folders get the pattern appended on the
  next scaffold, leaving hand-written rules untouched.

### Fixed — atomicity

- **`.course-meta` is written atomically** (temp file + `os.replace`). A write
  interrupted mid-flight left a truncated file behind — and since that file's
  *existence* is what marks a folder as a course, the result was a workspace
  that looked initialized while every subcommand refused to run. `errors/log.md`,
  `.gitignore` and `PAIDEIA.md` seeding use the same path.

### Fixed — stability

- **PDF rendering streams one page at a time.** Decoding a whole PDF up front
  peaked at **3031 MB** for a 120-page chapter at `dpi=160`; it now peaks at
  **47 MB** (measured, same file). The old ingest spec listed "split the PDF
  first" as the workaround for the resulting OOM — that advice is gone because
  the cause is.
- **Page numbering is padded to the page count.** Fixed 2-digit padding sorted
  `p100.png` between `p10.png` and `p11.png`, and agents read pages in sorted
  order — a 100+ page chapter (ordinary for a textbook) was transcribed in
  scrambled sequence with nothing to signal it. Now `p001.png … p120.png`.
- **PDF page numbering is correct even when poppler can't count.** The
  fallback path (no usable `pdfinfo`) guessed a 3-wide pad, reintroducing the
  `p1000` / `p999` ordering bug it was meant to fix past 999 pages. It now
  counts before it names.
- **The atomic write keeps file permissions.** `mkstemp()` hardcodes `0600`, so
  moving to temp-file-plus-rename silently made `.course-meta`, `.gitignore` and
  `PAIDEIA.md` owner-only. A rewrite now carries the existing file's mode, and a
  new file is created with `os.open(..., 0o666)` so the umask applies exactly as
  it would to any other file — hardcoding `0644` instead would have overridden a
  deliberately strict umask, and reading the umask to compute the mode cannot be
  done without briefly setting it, racing every other thread creating a file.
- **Control characters can't reach the terminal through a course name.**
  `COURSE_NAME` is echoed by the session banner and the status line, so an escape
  sequence stored in `.course-meta` was written to the terminal on every session
  start in that folder. `errors/log.md` already scrubbed these; `.course-meta`
  now does too.

### Fixed — a broken course now reads as broken everywhere

A `.course-meta` that exists but parses to nothing left the four surfaces
disagreeing: `is_course()` said yes so the LLM subcommands ran, `/paideia status`
said "not a course folder — run `/paideia init` here" (which would have
overwritten the remains), the session banner went silent, and `/paideia doctor` —
the tool you run to diagnose exactly this — reported **all clear** while skipping
every workspace check. All four now agree it is a broken course and point at
`doctor`, which fails with a specific reason and still repairs what `--fix` can.

### Fixed — contradictions between specs and code

- **`/paideia grade` no longer risks launching the wrong OCR tier.** The
  `answer-processing` skill hard-coded the ollama invocation while
  `commands/grade.md` correctly dispatched on `OCR_ENGINE` (default `claude`).
  Both files are loaded for the same command, so a default-configured user could
  end up stalled on a 6 GB model they never pulled. The skill now dispatches.
- **"Latest weakmap" means one thing.** The specs said "most recent mtime", the
  code sorted by filename timestamp. They disagree after any `git clone`, which
  stamps every file with the checkout time — and the course folder is meant to be
  committed. The filename-order rule is now stated in both specs.
- **The acknowledgement line names no provider.** It read "handed to the agent
  (codex)" while both READMEs promise switching providers changes nothing.
- **Both init paths produce identical workspaces.** The interactive wizard wrote
  `.course-meta` by hand and called `doctor --fix`, which creates directories but
  no `.gitignore` and no `PAIDEIA.md`. It now routes through `/paideia init`, the
  single scaffolding implementation.
- **`/paideia init-course` is gone from the docs.** The `vision-ocr` skill told
  users `.course-meta` is written by `/paideia init-course` — twice. That
  subcommand does not exist; the dispatcher answers "unknown subcommand". The
  real command is `/paideia init` (`init-course.md` is the internal spec name for
  the interactive wizard).
- **`hwmap` has one meaning again.** The `exam-drill` skill said
  `/paideia hwmap blind` "lists all 🔴 and 🔴🔴 entries", and `analyze.md` sent
  users there to "review all blind spots" — but `hwmap.md` treats `blind` as a
  legacy alias for `hot` and returns exam-*hot* zones. Worse, the blind-spot
  reading inverts the plugin's core thesis, stated four lines above it in the
  same skill file: a section with no HW is the professor signalling the topic is
  off the exam, not a hazard to drill. Both call sites now match `hwmap.md`, and
  `analyze.md` surfaces only 🔴🔴 Critical blinds (no coverage *and* a declared
  weak zone), which are the ones that genuinely warrant attention.
- **The "drills never make PDFs" rule names its one exception.** The rule is
  scoped to drill artifacts, but `/paideia cheatsheet --pdf` loads the same skill
  and must render a PDF.
- **`/paideia alt`'s "no export found" message follows `INTERFACE_LANG`.** It was
  a hard-coded Korean sentence in a spec whose own header requires otherwise.

### Added

- **`tests/`** — 98 tests on stdlib `unittest`; no pytest, no venv, no install
  step (`./tests/run.sh`). Four of them check `errors/log.md` against a real YAML
  parser and skip without one, reporting `OK (skipped=4)`. Includes contract
  tests that pin `pd_doctor`'s deliberate
  standalone copies of `SKELETON`/`META_KEYS`/the errors seed to their sources,
  assert every LLM subcommand has both a command spec and a skill that exists on
  disk, and — because a spec is an instruction to an agent, so a wrong reference
  becomes a wrong action — reject any spec that names a subcommand the
  dispatcher would refuse or a bundled script that isn't shipped.
- **`/paideia doctor` checks the plugin's own payload** — 24 scripts, command
  specs and skill files. A truncated clone or stale symlink previously passed
  every check and failed later, mid-command, as "no command spec file found".
- **`/paideia init` rejects a malformed `exam=` date** instead of scaffolding a
  course whose D-N countdown and phase tracking silently never appear.
- **`pd_render.py` is wired in.** It shipped unreferenced while three spec files
  inlined their own hand-rolled render+resize snippets; those snippets are the
  ones that carried the OOM and page-ordering bugs. `/paideia ingest` and
  `/paideia grade`'s claude tier now both call it.

### Changed

- **`/paideia doctor` grades dependencies by what actually breaks.** Every Python
  dep was reported as a warning, including `pdf2image` and `pillow` — required by
  every OCR tier, exactly like poppler, which was already a failure. Required and
  optional deps are now separated, and each optional one says which command it
  serves.
- **`/paideia doctor` probes every dependency in one interpreter launch**
  instead of one per dependency. Doctor is interactive — the `init` wizard runs
  it, and it is the first thing you reach for when something breaks — and it was
  spending most of its runtime on process startup. A dependency the batch
  doesn't report on still falls back to its own subprocess, so one pathological
  module can't hide the rest.
- **`install.sh --copy` excludes `.git/`, `tests/` and `__pycache__/`** instead of
  copying the whole checkout — tens of MB of history the plugin never reads, plus
  `.pyc` files compiled by whichever interpreter ran last.

## 0.3.0

- Slack/gateway support via the `pre_gateway_dispatch` hook.

## 0.2.0

- Validated on codex; doctor probes the agent's `python3` rather than hermes'
  venv interpreter.

## 0.1.0

- Initial port of OPTIMETA/PAIDEIA to a hermes-agent plugin.
