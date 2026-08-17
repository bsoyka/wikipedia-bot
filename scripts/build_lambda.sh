#!/usr/bin/env bash
# Build Lambda deployment artifacts for BsoykaBot.
#
# Usage:
#   scripts/build_lambda.sh layer   # dependency closure -> build/layer/python
#   scripts/build_lambda.sh code    # bsoykabot itself    -> build/code
#
# Both artifacts are built for the Lambda runtime's platform (arm64 Linux,
# Python 3.13) regardless of the host this script runs on. That matters
# because mwparserfromhell ships a compiled tokenizer extension: installing
# it without pinning the target platform would happily install whatever
# wheel matches the *build* host (e.g. macOS/arm64) instead, which then
# fails to import on Lambda. --only-binary=:all: turns a missing
# linux/aarch64 wheel for any dependency into a build failure here, rather
# than a silent ImportError at runtime.
#
# Paths are resolved relative to the repository root regardless of the
# working directory from which the script is invoked.

set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
PYTHON_VERSION="3.13"
PYTHON_PLATFORM="aarch64-unknown-linux-gnu"

build_layer() {
  local dest="$REPO_ROOT/build/layer/python"
  local requirements="$REPO_ROOT/build/layer-requirements.txt"

  rm -rf "$dest"
  mkdir -p "$dest" "$(dirname "$requirements")"

  # --no-default-groups: pyproject.toml opts dev/tests/typing into every
  # ordinary uv command via [tool.uv].default-groups, but the layer must
  # ship only [project.dependencies] -- pytest, mypy, and friends have no
  # business in a production Lambda artifact.
  uv export \
    --project "$REPO_ROOT" \
    --frozen \
    --no-default-groups \
    --no-emit-project \
    --format requirements.txt \
    >"$requirements"

  uv pip install \
    --python-platform "$PYTHON_PLATFORM" \
    --python-version "$PYTHON_VERSION" \
    --only-binary=:all: \
    --target "$dest" \
    -r "$requirements"

  # boto3 is provided by the Lambda runtime itself; shipping another copy
  # in the layer would only make it bigger for no benefit.
  rm -rf \
    "$dest"/boto3 "$dest"/boto3-*.dist-info \
    "$dest"/botocore "$dest"/botocore-*.dist-info

  echo "Built layer at $dest"
}

build_code() {
  local dest="$REPO_ROOT/build/code"
  local wheelhouse="$REPO_ROOT/build/code-wheel"

  rm -rf "$dest" "$wheelhouse"
  mkdir -p "$dest"

  # Build bsoykabot's own wheel first, rather than pointing uv pip install
  # straight at the project directory: --only-binary=:all: below refuses to
  # build a source distribution, and a directory source always looks like
  # one. bsoykabot is pure Python, so the wheel it builds is
  # platform-independent regardless of the host this script runs on.
  uv build --wheel --out-dir "$wheelhouse" "$REPO_ROOT" >/dev/null

  # --no-deps: the dependency closure lives in the layer, built separately
  # above. This only installs bsoykabot itself, as a real distribution (not
  # a plain file copy) so bsoykabot-*.dist-info lands in the zip -- that's
  # what makes importlib.metadata.version('bsoykabot') resolve correctly at
  # runtime instead of raising PackageNotFoundError.
  uv pip install \
    --python-platform "$PYTHON_PLATFORM" \
    --python-version "$PYTHON_VERSION" \
    --only-binary=:all: \
    --target "$dest" \
    --no-deps \
    "$wheelhouse"/*.whl

  echo "Built code at $dest"
}

case "${1:-}" in
  layer) build_layer ;;
  code) build_code ;;
  *)
    echo "Usage: $0 {layer|code}" >&2
    exit 1
    ;;
esac
