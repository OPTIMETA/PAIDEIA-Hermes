<h1 align="center">ΠΑΙΔΕΙΑ · Paideia <sub>for Hermes</sub></h1>

<p align="center">
  <strong>Your course. Your patterns. Your errors. Your cheatsheet.</strong><br>
  <em>A <a href="https://github.com/NousResearch/hermes-agent">hermes-agent</a> plugin that turns your own materials into a permanent, editable, per-course study graph — every artifact shaped by you, not by a generic syllabus.</em>
</p>

<p align="center">
  <a href="https://github.com/OPTIMETA/PAIDEIA-Alt"><img height="30" src="https://img.shields.io/badge/Exam_Radar-OPTIMETA_Alt_plugin-333333?style=for-the-badge&labelColor=000000&color=333333" alt="Exam Radar — OPTIMETA Alt plugin"></a>
</p>

<p align="center">
  <sub><em>Capture lectures with <a href="https://github.com/OPTIMETA/PAIDEIA-Alt"><strong>Exam Radar</strong></a> — OPTIMETA's Alt plugin — and study them with Paideia. Pipe a roadmap straight in with <code>/paideia alt</code>.</em></sub>
</p>

<p align="center">
  <img src="https://img.shields.io/badge/License-MIT-333333?style=flat-square&labelColor=000000&color=333333" alt="License: MIT">
  <img src="https://img.shields.io/badge/hermes--agent-000000?style=flat-square&logo=anthropic&logoColor=white&labelColor=000000&color=000000" alt="hermes-agent">
  <img src="https://img.shields.io/badge/Plugin-000000?style=flat-square&labelColor=000000&color=000000" alt="Plugin">
  <img src="https://img.shields.io/badge/Model--agnostic-000000?style=flat-square&labelColor=000000&color=000000" alt="Model-agnostic">
  <img src="https://img.shields.io/badge/Markdown-000000?style=flat-square&logo=markdown&logoColor=white&labelColor=000000&color=000000" alt="Markdown">
  <img src="https://img.shields.io/badge/Python-000000?style=flat-square&logo=python&logoColor=white&labelColor=000000&color=000000" alt="Python">
  <img src="https://img.shields.io/badge/Ollama-000000?style=flat-square&logo=ollama&logoColor=white&labelColor=000000&color=000000" alt="Ollama">
  <img src="https://img.shields.io/badge/Qwen3--VL-000000?style=flat-square&labelColor=000000&color=000000" alt="Qwen3-VL">
  <img src="https://img.shields.io/badge/Tesseract-000000?style=flat-square&labelColor=000000&color=000000" alt="Tesseract">
  <img src="https://img.shields.io/badge/LaTeX-000000?style=flat-square&logo=latex&logoColor=white&labelColor=000000&color=000000" alt="LaTeX">
  <img src="https://img.shields.io/badge/Obsidian-000000?style=flat-square&logo=obsidian&logoColor=white&labelColor=000000&color=000000" alt="Obsidian">
</p>

<p align="center">
  <a href="./README.ko.md">한국어 README</a>
  &nbsp;·&nbsp;
  <a href="https://github.com/OPTIMETA/PAIDEIA"><strong>PAIDEIA</strong> — the original (Claude Code)</a>
  &nbsp;·&nbsp;
  <a href="https://taewoopark.com"><strong>taewoopark.com</strong> — author site</a>
</p>

