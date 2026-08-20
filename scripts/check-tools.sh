#!/usr/bin/env bash
# Detect available tools for the starsieve pipeline.
# Prints a status report to stdout. Exits 0 if gh is authenticated.
set -euo pipefail

echo "🔍 Tool availability:"

# gh CLI (mandatory)
if command -v gh &>/dev/null && gh auth status &>/dev/null 2>&1; then
  USER=$(gh api user --jq .login 2>/dev/null || echo "unknown")
  echo "  ✅ gh CLI        — authenticated as @$USER"
  GH_OK=1
else
  echo "  ❌ gh CLI        — not authenticated (run: gh auth login)"
  GH_OK=0
fi

# Ollama (optional)
if command -v ollama &>/dev/null && ollama list &>/dev/null 2>&1; then
  MODELS=$(ollama list 2>/dev/null | tail -n +2 | head -3 | awk '{print $1}' | tr '\n' ',' | sed 's/,$//')
  echo "  ✅ Ollama local  — $MODELS"
elif [ -n "${OLLAMA_API_KEY:-}" ]; then
  echo "  ✅ Ollama cloud  — API key set"
else
  echo "  ❌ Ollama        — not available (main LLM will handle classification)"
fi

# DeepWiki (optional — can't detect from shell, agent must check)
echo "  ❓ DeepWiki      — agent must verify MCP connection"

# Sideshow (optional — can't detect from shell, agent must check)
echo "  ❓ Sideshow      — agent must verify connection"

# jq (recommended)
if command -v jq &>/dev/null; then
  echo "  ✅ jq            — available"
else
  echo "  ❌ jq            — not available (scripts fall back to python)"
fi

if [ "$GH_OK" -eq 0 ]; then
  echo ""
  echo "FATAL: gh CLI is not authenticated. Run: gh auth login"
  exit 1
fi