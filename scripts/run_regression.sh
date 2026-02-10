#!/usr/bin/env sh
set -e

ROOT_DIR="$(cd "$(dirname "$0")/.." && pwd)"

PYTHONPATH="$ROOT_DIR/src" pytest -q \
  "$ROOT_DIR/tests/integration/test_regression_suite.py" \
  "$ROOT_DIR/tests/integration/test_chinese_phrase_cases.py"
