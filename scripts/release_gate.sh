#!/usr/bin/env sh

set -eu

BRANCH="${1:-}"
VERSION="${2:-}"

if [ -z "$BRANCH" ] || [ -z "$VERSION" ]; then
  echo "Usage: scripts/release_gate.sh <branch> <version>" >&2
  echo "Example: scripts/release_gate.sh main 1.0.0" >&2
  exit 2
fi

is_stable_version() {
  echo "$1" | grep -Eq '^[0-9]+\.[0-9]+\.[0-9]+$'
}

is_preview_version() {
  echo "$1" | grep -Eq '^[0-9]+\.[0-9]+\.[0-9]+-(beta|rc)\.[0-9]+$'
}

case "$BRANCH" in
  main)
    if is_stable_version "$VERSION"; then
      echo "OK: main accepts stable version '$VERSION'."
      exit 0
    fi
    echo "ERROR: main only accepts stable versions like 1.0.0" >&2
    exit 1
    ;;
  next)
    if is_preview_version "$VERSION"; then
      echo "OK: next accepts preview version '$VERSION'."
      exit 0
    fi
    echo "ERROR: next only accepts preview versions like 1.1.0-beta.1 or 1.1.0-rc.1" >&2
    exit 1
    ;;
  *)
    echo "WARN: no strict rule for branch '$BRANCH' (feature/dev branch)." >&2
    exit 0
    ;;
esac
