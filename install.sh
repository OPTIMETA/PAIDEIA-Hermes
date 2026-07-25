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
  mkdir -p "$DEST"
  # tar, not `cp -R`: the checkout carries .git (tens of MB of history the plugin
  # never reads) and __pycache__ (.pyc compiled against whichever interpreter ran
  # last, which is not necessarily the one hermes will use).
  ( cd "$SRC" && tar --exclude='./.git' --exclude='./tests' \
      --exclude='__pycache__' --exclude='.DS_Store' -cf - . ) \
    | ( cd "$DEST" && tar -xf - )
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
