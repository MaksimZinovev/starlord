#!/usr/bin/env bash
# Pull the user's starred repos from GitHub. Uses shared cache.
# Usage: pull-stars.sh {task-dir} [--refresh] [--output PATH]
# Output: JSON array of starred repos to stdout (or --output file)
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
TASK_DIR="${1:-.}"
shift || true

CACHE_DIR="${STARSIEVE_CACHE_DIR:-$HOME/.cache/starsieve}"
CACHE_FILE="$CACHE_DIR/raw-stars.json"
AGE_FILE="$CACHE_DIR/raw-stars.age"
REFRESH=0
OUTPUT=""

while [[ $# -gt 0 ]]; do
  case "$1" in
    --refresh) REFRESH=1; shift ;;
    --output)  OUTPUT="$2"; shift 2 ;;
    *) echo "Unknown arg: $1" >&2; exit 1 ;;
  esac
done

mkdir -p "$CACHE_DIR"
LOG() { bash "$SCRIPT_DIR/log.sh" "$TASK_DIR" "$@"; }

# Check cache freshness (default: 24h)
if [ "$REFRESH" -eq 0 ] && [ -f "$CACHE_FILE" ]; then
  CACHE_AGE=$(( $(date +%s) - $(stat -f %m "$CACHE_FILE" 2>/dev/null || stat -c %Y "$CACHE_FILE" 2>/dev/null || echo 0) ))
  if [ "$CACHE_AGE" -lt 86400 ]; then
    echo "Using cached stars ($CACHE_AGE seconds old). Use --refresh to re-pull." >&2
    LOG PHASE2 OK "cache hit ($CACHE_AGE seconds old), $([ -f "$CACHE_FILE" ] && jq 'length' "$CACHE_FILE" 2>/dev/null || echo '?') repos"
    if [ -n "$OUTPUT" ]; then cp "$CACHE_FILE" "$OUTPUT"; else cat "$CACHE_FILE"; fi
    exit 0
  fi
  echo "Cache stale ($CACHE_AGE seconds old). Re-pulling..." >&2
  LOG PHASE2 INFO "cache stale ($CACHE_AGE seconds old), re-pulling"
fi

# Pull all starred repos with pagination
echo "Pulling starred repos from GitHub..." >&2
gh api user/starred --paginate --jq '[
  .[] | {
    full_name,
    description,
    language,
    stargazers_count,
    pushed_at,
    license: .license.spdx_id,
    topics,
    html_url,
    fork,
    archived
  }
]' > "$CACHE_FILE"

date +%s > "$AGE_FILE"
COUNT=$(jq 'length' "$CACHE_FILE")
echo "Pulled $COUNT starred repos." >&2
LOG PHASE2 OK "pulled $COUNT starred repos from GitHub API"

if [ -n "$OUTPUT" ]; then cp "$CACHE_FILE" "$OUTPUT"; else cat "$CACHE_FILE"; fi