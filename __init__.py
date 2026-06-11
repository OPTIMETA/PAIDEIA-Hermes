"""PAIDEIA-Hermes plugin entry point.

Registers the ``/paideia`` slash command and an ``on_session_start`` banner.
Loaded by hermes-agent's PluginManager from ``~/.hermes/plugins/paideia/`` as
the package ``hermes_plugins.paideia`` (so the ``from . import …`` relative
imports below resolve correctly).
"""
from __future__ import annotations

import logging
import re
import sys
from pathlib import Path

logger = logging.getLogger(__name__)

# Matches `paideia <sub> [args]` with an optional typed-command prefix
# (CLI/Discord use "/", Slack/Matrix use "!"). Used by the gateway hook.
_GATEWAY_CMD_RX = re.compile(r"^\s*[!/]?\s*paideia\s+(\S+)\s*(.*)$", re.S | re.I)

_ARGS_HINT = "<init|ingest|analyze|quiz|grade|weakmap|cheatsheet|doctor|status|…> [args]"


def register(ctx) -> None:
    from . import pd_banner, pd_commands, pd_prompts

    ctx.register_command(
        "paideia",
        handler=lambda raw_args: pd_commands.dispatch(raw_args, ctx),
        description="PAIDEIA exam-prep: ingest course PDFs, HW-density drills, grade scans.",
        args_hint=_ARGS_HINT,
    )

    def _on_session_start(**kwargs) -> None:
        """Print the D-N/phase/top-miss banner when opening a course folder."""
        try:
            text = pd_banner.render_banner(Path.cwd())
            if text:
                sys.stderr.write(text + "\n")
                sys.stderr.flush()
        except Exception as exc:  # never break session start
            logger.debug("paideia banner failed: %s", exc)

    ctx.register_hook("on_session_start", _on_session_start)

    def _on_pre_gateway_dispatch(event=None, **kwargs):
        """Make `/paideia <llm-sub>` work in gateway sessions (Slack, Discord, …).

        inject_message() is CLI-only (no _cli_ref in gateway), so the LLM-driven
        subcommands can't hand work to the agent the way they do in the CLI.
        Here we intercept the incoming message and rewrite it into the same
        agent-turn prompt; the gateway then dispatches it as a normal turn.
        Deterministic subs (status/doctor/help/init) return None and fall through
        to the plugin slash-command handler, which replies with text directly.
        """
        try:
            text = getattr(event, "text", "") or ""
            m = _GATEWAY_CMD_RX.match(text)
            if not m:
                return None
            sub = m.group(1).lower()
            args = (m.group(2) or "").strip()
            if sub not in pd_commands.LLM_SUBS:
                return None
            return {"action": "rewrite", "text": pd_prompts.build_inject(sub, args, None, None)}
        except Exception as exc:  # never break gateway dispatch
            logger.debug("paideia pre_gateway_dispatch failed: %s", exc)
            return None

    ctx.register_hook("pre_gateway_dispatch", _on_pre_gateway_dispatch)
    logger.debug("paideia plugin registered (/paideia + on_session_start + pre_gateway_dispatch)")
