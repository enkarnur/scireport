#!/usr/bin/env bash
set -euo pipefail

if [ "$#" -lt 2 ]; then
  echo "usage: $0 <output-binary> <package-or-file>" >&2
  exit 1
fi

OUT="$1"
TARGET="$2"
ROOT_DIR="$(cd "$(dirname "$0")/.." && pwd)"
BIN_DIR="$(dirname "$OUT")"
mkdir -p "$BIN_DIR"

needs_build=false
if [ ! -x "$OUT" ]; then
  needs_build=true
elif [ "$ROOT_DIR/go.mod" -nt "$OUT" ]; then
  needs_build=true
elif [ -d "$ROOT_DIR/internal" ] && [ -n "$(find "$ROOT_DIR/internal" -type f -newer "$OUT" 2>/dev/null | head -1)" ]; then
  needs_build=true
elif [ -e "$ROOT_DIR/$TARGET" ] && [ "$ROOT_DIR/$TARGET" -nt "$OUT" ]; then
  needs_build=true
fi

if [ "$needs_build" = true ]; then
  cd "$ROOT_DIR"
  export GOWORK=off
  go build -o "$OUT" "$TARGET"
fi

exec "$OUT" "${@:3}"
