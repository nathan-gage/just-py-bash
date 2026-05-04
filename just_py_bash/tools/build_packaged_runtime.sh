#!/usr/bin/env bash
set -euo pipefail

PACKAGE_DIR=$(cd "$(dirname "$0")/.." && pwd)
ROOT=$(cd "$PACKAGE_DIR/.." && pwd)
VENDOR_DIR="$ROOT/vendor/just-bash"
VENDOR_PACKAGE_DIR="$VENDOR_DIR"
if [[ -f "$VENDOR_DIR/packages/just-bash/package.json" ]]; then
  VENDOR_PACKAGE_DIR="$VENDOR_DIR/packages/just-bash"
fi
OUT_DIR="${JUST_BASH_PACKAGED_RUNTIME_OUT_DIR:-$PACKAGE_DIR/src/just_bash/_vendor/just-bash}"
OUT_PARENT=$(dirname "$OUT_DIR")
mkdir -p "$OUT_PARENT"
TMP_DIR=$(mktemp -d)
STAGING_DIR=$(mktemp -d "$TMP_DIR/.just-bash-staging.XXXXXX")
trap 'rm -rf "$TMP_DIR" "$STAGING_DIR"' EXIT

if [[ ! -d "$VENDOR_DIR" ]]; then
  echo "Missing vendor/just-bash checkout" >&2
  exit 1
fi

if [[ ! -f "$VENDOR_PACKAGE_DIR/dist/index.js" ]]; then
  echo "Missing built just-bash package dist/index.js at $VENDOR_PACKAGE_DIR" >&2
  echo "Run: (cd vendor/just-bash && pnpm install && pnpm build)" >&2
  exit 1
fi

if [[ ! -f "$VENDOR_PACKAGE_DIR/dist/bin/just-bash.js" ]]; then
  echo "Missing built just-bash package dist/bin/just-bash.js at $VENDOR_PACKAGE_DIR" >&2
  echo "Run: (cd vendor/just-bash && pnpm install && pnpm build)" >&2
  exit 1
fi

if [[ ! -f "$VENDOR_PACKAGE_DIR/dist/bin/shell/shell.js" ]]; then
  echo "Missing built just-bash package dist/bin/shell/shell.js at $VENDOR_PACKAGE_DIR" >&2
  echo "Run: (cd vendor/just-bash && pnpm install && pnpm build)" >&2
  exit 1
fi

if [[ ! -f "$VENDOR_PACKAGE_DIR/src/commands/python3/worker.js" ]]; then
  echo "Missing built just-bash package python worker at $VENDOR_PACKAGE_DIR" >&2
  echo "Run: (cd vendor/just-bash && pnpm install && pnpm build)" >&2
  exit 1
fi

JS_EXEC_WORKER_TS="src/commands/js-exec/js-exec-worker.ts"
if [[ ! -f "$VENDOR_PACKAGE_DIR/$JS_EXEC_WORKER_TS" ]]; then
  JS_EXEC_WORKER_TS="src/commands/js-exec/worker.ts"
fi
if [[ ! -f "$VENDOR_PACKAGE_DIR/$JS_EXEC_WORKER_TS" ]]; then
  echo "Missing just-bash package js-exec worker source at $VENDOR_PACKAGE_DIR" >&2
  echo "Run: (cd vendor/just-bash && pnpm install && pnpm build)" >&2
  exit 1
fi

PACKAGE_VERSION=$(python - <<PY
import json
from pathlib import Path
print(json.loads(Path(r"$VENDOR_PACKAGE_DIR/package.json").read_text())["version"])
PY
)

