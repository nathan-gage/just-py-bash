#!/usr/bin/env bash
set -euo pipefail

ROOT=$(cd "$(dirname "$0")/.." && pwd)
VENDOR_DIR="$ROOT/vendor/just-bash"
OUT_DIR="$ROOT/src/just_py_bash/_vendor/just-bash"
TMP_DIR=$(mktemp -d)
trap 'rm -rf "$TMP_DIR"' EXIT

if [[ ! -d "$VENDOR_DIR" ]]; then
  echo "Missing vendor/just-bash checkout" >&2
  exit 1
fi

if [[ ! -f "$VENDOR_DIR/dist/index.js" ]]; then
  echo "Missing built vendor/just-bash dist/index.js" >&2
  echo "Run: (cd vendor/just-bash && pnpm install && pnpm build)" >&2
  exit 1
fi

(
  cd "$VENDOR_DIR"
  npx esbuild dist/index.js \
    --bundle \
    --splitting \
    --platform=node \
    --format=esm \
    --define:__BROWSER__=false \
    --outdir="$TMP_DIR/dist" \
    --chunk-names=chunks/[name]-[hash] \
    --external:@mongodb-js/zstd \
    --external:node-liblzma
)

rm -rf "$OUT_DIR"
mkdir -p "$OUT_DIR"
cp "$VENDOR_DIR/package.json" "$OUT_DIR/package.json"
cp -R "$TMP_DIR/dist" "$OUT_DIR/dist"
