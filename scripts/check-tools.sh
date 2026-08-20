#!/usr/bin/env bash
# Detect available tools for the starsieve pipeline.
# Prints a status report to stdout. Exits 0 if gh is authenticated.
# Usage: check-tools.sh [task-dir]  (task-dir optional, enables logging)
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
TASK_DIR="${1:-}"
LOG() {
  [ -n "$TASK_DIR" ] && bash "$SCRIPT_DIR/log.sh" "$TASK_DIR" "$@" || true
}

echo "🔍 Tool availability:"

# gh CLI (mandatory)
if command -v gh &>/dev/null && gh auth status &>/dev/null 2>&1; then
  USER=$(gh api user --jq .login 2>/dev/null || echo "unknown")
  echo "  ✅ gh CLI        — authenticated as @$USER"
  GH_OK=1
  LOG PHASE0 OK "gh CLI authenticated as @$USER"
else
  echo "  ❌ gh CLI        — not authenticated (run: gh auth login)"
  GH_OK=0
  LOG PHASE0 FAIL "gh CLI not authenticated"
fi

# Ollama (optional) — check local and cloud independently
OLLAMA_LOCAL=0
OLLAMA_CLOUD=0
OLLAMA_MODE="unavailable"

if command -v ollama &>/dev/null && ollama list &>/dev/null 2>&1; then
  MODELS=$(ollama list 2>/dev/null | tail -n +2 | head -3 | awk '{print $1}' | tr '\n' ',' | sed 's/,$//')
  echo "  ✅ Ollama local  — $MODELS"
  OLLAMA_LOCAL=1
  LOG PHASE0 OK "Ollama local available: $MODELS"
fi

if [ -n "${OLLAMA_API_KEY:-}" ]; then
  echo "  ✅ Ollama cloud  — API key set"
  OLLAMA_CLOUD=1
  LOG PHASE0 OK "Ollama cloud available (API key set)"
fi

if [ $OLLAMA_LOCAL -eq 1 ] && [ $OLLAMA_CLOUD -eq 1 ]; then
  echo "  ⚠️  Both Ollama local and cloud available — agent must ask user which to prefer."
  echo "     Local: free, no latency. Cloud: pay per token, larger models, any machine."
  LOG PHASE0 INFO "Both Ollama local and cloud available — agent must ask user preference"
elif [ $OLLAMA_LOCAL -eq 1 ]; then
  OLLAMA_MODE="local"
elif [ $OLLAMA_CLOUD -eq 1 ]; then
  OLLAMA_MODE="cloud"
else
  echo "  ❌ Ollama        — not available (main LLM will handle classification)"
  LOG PHASE0 WARN "Ollama not available, main LLM will handle classification"
fi

# DeepWiki (optional — can't detect from shell, agent must check)
echo "  ❓ DeepWiki      — agent must verify MCP connection"
LOG PHASE0 INFO "DeepWiki: agent must verify MCP connection"

# Sideshow (optional — can't detect from shell, agent must check)
echo "  ❓ Sideshow      — agent must verify connection"
LOG PHASE0 INFO "Sideshow: agent must verify connection"

# jq (recommended)
if command -v jq &>/dev/null; then
  echo "  ✅ jq            — available"
  LOG PHASE0 OK "jq available"
else
  echo "  ❌ jq            — not available (scripts fall back to python)"
  LOG PHASE0 WARN "jq not available, scripts fall back to python"
fi

if [ "$GH_OK" -eq 0 ]; then
  echo ""
  echo "FATAL: gh CLI is not authenticated. Run: gh auth login"
  exit 1
fi