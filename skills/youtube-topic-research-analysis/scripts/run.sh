#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
CACHE_ROOT="${YTTOPIC_CACHE_DIR:-${XDG_CACHE_HOME:-$HOME/.cache}/youtube-transcripts-to-obsidian}"
PYTHON_ENV="$CACHE_ROOT/python"
NODE_PREFIX="$CACHE_ROOT/node"
DEFUDDLE_PATH="$NODE_PREFIX/node_modules/.bin/defuddle"

if [[ ! -x "$PYTHON_ENV/bin/python" ]] || ! "$PYTHON_ENV/bin/python" -c 'import yt_dlp' >/dev/null 2>&1 || [[ ! -x "$DEFUDDLE_PATH" ]]; then
  if [[ "${YTTOPIC_ALLOW_INSTALL:-0}" != "1" ]]; then
    echo "Cached yt-dlp/Defuddle tools are unavailable. No installation was attempted." >&2
    echo "Set YTTOPIC_ALLOW_INSTALL=1 only after the user explicitly authorises installation." >&2
    exit 1
  fi
  if ! command -v python3 >/dev/null 2>&1; then
    echo "python3 is required." >&2
    exit 1
  fi
  if ! command -v npm >/dev/null 2>&1; then
    echo "npm is required to install and run Defuddle." >&2
    exit 1
  fi
  if [[ ! -x "$PYTHON_ENV/bin/python" ]]; then
    echo "Preparing the private Python runtime..." >&2
    python3 -m venv "$PYTHON_ENV"
  fi
  echo "Installing/updating yt-dlp in the private runtime..." >&2
  "$PYTHON_ENV/bin/python" -m pip install --disable-pip-version-check --quiet --upgrade yt-dlp
  echo "Installing/updating Defuddle in the private runtime..." >&2
  npm install --prefix "$NODE_PREFIX" --no-save --package-lock=false --no-audit --no-fund --silent defuddle@latest
fi

export DEFUDDLE_BIN="$DEFUDDLE_PATH"
exec "$PYTHON_ENV/bin/python" "$SCRIPT_DIR/search_fetch.py" "$@"