resolve_cpython_assets() {
  local source_dir="$VENDOR_PACKAGE_DIR/vendor/cpython-emscripten"
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

resolve_sql_wasm() {
  local wasm_path
  wasm_path=$(find "$VENDOR_DIR/node_modules" -path '*/sql.js/dist/sql-wasm.wasm' | head -n 1)
  if [[ -z "$wasm_path" ]]; then
    echo "Could not find sql.js sql-wasm.wasm in vendor/just-bash/node_modules" >&2
    echo "Run: (cd vendor/just-bash && pnpm install)" >&2
    exit 1
  fi
  printf '%s' "$wasm_path"
}

mkdir -p "$TMP_DIR/runtime/dist/bundle/chunks"
cp -R "$VENDOR_PACKAGE_DIR/dist/bin" "$TMP_DIR/runtime/dist/bin"

(
  cd "$VENDOR_PACKAGE_DIR"
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
import re

bundle_root = Path(r"$TMP_DIR/runtime/dist/bundle")
chunks_dir = bundle_root / "chunks"
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

index_path = bundle_root / "index.js"
index_text = index_path.read_text()
flag_coverage_pattern = re.compile(
    r'''if \(ctx\.coverage(?: && true)?\) \{\n\s+const \{ emitFlagCoverage \} = await import\("(?P<chunk>\./chunks/flag-coverage-[^"]+\.js)"\);\n\s+emitFlagCoverage\(ctx\.coverage, def\.name, args\);\n\s+\}'''
)
match = flag_coverage_pattern.search(index_text)
if match is None:
    raise SystemExit("Could not patch optional flag-coverage import in packaged runtime bundle")

replacement = f'''if (ctx.coverage) {{
      try {{
        const {{ emitFlagCoverage }} = await import("{match.group("chunk")}");
        emitFlagCoverage(ctx.coverage, def.name, args);
      }} catch {{
        // The packaged runtime only needs core coverage hits. Some optional
        // fuzzing-oriented flag metadata chunks pull in dependencies that are
        // not safe to initialize in this bundled ESM artifact.
      }}
    }}'''
index_path.write_text(flag_coverage_pattern.sub(replacement, index_text, count=1))
PY

cp "$VENDOR_PACKAGE_DIR/src/commands/python3/worker.js" "$TMP_DIR/runtime/dist/bundle/chunks/worker.js"
(
  cd "$VENDOR_PACKAGE_DIR"
  npx esbuild "$JS_EXEC_WORKER_TS" \
    --bundle \
    --platform=node \
    --format=esm \
    --outfile="$TMP_DIR/runtime/dist/bundle/chunks/js-exec-worker.js"
)
cp "$(resolve_quickjs_wasm)" "$TMP_DIR/runtime/dist/bundle/chunks/emscripten-module.wasm"

# sqlite3 was inlined in the main bundle prior to just-bash 2.14.4. Starting in
# 2.14.4 it runs in a worker thread, so the bundle needs a sibling sqlite3-worker.js
# (with sql.js inlined since the wheel ships no node_modules) and sql-wasm.wasm.
SQLITE3_WORKER_TS="src/commands/sqlite3/worker.ts"
if [[ -f "$VENDOR_PACKAGE_DIR/$SQLITE3_WORKER_TS" ]]; then
  # The banner restores a working `require` for sql.js, which is CJS and uses
  # dynamic `require("node:fs")` — esbuild's default __require shim throws on
  # dynamic specifiers when emitting ESM.
  (
    cd "$VENDOR_PACKAGE_DIR"
    npx esbuild "$SQLITE3_WORKER_TS" \
      --bundle \
      --platform=node \
      --format=esm \
      --banner:js='import { createRequire as __jpbCreateRequire } from "node:module"; import { fileURLToPath as __jpbFileURLToPath } from "node:url"; import { dirname as __jpbDirname } from "node:path"; const require = __jpbCreateRequire(import.meta.url); const __filename = __jpbFileURLToPath(import.meta.url); const __dirname = __jpbDirname(__filename);' \
      --outfile="$TMP_DIR/runtime/dist/bundle/chunks/sqlite3-worker.js"
  )
  cp "$(resolve_sql_wasm)" "$TMP_DIR/runtime/dist/bundle/chunks/sql-wasm.wasm"
fi

resolve_cpython_assets
mkdir -p "$TMP_DIR/runtime/vendor"
cp -R "$TMP_DIR/cpython-emscripten" "$TMP_DIR/runtime/vendor/cpython-emscripten"

rm -rf "$STAGING_DIR"
mkdir -p "$STAGING_DIR"
cp "$VENDOR_PACKAGE_DIR/package.json" "$STAGING_DIR/package.json"
cp -R "$TMP_DIR/runtime/dist" "$STAGING_DIR/dist"
cp -R "$TMP_DIR/runtime/vendor" "$STAGING_DIR/vendor"
rm -rf "$OUT_DIR"
mv "$STAGING_DIR" "$OUT_DIR"
