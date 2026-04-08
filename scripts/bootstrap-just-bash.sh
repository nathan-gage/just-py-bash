#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "$0")/../vendor/just-bash"
pnpm install
pnpm build
