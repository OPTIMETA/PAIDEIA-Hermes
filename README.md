# PAIDEIA-Hermes

**Exam-prep from your own course materials — as a native [hermes-agent](https://github.com/NousResearch/hermes-agent) plugin.**

> Your course. Your patterns. Your errors. Your cheatsheet.

PAIDEIA-Hermes is a port of the [OPTIMETA/PAIDEIA](https://github.com/OPTIMETA/PAIDEIA)
Claude Code plugin to hermes-agent. It turns a folder of your lectures, textbook,
homework and solutions into a persistent, editable study graph and drills you on
it — weighted by **homework density** (what actually shows up on the exam), not a
generic syllabus.

It is **model-agnostic**: it runs on whatever provider hermes is pointed at. If
your `~/.hermes/config.yaml` uses `provider: openai-codex`, PAIDEIA-Hermes is
driven by Codex; switch with `/model` and nothing about PAIDEIA changes.

> **Status (v0.2.0):** validated end-to-end driving real Codex (gpt-5.5) through
> hermes across the full lifecycle — `init → ingest → analyze → hwmap → quiz →
> grade → weakmap → mock → cheatsheet --pdf → twin → derive → chain` — with the
> phase machine (setup→diag→drill→cram), the `errors/log.md` schema contract,
> and en/ko i18n all confirmed. Bugs found in live use were patched (see commit log).

---

## Install (existing hermes users — one line)

```bash
hermes plugins install TaewoooPark/PAIDEIA-Hermes   # private repo: uses your GitHub auth
hermes plugins enable paideia
# restart hermes, then in any course folder:
/paideia init
```

Alternatives:

```bash
# B) git clone straight into the user-plugins dir
git clone https://github.com/TaewoooPark/PAIDEIA-Hermes ~/.hermes/plugins/paideia
hermes plugins enable paideia

# C) dev / local checkout (symlink — edits are live on next session)
git clone https://github.com/TaewoooPark/PAIDEIA-Hermes
ln -s "$PWD/PAIDEIA-Hermes" ~/.hermes/plugins/paideia
hermes plugins enable paideia

# …or just run the bundled installer
./install.sh
```

Nothing in `~/.hermes/config.yaml` needs to change. The plugin discovers itself
from `~/.hermes/plugins/paideia/` (see hermes' PluginManager).

## Requirements

- hermes-agent (any provider)
- `poppler` (`pdftoppm`) — required by every OCR tier · `brew install poppler`
- Python libs (lazy, only for ingest/grade/cheatsheet): `pypdf pdfplumber pdf2image pillow reportlab pytesseract`
- Optional offline OCR: `tesseract` (+ `tesseract-lang` for Korean), or `ollama` + `qwen3-vl:8b`

Run `/paideia doctor` any time to check all of the above (and `--fix` to repair
the safe ones).

---

## Commands

`/paideia <subcommand> [args]` (run `/paideia help` for the full list).

| Subcommand | What it does |
|---|---|
| `init` | bootstrap a course folder (args or interactive) |
| `doctor [--fix]` | diagnose install + workspace |
| `status` | one-line `course · D-N · phase · top-miss` |
| `ingest` | transcribe `materials/*.pdf` → `converted/*.md` (LaTeX-faithful) |
| `analyze` | build `course-index/` (summary, patterns, coverage) |
| `hwmap [hot\|§N\|all]` | exam-hot sections ranked by HW density |
| `pattern [§/Pk/kw]` | show solution-pattern cards |
| `quiz <topic\|weakmap> [N]` | N practice problems (weakmap → target weaknesses) |
| `blind <id>` | strategy-only blind drill (you don't type math) |
| `twin <id>` | same-technique variant problem |
| `chain` | multi-pattern integration problem |
| `mock` | full HW-weighted mock exam |
| `derive <topic>` | save a clean reference derivation |
| `grade [--ocr=…] [path]` | OCR a scanned answer PDF + strategy-grade it |
| `weakmap [concept]` | priority-ranked weakness report |
| `cheatsheet [--pdf]` | one-page error-driven cheatsheet |
| `alt [path]` | import Exam Radar (Alt) lecture-emphasis signal |

The drill loop: PAIDEIA generates problems → you solve **on paper** → scan to
`answers/` → `/paideia grade` OCRs + grades by *strategy* (pattern recognition,
variable choice, end-form), logging misses to `errors/log.md`. `/paideia weakmap`
ranks them; `/paideia quiz weakmap` drills exactly those.

---

## How it maps PAIDEIA → hermes-agent

PAIDEIA was a Claude Code plugin (namespaced `/paideia:*` slash commands +
auto-loaded skills + a statusline/SessionStart hook). The hermes port preserves
every capability on hermes' own extension surfaces:

| PAIDEIA (Claude Code) | PAIDEIA-Hermes (hermes-agent) |
|---|---|
| `/paideia:ingest` … (16 namespaced commands) | one `/paideia` slash command + subcommand dispatch (`ctx.register_command`) |
| 6 auto-loaded skills | `skills/paideia-*/SKILL.md`, read by absolute path from the inject prompt |
| deterministic scripts (statusline, doctor, OCR) | flat `pd_*.py` modules; the two run-standalone scripts stay import-self-contained |
| LLM commands run the command `.md` directly | handler `inject_message()`s a turn that loads the skill + spec |
| `SessionStart` hook banner | `on_session_start` hook → stderr banner |
| `statusLine` hook | `/paideia status` + the session banner (hermes has no plugin statusline slot) |
| parallel ingest agents | hermes subagent delegation (one per PDF) |
| `CLAUDE.md` per course | `PAIDEIA.md` per course |

The on-disk data model (`.course-meta`, `course-index/`, `errors/log.md` YAML
schema, `weakmap/`, tier markers 🔥🔥/🔥/🟡/⚪) is **byte-compatible** with
upstream PAIDEIA, so artifacts move between the two.

## Credits

- [OPTIMETA/PAIDEIA](https://github.com/OPTIMETA/PAIDEIA) by TaewoooPark — the original.
- [NousResearch/hermes-agent](https://github.com/NousResearch/hermes-agent) — the host platform.

MIT licensed.
