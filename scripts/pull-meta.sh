#!/usr/bin/env bash
# Pull metadata + README for a single repo. Saves to {task-dir}/meta/.
# Usage: pull-meta.sh {task-dir} {owner/repo}
set -euo pipefail

TASK_DIR="$1"
REPO="$2"
SLUG=$(echo "$REPO" | tr '/' '_')
META_DIR="$TASK_DIR/meta"
mkdir -p "$META_DIR"

# Pull repo metadata
gh api "repos/$REPO" --jq '{
  full_name,
  description,
  language,
  stargazers_count,
  forks_count,
  watchers_count,
  open_issues_count,
  license: .license.spdx_id,
  topics,
  pushed_at,
  created_at,
  archived,
  html_url,
  homepage
}' > "$META_DIR/${SLUG}_meta.json"

# Pull README (decoded from base64)
gh api "repos/$REPO/readme" --jq '.content' 2>/dev/null | base64 -d > "$META_DIR/${SLUG}_readme.md" 2>/dev/null || {
  echo "WARNING: Could not fetch README for $REPO" >&2
  echo "(no README)" > "$META_DIR/${SLUG}_readme.md"
}

# Pull latest release info
gh api "repos/$REPO/releases/latest" --jq '{tag_name, published_at}' 2>/dev/null > "$META_DIR/${SLUG}_release.json" || {
  echo '{"tag_name": null, "published_at": null}' > "$META_DIR/${SLUG}_release.json"
}

# Pull issue stats (open/closed counts)
OPEN=$(gh api "repos/$REPO/issues?state=open&per_page=1" --jq 'length' 2>/dev/null || echo "?")
CLOSED=$(gh api "search/issues?q=repo:'"$REPO"'+is:issue+is:closed&per_page=1" --jq '.total_count' 2>/dev/null || echo "?")

# Merge issue stats into meta
if command -v jq &>/dev/null; then
  jq --arg open "$OPEN" --arg closed "$CLOSED" \
    '. + {open_issues_count: $open, closed_issues_count: $closed}' \
    "$META_DIR/${SLUG}_meta.json" > "$META_DIR/${SLUG}_meta.tmp" && \
    mv "$META_DIR/${SLUG}_meta.tmp" "$META_DIR/${SLUG}_meta.json"
fi

echo "Saved metadata for $REPO → $META_DIR/${SLUG}_meta.json"
echo "Saved README for $REPO → $META_DIR/${SLUG}_readme.md"