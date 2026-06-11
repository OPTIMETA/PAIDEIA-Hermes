"""Build the message injected into the conversation for LLM-driven subcommands.

Upstream PAIDEIA executed each command's markdown spec directly (Claude Code
runs the slash-command file as a prompt). hermes plugin slash-commands return a
string and cannot run an LLM turn synchronously, so instead we ``inject_message``
a turn that (a) names the skill to load, (b) pins the working directory +
language, (c) passes the user's args, and (d) inlines the command spec.
"""
from __future__ import annotations

from pathlib import Path

PLUGIN_ROOT = Path(__file__).resolve().parent
COMMANDS_DIR = PLUGIN_ROOT / "commands"

# Which bundled skill dir(s) the agent should read+follow for each subcommand.
# The agent reads these SKILL.md files by absolute path (so they work whether or
# not they're registered in hermes' skill system). Orchestration skills
# (course-builder, exam-drill, answer-processing) reference the infra skills
# (pdf, vision-ocr) themselves.
SKILL_FOR = {
    "ingest": ["paideia-course-builder", "paideia-pdf"],
    "analyze": ["paideia-course-builder"],
    "hwmap": ["paideia-exam-drill"],
    "pattern": ["paideia-exam-drill"],
    "derive": ["paideia-exam-drill"],
    "blind": ["paideia-exam-drill"],
    "twin": ["paideia-exam-drill"],
    "quiz": ["paideia-exam-drill"],
    "chain": ["paideia-exam-drill"],
    "mock": ["paideia-exam-drill"],
    "weakmap": ["paideia-exam-drill"],
    "cheatsheet": ["paideia-exam-drill"],
    "grade": ["paideia-answer-processing", "paideia-vision-ocr"],
    "alt": ["paideia-alt-import"],
}


def load_spec(sub: str) -> str | None:
    p = COMMANDS_DIR / f"{sub}.md"
    if p.exists():
        try:
            return p.read_text(encoding="utf-8", errors="replace")
        except OSError:
            return None
    return None


def build_inject(sub: str, args: str, cwd: Path, lang: str) -> str:
    spec = load_spec(sub) or f"(no command spec file found for '{sub}.md')"
    # Specs reference ${PAIDEIA_PLUGIN_ROOT} for bundled scripts — resolve it now.
    spec = spec.replace("${PAIDEIA_PLUGIN_ROOT}", str(PLUGIN_ROOT))

    skill_dirs = SKILL_FOR.get(sub, [])
    skill_paths = [PLUGIN_ROOT / "skills" / d / "SKILL.md" for d in skill_dirs]
    skill_block = ""
    if skill_paths:
        bullets = "\n".join(f"  - {p}" for p in skill_paths)
        skill_block = (
            "First read the skill file(s) below and follow them as the method "
            "(they reference further files relative to their own directory), "
            "then execute the command spec:\n" + bullets + "\n\n"
        )
    return (
        f"[PAIDEIA · /paideia {sub}]\n"
        f"Working directory (course root): {cwd}\n"
        f"Plugin root (bundled scripts/skills): {PLUGIN_ROOT}\n"
        f"Interface language: {lang} — write all prose to the user in this language; "
        f"keep file paths, slash-command names, pattern IDs (P1, P2…), YAML keys, "
        f"LaTeX, and tier markers (🔥🔥/🔥/🟡/⚪) verbatim in any language.\n"
        f"Arguments: {args.strip() or '(none)'}\n\n"
        f"{skill_block}"
        f"Execute the command spec below against the course workspace in the "
        f"working directory. Use the read_file / write_file / terminal tools; for "
        f"per-file parallel work (e.g. ingest), delegate one subagent per file.\n"
        f"IMPORTANT — materialize every artifact: whenever the spec says to save / "
        f"write a file to a path, you MUST create it on disk with write_file before "
        f"the turn ends. Printing content to chat is NOT a substitute for writing the "
        f"file. For any `<ts>` timestamp in a filename, get it once via the terminal "
        f"tool (`date +%Y-%m-%d_%H%M`) and reuse it. The command is not done until "
        f"the files the spec names actually exist.\n\n"
        f"--- COMMAND SPEC: {sub} ---\n{spec}\n"
    )
