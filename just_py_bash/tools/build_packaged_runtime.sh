#!/usr/bin/env bash
set -euo pipefail

PACKAGE_DIR=$(cd "$(dirname "$0")/.." && pwd)
ROOT=$(cd "$PACKAGE_DIR/.." && pwd)
VENDOR_DIR="$ROOT/vendor/just-bash"
OUT_DIR="${JUST_BASH_PACKAGED_RUNTIME_OUT_DIR:-$PACKAGE_DIR/src/just_bash/_vendor/just-bash}"
OUT_PARENT=$(dirname "$OUT_DIR")
STAGING_DIR=$(mktemp -d "$OUT_PARENT/.just-bash-staging.XXXXXX")
TMP_DIR=$(mktemp -d)
trap 'rm -rf "$TMP_DIR" "$STAGING_DIR"' EXIT

if [[ ! -d "$VENDOR_DIR" ]]; then
  echo "Missing vendor/just-bash checkout" >&2
  exit 1
fi

if [[ ! -f "$VENDOR_DIR/dist/index.js" ]]; then
  echo "Missing built vendor/just-bash dist/index.js" >&2
  echo "Run: (cd vendor/just-bash && pnpm install && pnpm build)" >&2
  exit 1
fi

if [[ ! -f "$VENDOR_DIR/src/commands/python3/worker.js" ]]; then
  echo "Missing built vendor/just-bash python worker" >&2
  echo "Run: (cd vendor/just-bash && pnpm install && pnpm build)" >&2
  exit 1
fi

PACKAGE_VERSION=$(python - <<PY
import json
from pathlib import Path
print(json.loads(Path(r"$VENDOR_DIR/package.json").read_text())["version"])
PY
)

resolve_cpython_assets() {
  local source_dir="$VENDOR_DIR/vendor/cpython-emscripten"
  local wasm_file="$source_dir/python.wasm"

  if [[ -f "$wasm_file" ]] && file "$wasm_file" | grep -q 'WebAssembly'; then
    cp -R "$source_dir" "$TMP_DIR/cpython-emscripten"
    return
  fi

  echo "Fetching packaged CPython assets for just-bash@$PACKAGE_VERSION" >&2
  mkdir -p "$TMP_DIR/npm"
  (
    cd "$TMP_DIR/npm"
    npm pack "just-bash@$PACKAGE_VERSION" >/dev/null
    tar -xzf "just-bash-$PACKAGE_VERSION.tgz"
  )
  cp -R "$TMP_DIR/npm/package/vendor/cpython-emscripten" "$TMP_DIR/cpython-emscripten"
}

resolve_quickjs_wasm() {
  local wasm_path
  wasm_path=$(find "$VENDOR_DIR/node_modules" -path '*@jitl+quickjs-wasmfile-release-sync*' -path '*/dist/emscripten-module.wasm' | head -n 1)
  if [[ -z "$wasm_path" ]]; then
    echo "Could not find quickjs emscripten-module.wasm in vendor/just-bash/node_modules" >&2
    echo "Run: (cd vendor/just-bash && pnpm install)" >&2
    exit 1
  fi
  printf '%s' "$wasm_path"
}

mkdir -p "$TMP_DIR/runtime/dist/bundle/chunks"

(
  cd "$VENDOR_DIR"
  npx esbuild dist/index.js \
    --bundle \
    --splitting \
    --platform=node \
    --format=esm \
    --define:__BROWSER__=false \
    --outdir="$TMP_DIR/runtime/dist/bundle" \
    --chunk-names=chunks/[name]-[hash] \
    --external:@mongodb-js/zstd \
    --external:node-liblzma
)

python - <<PY
from pathlib import Path

chunks_dir = Path(r"$TMP_DIR/runtime/dist/bundle/chunks")
for path in chunks_dir.glob("js-exec-*.js"):
    text = path.read_text()
    updated = text.replace(
        'new URL("./worker.js", import.meta.url)',
        'new URL("./js-exec-worker.js", import.meta.url)',
    ).replace(
        "new URL('./worker.js', import.meta.url)",
        "new URL('./js-exec-worker.js', import.meta.url)",
    )
    path.write_text(updated)
PY

cp "$VENDOR_DIR/src/commands/python3/worker.js" "$TMP_DIR/runtime/dist/bundle/chunks/worker.js"
(
  cd "$VENDOR_DIR"
  npx esbuild src/commands/js-exec/worker.ts \
    --bundle \
    --platform=node \
    --format=esm \
    --outfile="$TMP_DIR/runtime/dist/bundle/chunks/js-exec-worker.js"
)
cp "$(resolve_quickjs_wasm)" "$TMP_DIR/runtime/dist/bundle/chunks/emscripten-module.wasm"

resolve_cpython_assets
mkdir -p "$TMP_DIR/runtime/vendor"
cp -R "$TMP_DIR/cpython-emscripten" "$TMP_DIR/runtime/vendor/cpython-emscripten"

rm -rf "$STAGING_DIR"
mkdir -p "$STAGING_DIR"
cp "$VENDOR_DIR/package.json" "$STAGING_DIR/package.json"
cp -R "$TMP_DIR/runtime/dist" "$STAGING_DIR/dist"
cp -R "$TMP_DIR/runtime/vendor" "$STAGING_DIR/vendor"
rm -rf "$OUT_DIR"
mv "$STAGING_DIR" "$OUT_DIR"