> **A port, not a rewrite.** PAIDEIA-Hermes is [OPTIMETA/PAIDEIA](https://github.com/OPTIMETA/PAIDEIA) — originally a Claude Code plugin — re-expressed on [NousResearch/hermes-agent](https://github.com/NousResearch/hermes-agent)'s own extension surfaces. Same formation cycle, same on-disk layout, same MIT license. Because hermes is **model-agnostic**, the exact same plugin runs on whatever provider you point hermes at: if your `~/.hermes/config.yaml` uses `provider: openai-codex`, Paideia is driven by **Codex (gpt-5.5)**; switch with `/model` and nothing about Paideia changes.

> **Security notice.** PAIDEIA-Hermes installs as a hermes-agent plugin (`hermes plugins install …`) and never asks you to download a `.zip`, run an `.exe`, or use any installer. Any other repository using the PAIDEIA name is not affiliated with this project unless it is explicitly linked from this README.

<p align="center">
  <em>Generic study tools teach you the average syllabus. Paideia teaches you <strong>your</strong> syllabus —<br>
  from your professor's notes, your HW emphases, your handwriting, your errors. Every artifact is a markdown file you can edit.</em>
</p>

---

## What Paideia means

In ancient Greece, **Παιδεία** was never the deposit of facts into a passive student. It was the lifelong formation of a complete human being — through structured encounter with primary texts, guided practice under a master, and reflective dialogue that folds feedback into deeper revision.

This plugin implements that cycle for the specific, bounded problem of **exam preparation** in math, physics, and engineering courses:

```
  ingest ──▶ analyze ──▶ drill ──▶ grade ──▶ weakmap ──▶ cheatsheet
     ▲                                                        │
     └────────────────── feedback loop ───────────────────────┘
```

Every stage produces a markdown artifact that lives in your course folder forever. Nothing is ephemeral. Nothing is hidden behind an API. Nothing stops working when the next funding winter hits — and because hermes is model-agnostic, nothing breaks when you change models.

---

## What generic study tools can't do

Most study tools can't personalize to *your* course, *your* professor, or *your* mistakes — because the product they sell is a generic curriculum.

- **Coursera, edX, Khan Academy** — fixed curriculum; no idea what your professor actually emphasizes.
- **Quizlet, Anki, Brainscape** — you manually curate every card; nothing derives patterns from your own solution manuals.
- **Chegg, Course Hero** — generic solution manuals; not organized around your course's recurring idioms.
- **ChatGPT Study Mode, Gemini "Deep Study", NotebookLM** — no persistent per-course state. Every new session starts cold, and last week's mistakes don't shape this week's drill unless you re-upload and re-explain.

None of them *form* understanding around the specific material in front of you. Paideia does the opposite: every artifact is derived from *your* folder — lecture notes, textbook chapter, HW, solutions, handwritten attempts — and accumulates permanently in plain markdown you can edit.

| Axis | Paideia | Typical edu-SaaS / LLM chat |
|-----|---------|------------------------------|
| Solution patterns (`P1..Pk`) | Extracted from *your course's* own solutions, citing your own files | Generic textbook list, or none |
| Drill priority | Weighted by *your professor's* HW emphasis (HW density = exam tier) | Fixed curriculum, or your own guesswork |
| Cheatsheet | Built from *your* `errors/log.md` — whatever you actually got wrong | Boilerplate from the syllabus |
| Per-course state across sessions | Permanent markdown + YAML, grows as you work | Conversation resets; paid tier for history |
| Editing an artifact you disagree with | Open the `.md` in any editor, save | Read-only UI |
| Version history of your own understanding | `git log` / `git diff` any artifact | Not surfaced |
| Where the artifacts live | Your disk, as text | Remote DB, exportable only with paid tier |
| Which model does the work | **Whatever you configured** — Nous, OpenAI/Codex, Anthropic, OpenRouter, local | Vendor-locked |

The plugin uses hermes (which drives a paid or local model of your choice) to do the heavy lifting, but everything it produces lives on your disk as plain markdown. Pause your subscription, swap providers, go fully local — the course-index, patterns, error log, weakmaps, and cheatsheets are all still yours to open, read, edit, and diff. The scaffold is the plugin; the study graph is yours.

By default, OCR goes through the agent's own native vision (whatever multimodal model your hermes provider exposes). If you'd rather the handwritten PDFs never leave the machine, `ollama pull qwen3-vl:8b` is a one-time ~6 GB download that flips every subsequent OCR pass to local Qwen3-VL inference.

---

## The load-bearing principle: HW density = exam probability

Most "study smart" advice tells you to hunt your blind spots. That is **backwards**. The professor has *already told you* where the exam points live — by assigning homework. Sections with heavy HW coverage are 🔥🔥 Exam-primary. Sections with zero HW are ⚪ Low-risk, not "hidden traps". The professor's omission is the strongest possible signal that the topic is off the exam.

Paideia's ranking is explicit about this, and every drill command honors it by default:

| Tier | HW count on section | Treatment | Share of mock-exam points |
|------|---------------------|-----------|---------------------------|
| 🔥🔥 Exam-primary | 3+ | Drill hardest | ≥70% |
| 🔥 Exam-likely | 2 | Drill next | ~25% |
| 🟡 Exam-possible | 1 | Warm-pass review | ≤5% |
| ⚪ Low-risk | 0 | Reference only | 0 |

`/paideia quiz all`, `/paideia mock`, `/paideia hwmap hot` all weight output by this tiering. If you insist on drilling a ⚪ section, the plugin complies once and warns you that exam probability is low — your limited time is worth more than an imagined gotcha.

---

## The formation cycle, stage by stage

| Stage | What it does | Commands | Produces |
|-------|-------------|----------|----------|
| **Encounter** | Read the professor's signal | `/paideia ingest` | `converted/**/*.md` — every lecture, textbook chapter, HW, solution, as clean LaTeX markdown |
| **Structure** | Extract the grammar of the course | `/paideia analyze` | `course-index/{summary,patterns,coverage}.md` — topic tree, recurring solution patterns (P1..Pk), HW-density exam-tier ranking |
| **Practice** | Active recall weighted by what the professor actually tests | `/paideia quiz`, `/paideia twin`, `/paideia blind`, `/paideia chain`, `/paideia mock` | `quizzes/`, `twins/`, `chain/`, `mock/` — problems you solve on paper |
| **Reflection** | Your hand-written work becomes a grade | `/paideia grade` | `answers/converted/<name>.md` + `errors/log.md` — OCR via the agent's vision (default), Ollama/Qwen3-VL, or Tesseract; then strategy-based grading |
| **Diagnosis** | Errors compressed into a priority-ranked weakness report | `/paideia weakmap` | `weakmap/weakmap_<ts>.md` — append-only history |
| **Distillation** | One page, error-driven, printable | `/paideia cheatsheet`, `/paideia derive`, `/paideia pattern` | `cheatsheet/final.md`, `derivations/<slug>.md` — reference only what you actually need |

Supporting: `/paideia hwmap` surfaces HW-density exam-probability, `/paideia status` shows where you are in the cycle, `/paideia init` bootstraps a fresh course folder.

---

## Install

### Prerequisites

**Required**

- [hermes-agent](https://github.com/NousResearch/hermes-agent), on any provider (Nous Portal, OpenAI/Codex, Anthropic, OpenRouter, local, …).
- Python 3 + a Unix-style shell (`bash`/`zsh`; WSL2 on Windows).
- `poppler` (`pdftoppm`) — required by every OCR tier.
  - **macOS**: `brew install poppler tesseract tesseract-lang`
  - **Linux (Debian/Ubuntu)**: `apt-get install poppler-utils tesseract-ocr tesseract-ocr-kor`
- Python libs (lazy — only for ingest/grade/cheatsheet): `pip install pypdf pdfplumber pdf2image pillow reportlab pytesseract`

**Optional — only for `--ocr=ollama` (every page image stays on your machine)**

- `ollama` + `qwen3-vl:8b` (~6 GB). `brew install ollama` / [install script](https://ollama.com/install.sh), then `ollama pull qwen3-vl:8b`.

Run `/paideia doctor` any time to check all of the above (and `/paideia doctor --fix` to repair the permission-free ones). It probes the same `python3` your agent's terminal uses, so it reports what the agent can actually run.

### Install the plugin

```bash
hermes plugins install OPTIMETA/PAIDEIA-Hermes
hermes plugins enable paideia
```

Restart hermes; the `/paideia` command is now available in every session. Alternatives:

```bash
# B) git clone straight into the user-plugins dir
git clone https://github.com/OPTIMETA/PAIDEIA-Hermes ~/.hermes/plugins/paideia
hermes plugins enable paideia

# C) dev / local checkout (symlink — edits go live on the next session)
git clone https://github.com/OPTIMETA/PAIDEIA-Hermes && ./PAIDEIA-Hermes/install.sh
```

Nothing in `~/.hermes/config.yaml` needs to change — the plugin is discovered from `~/.hermes/plugins/paideia/`.

### Per-course bootstrap

Open hermes inside the folder you want to use for this course, then either run the wizard:

```
/paideia init
```

…or scaffold non-interactively in one line:

```
/paideia init name="Complex Analysis MATH 405" exam=2026-12-15 type=final lang=en ocr=claude weak="contour integration"
```

This checks deps, asks (or takes as args) interface language `en|ko`, `COURSE_NAME`, `EXAM_DATE`, `EXAM_TYPE`, `USER_WEAK_ZONES`, and the OCR engine, then creates the directory skeleton, writes `.course-meta` + a project `PAIDEIA.md`, and seeds `errors/log.md`. Override the OCR engine for a single grade with `/paideia grade --ocr=claude path/to/answer.pdf`.

---

## Course folder layout

After `/paideia init`, your course folder looks like this:

```
my-course/
├── .course-meta                     # course name, exam date, interface language (en|ko), OCR engine
├── PAIDEIA.md                       # per-course workflow context the agent reads
├── .gitignore                       # hides raw PDF scans + OCR scratch; the study graph itself stays committed
│
├── materials/                       # YOU DROP RAW FILES HERE (PDF or MD)
│   ├── lectures/  textbook/  homework/  solutions/
│
├── converted/                       # auto-generated markdown — do not edit (output of /paideia ingest)
│   ├── lectures/  textbook/  homework/  solutions/
│
├── course-index/                    # knowledge base — built by /paideia analyze
│   ├── summary.md                   # topic tree (§1, §1.1, §2, …)
│   ├── patterns.md                  # recurring solution patterns, labeled P1, P2, …
│   ├── coverage.md                  # HW ↔ § map with 🔥🔥 / 🔥 / 🟡 / ⚪ exam tiers
│   └── radar.md                     # lecture-emphasis signal — imported by /paideia alt
│
├── answers/                         # YOU DROP HAND-WRITTEN SCAN PDFs HERE
│   └── converted/                   # /paideia grade writes OCR'd markdown here
│
├── errors/log.md                    # append-only YAML error log (seed for /weakmap + /cheatsheet)
│
├── quizzes/                         # /paideia quiz — each problem has a hidden _answers.md sibling
├── mock/                            # /paideia mock — full mock exams (hidden _sol.md siblings)
├── twins/                           # /paideia twin — same pattern, new surface
├── chain/                           # /paideia chain — multi-pattern integration problems
├── derivations/                     # /paideia derive — clean reference derivations
├── cheatsheet/                      # /paideia cheatsheet — error-driven one-pager (+ optional PDF)
└── weakmap/                         # /paideia weakmap — timestamped, append-only history
```

**Only two directories are yours to edit by hand:** `materials/` (drop source PDFs/MDs) and `answers/` (drop hand-written scans). Everything else is produced by `/paideia` commands and is regenerable. `git log <dir>` to see your own progress over time, or point Obsidian at the whole folder as a vault.

The on-disk layout is **byte-compatible with upstream [PAIDEIA](https://github.com/OPTIMETA/PAIDEIA)** — a course folder moves between the Claude Code plugin and this hermes port unchanged.

---

## A reading tip: use Obsidian

Paideia writes everything as plain markdown with LaTeX math (`$...$`, `$$...$$`); you can read it in any editor, but **[Obsidian](https://obsidian.md)** is the natural choice:

- Renders `$...$` and `$$...$$` math via MathJax with zero configuration.
- Backlinks let you click from `quizzes/q_<ts>.md` straight into the cited `converted/lectures/chN.md §K`.
- The whole course folder is just a vault — point Obsidian at `~/courses/my-course`, and everything is a searchable graph. Offline, free, local — consistent with Paideia's philosophy.

The terminal is bad for math; don't fight that.

## And the lecture end: Alt

Obsidian is the companion at the reading end. **[Alt](https://www.altalt.io/ko/)** is the companion at the other end — where the lectures come in. Alt records and transcribes your lectures, and OPTIMETA's **Exam Radar** plugin runs inside it to rank topics by how strongly the professor emphasized them out loud. Send that into Paideia with `/paideia alt`, and the loop closes: **attend the lecture → capture it → extract the exam signal → study what matters.**

---

## Full workflow — an example

**Phase 0 — once per course (15 minutes).** Drop PDFs into `materials/{lectures,textbook,homework,solutions}/`, then in hermes:

```
/paideia ingest                     # every PDF → vision pipeline (subagent per PDF, LaTeX-faithful)
/paideia analyze <weak-zone hints>  # build patterns + coverage + summary
/paideia hwmap hot                  # surface 🔥🔥 exam-primary zones
```

**Phase 1 — diagnostic (40 minutes).**

```
/paideia quiz all 20                # broad diagnostic, 20 problems
# solve on paper, scan to answers/diagnostic.pdf
/paideia grade                      # OCR + strategy grade
```

**Phase 2 — targeted drilling (bulk of your prep time).**

```
/paideia weakmap                    # priority-ranked weakness report
/paideia blind hw3-p2               # strategy-only drill on a known problem
/paideia twin hw3-p2                # variant with same pattern, new surface
/paideia chain 3                    # multi-pattern integration problem
/paideia quiz weakmap 5             # 5 problems targeting the latest weakmap
```

**Phase 3 — integration (~90 minutes).**

```
/paideia mock 90                    # full mock weighted by HW density
# solve on paper, scan, upload to answers/mock_<ts>.pdf
/paideia grade
```

**Phase 4 — compression (night before).**

```
/paideia cheatsheet --pdf           # error-driven one-pager
/paideia weakmap                    # review weak zones one more time
```

**Phase 5 — cool-down (10 minutes before).** `/paideia weakmap` — top 3 only. Do not learn new things.

---

## Commands (16 total)

`/paideia <subcommand> [args]` — run `/paideia help` for the list inline.

| Command | Purpose |
|---------|---------|
| `/paideia init [name=… exam=… …]` | Bootstrap a fresh course folder (wizard, or one-line with args) |
| `/paideia doctor [--fix]` | Diagnose the install + workspace; `--fix` repairs permission-free issues |
| `/paideia status` | One-line `course · D-N · phase · top-miss pattern` |
| `/paideia ingest [--force]` | Every PDF in `materials/**` → markdown in `converted/**` (subagent per PDF, LaTeX-faithful) |
| `/paideia analyze [hints]` | Build `course-index/{summary,patterns,coverage}.md` |
| `/paideia hwmap hot\|<§>` | Surface 🔥🔥 Exam-primary sections ranked by HW density |
| `/paideia pattern <§\|Pk\|keyword>` | Show pattern cards from course-index |
| `/paideia derive <target>` | Clean reference derivation to `derivations/<slug>.md` |
| `/paideia quiz <topic\|§\|weakmap> [N]` | N practice problems, answers hidden in a sibling `_answers.md` |
| `/paideia blind <problem-id>` | Strategy-check drill on a known problem (describe approach, no re-solve) |
| `/paideia twin <problem-id>` | Variant of a known problem — same pattern, new surface |
| `/paideia chain <N>` | Multi-pattern integration problem combining N patterns |
| `/paideia mock <minutes>` | Full mock exam, HW-density weighted |
| `/paideia grade [--ocr=<engine>] [path]` | OCR an answer PDF, strategy-grade, append `errors/log.md` |
| `/paideia weakmap [concept]` | Priority-ranked weakness report → `weakmap/weakmap_<ts>.md` |
| `/paideia cheatsheet [--pdf]` | Error-driven one-pager |
| `/paideia alt [paste]` | Import an OPTIMETA Exam Radar (Alt) export → `radar.md` + a lecture-emphasis column on `coverage.md` |

---

## Slack & other messaging gateways

PAIDEIA-Hermes works through hermes' messaging gateway (Slack, Discord, Telegram, …), not just the CLI. Use your platform's typed-command prefix (Slack/Matrix use `!`, most others `/`):

- **Deterministic commands** — `!paideia status`, `!paideia doctor`, `!paideia init name="…" exam=…`, `!paideia help` — reply with text directly.
- **Agent-driven commands** — `!paideia ingest|analyze|quiz|grade|weakmap|mock|twin|…` — a `pre_gateway_dispatch` hook rewrites them into a normal agent turn (the CLI's in-session `inject_message` isn't available in the gateway). A bare phrase works too: `paideia quiz §1.2 3`.

The gateway runs in its configured working directory (`terminal.cwd`), so point that at your course folder; each command reads `INTERFACE_LANG` from `.course-meta` itself, so en/ko prose is preserved in Slack too.

---

## Under the hood

### Ingest pipeline: vision for every PDF

`/paideia ingest` routes every PDF in `materials/**` through one vision pipeline. `pdfplumber` proved unreliable even on prose pages the moment they mix equations, figures, or multi-column layouts, so everything goes through vision uniformly. `materials/**/*.md` are copied through with a provenance header.

Every page is rendered to PNG at `dpi=160` and resized to ≤1800 px on the long edge **before any agent reads it** (multimodal requests reject oversized images); then hermes **delegates one subagent per PDF**, each reading its pages *sequentially* (parallel batches trip the dimension limit) and transcribing to LaTeX markdown — `$$\hat H = -\frac{\hbar^2}{2m}\partial_x^2 + V(x)$$` instead of `ℏ ∂ p2 …`. Details in `skills/paideia-pdf/VISION.md`.

### Hand-writing OCR: three engines, you pick

You don't type math into chat — you solve on paper, scan to PDF, drop it in `answers/`, and run `/paideia grade`. The engine is chosen per course (`OCR_ENGINE` in `.course-meta`) and overridable per call (`--ocr=`):

| Engine | Default? | How it runs | When to pick it |
|---|---|---|---|
| `claude` | **Yes** | `pdftoppm` renders each page → the agent reads each PNG with its own native vision → synthesizes markdown. No extra model, nothing to install. | The out-of-the-box path. |
| `ollama` | opt-in | `pd_vision_ocr.py --engine=ollama` → local Qwen3-VL 8B with automatic tesseract fallback. | Page images must never leave the machine. |
| `tesseract` | opt-in | `pd_vision_ocr.py --engine=tesseract` → pytesseract (`eng`/`eng+kor`). | Lightest; acceptable for typed scans. |

> The default engine is named `claude` for on-disk compatibility with upstream PAIDEIA; on hermes it means **"the agent's own native vision"** — whichever multimodal model your provider exposes (e.g. gpt-5.5 via `openai-codex`). It is not tied to Anthropic.

### Strategy-based grading, not line-by-line

OCR noise makes strict algebraic grading useless, and **pattern recognition is the actual exam bottleneck** anyway. The grader checks three things per problem: (1) **Pattern** — did you pick the right `Pk`? (2) **Variables** — the right substitution/basis/contour? (3) **End-form** — the right final shape? Errors are logged to `errors/log.md` as YAML with a typed classification (`pattern-missed | wrong-variable | wrong-end-form | algebraic | sign | definition`). This log is the seed for `/paideia weakmap` and the only input to `/paideia cheatsheet`.

### Patterns extracted from *your* solutions

`/paideia analyze` reads your course's actual solution manual and labels recurring moves P1, P2, … with instances that cite your own `converted/solutions/` files. For complex analysis, P3 might be "closed contour + Jordan's lemma + residue"; for linear systems, "partial fractions + inverse Laplace with complex poles." Only the course reveals its own idioms.

### Status & the session banner

hermes has no per-prompt plugin statusline slot, so Paideia surfaces the same signal two ways:

- **`/paideia status`** prints `paideia · <COURSE> · D-N · <phase> · P<top-miss> ↑` on demand.
- An **`on_session_start` hook** prints a matching banner when you open a session inside a course folder.

`<phase>` is derived from **activity on disk**, so it advances when you actually use an artifact: `setup` (no `patterns.md` yet) → `diag` (patterns exist, nothing graded) → `drill` (quiz problems exist AND a graded `errors/log.md` entry) → `mock` (a mock-sourced entry appeared) → `cram` (`cheatsheet/final.*` exists) → `cool` (`D-0`). `<top-miss>` is the most frequent `pattern:` tag from the latest weakmap (falls back to `errors/log.md`). Both surfaces stay silent outside a course folder.

---

## What ships

```
PAIDEIA-Hermes/                     # == ~/.hermes/plugins/paideia/
├── plugin.yaml                     # manifest (name, version, hooks)
├── __init__.py                     # register(ctx): /paideia command + on_session_start + pre_gateway_dispatch
├── pd_meta.py  pd_workspace.py  pd_errlog.py  pd_weakmap.py    # deterministic engine
├── pd_status.py  pd_banner.py  pd_doctor.py                    # status / banner / diagnostics
├── pd_render.py  pd_vision_ocr.py                              # PDF→PNG + offline OCR tiers (run standalone)
├── pd_prompts.py  pd_commands.py                               # inject-prompt builder + /paideia dispatcher
├── commands/                       # 15 agent-facing command specs (.md)
├── skills/
│   ├── paideia-pdf/{SKILL.md,VISION.md}        # vision ingest pipeline
│   ├── paideia-vision-ocr/SKILL.md             # the agent's vision + Ollama + tesseract
│   ├── paideia-course-builder/SKILL.md         # ingest + analyze
│   ├── paideia-exam-drill/{SKILL.md,twin-recipe.md}
│   ├── paideia-answer-processing/SKILL.md      # strategy-grade OCR output
│   └── paideia-alt-import/SKILL.md
├── install.sh  LICENSE  README.md  README.ko.md
```

How it maps to hermes' extension surfaces:

| PAIDEIA (Claude Code) | PAIDEIA-Hermes (hermes-agent) |
|---|---|
| `/paideia:*` namespaced (16) | one `/paideia` slash command + subcommand dispatch (`ctx.register_command`) |
| auto-loaded skills | `skills/paideia-*/SKILL.md`, read by absolute path from the inject prompt |
| in-session command runs the `.md` directly | handler `inject_message()`s a turn (CLI) / `pre_gateway_dispatch` rewrite (Slack/Discord) |
| `SessionStart` hook banner | `on_session_start` hook |
| `statusLine` hook | `/paideia status` + the session banner |
| parallel ingest agents | hermes subagent delegation (one per PDF) |
| `CLAUDE.md` per course | `PAIDEIA.md` per course |

---

## Design convictions

1. **The terminal is bad for math.** The agent produces markdown files; you read them (ideally in Obsidian).
2. **Typing solutions is slow and error-prone.** You solve on paper, scan, and the plugin OCRs locally.
3. **OCR noise is inevitable**, so grading is strategy-based (pattern / variables / end-form), which is what the real grader evaluates anyway.
4. **Patterns must be extracted from *your* course's solutions** — not a generic list.
5. **Your errors are the most valuable study signal.** The cheatsheet is generated from `errors/log.md`, not the syllabus.
6. **HW density tells you the exam.** Spend finite time where the points are.
7. **Everything is yours to edit** — plain markdown/YAML in your own git history. The plugin is a scaffold; the study graph is yours.
8. **Model-agnostic by construction.** The same plugin runs on Codex, Nous, Anthropic, OpenRouter, or a local model — your study graph never depends on one vendor.

---

## FAQ

**Does this work for non-math courses?** It's built around problem-pattern extraction, so it shines in quantitative disciplines (math, physics, EE, CS-theory, statistics). History/literature would ingest and summarize, but the drill commands assume problems have solution patterns.

**Korean and English mixed materials?** Yes. OCR is configured for `eng+kor`; prose stays in its source language and `INTERFACE_LANG` controls the plugin's own narrative (`en|ko`).

**Which model runs it — and do I need Codex specifically?** Whatever your hermes provider is. If `~/.hermes/config.yaml` says `provider: openai-codex` you're on Codex (gpt-5.5); switch with `/model` and nothing about Paideia changes. The default OCR engine (`claude`) means "the agent's own vision," not Anthropic specifically.

**Does it work in Slack?** Yes — see [Slack & other messaging gateways](#slack--other-messaging-gateways). Deterministic commands reply with text; agent-driven ones are rewritten into a turn by a `pre_gateway_dispatch` hook.

**Do I need Ollama / Qwen3-VL?** No. The default OCR is the agent's native vision. Ollama (`qwen3-vl:8b`) is opt-in for keeping page images fully on-machine; `tesseract` is a minimal-install floor.

**Can I edit the patterns / cheatsheet / weakmap if I disagree?** Yes — that's the point of plain markdown. Rewrite `P3` in `course-index/patterns.md` and the next drill uses your edit.

**Can I reuse the plugin across courses?** Yes — each course is its own folder with its own `.course-meta`, `course-index/`, `errors/log.md`, `weakmap/`. Nothing is shared. Open hermes inside whichever course folder you're working on.

**Is my data private?** Your PDFs, markdown, errors, and weakmaps live in your local course folder. Network traffic depends on the OCR engine: `claude` routes page images through your normal hermes provider; `ollama`/`tesseract` keep everything on the machine.

---

## Connect

<p align="center">
  <a href="https://github.com/TaewoooPark"><img src="https://img.shields.io/badge/-GitHub-181717?style=for-the-badge&logo=github&logoColor=white" alt="GitHub"></a>
  <a href="https://x.com/theoverstrcture"><img src="https://img.shields.io/badge/-X-000000?style=for-the-badge&logo=x&logoColor=white" alt="X (Twitter)"></a>
  <a href="https://www.linkedin.com/in/taewoo-park-427a05352"><img src="https://img.shields.io/badge/-LinkedIn-0A66C2?style=for-the-badge&logo=linkedin&logoColor=white" alt="LinkedIn"></a>
  <a href="https://taewoopark.com"><img src="https://img.shields.io/badge/-taewoopark.com-000000?style=for-the-badge&logo=safari&logoColor=white" alt="Personal site"></a>
  <a href="mailto:ptw151125@kaist.ac.kr"><img src="https://img.shields.io/badge/-Email-D14836?style=for-the-badge&logo=gmail&logoColor=white" alt="Email"></a>
</p>

---

## License

**MIT.** PAIDEIA-Hermes is a hermes-agent port of [OPTIMETA/PAIDEIA](https://github.com/OPTIMETA/PAIDEIA) and carries the same license and copyright (© 2026 Taewoo Park); see [`LICENSE`](./LICENSE). Use freely — fork and modify for your own courses. The point of the plugin is that the study graph it builds is yours to shape, not a fixed product you have to live with.

Credits: the original [PAIDEIA](https://github.com/OPTIMETA/PAIDEIA) (Claude Code) and the host platform [NousResearch/hermes-agent](https://github.com/NousResearch/hermes-agent) (MIT).

---

<p align="center">
  <em>Generic curricula teach the average student. Παιδεία — formation, one student at a time.</em>
</p>
