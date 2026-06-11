#!/usr/bin/env bash
# PAIDEIA-Hermes installer — symlink (dev) or copy this checkout into the hermes
# user-plugins dir and enable it.
#
#   ./install.sh            # symlink ~/.hermes/plugins/paideia -> this dir (live edits)
#   ./install.sh --copy     # copy instead of symlink
set -euo pipefail

HERMES_HOME="${HERMES_HOME:-$HOME/.hermes}"
SRC="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
DEST="$HERMES_HOME/plugins/paideia"

mkdir -p "$HERMES_HOME/plugins"

if [ "${1:-}" = "--copy" ]; then
  rm -rf "$DEST"
  cp -R "$SRC" "$DEST"
  echo "Copied $SRC -> $DEST"
else
  ln -sfn "$SRC" "$DEST"
  echo "Symlinked $DEST -> $SRC"
fi

if command -v hermes >/dev/null 2>&1; then
  hermes plugins enable paideia || true
  echo "Enabled. Restart hermes, then run '/paideia init' in a course folder."
else
  echo "hermes CLI not found on PATH. Enable manually: hermes plugins enable paideia"
fi
