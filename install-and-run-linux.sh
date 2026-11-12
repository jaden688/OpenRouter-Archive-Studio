#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$(realpath "$0")")"

echo
echo 'OPENROUTER ARCHIVE STUDIO - INSTALLER'
echo 'Dependencies will be installed into a private .venv in this folder.'
echo 'Your system Python installation will not be modified.'
echo

PYTHON=""
for candidate in python3.14 python3.13 python3.12 python3.11 python3.10 python3; do
  if command -v "$candidate" >/dev/null 2>&1 && "$candidate" -c 'import sys; raise SystemExit(0 if sys.version_info >= (3,10) else 1)' >/dev/null 2>&1; then
    PYTHON="$candidate"
    break
  fi
done
if [[ -z "$PYTHON" ]]; then
  echo 'Python 3.10 or newer is required. Install Python 3 and its venv support using your distribution package manager.'
  exit 1
fi

if [[ ! -x .venv/bin/python ]]; then
  "$PYTHON" -m venv .venv
fi
.venv/bin/python -m pip install --upgrade pip
.venv/bin/python -m pip install -r requirements.txt
exec .venv/bin/python OpenRouter_Translate_Viewer.py
