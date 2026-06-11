"""PAIDEIA-Hermes plugin entry point.

Registers the ``/paideia`` slash command and an ``on_session_start`` banner.
Loaded by hermes-agent's PluginManager from ``~/.hermes/plugins/paideia/`` as
the package ``hermes_plugins.paideia`` (so the ``from . import …`` relative
imports below resolve correctly).
"""
from __future__ import annotations

import logging
import sys
from pathlib import Path

logger = logging.getLogger(__name__)

_ARGS_HINT = "<init|ingest|analyze|quiz|grade|weakmap|cheatsheet|doctor|status|…> [args]"


def register(ctx) -> None:
    from . import pd_banner, pd_commands

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
    logger.debug("paideia plugin registered (/paideia + on_session_start)")
