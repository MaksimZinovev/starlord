#!/usr/bin/env bash
# Append a structured entry to the task run log.
# Usage: log.sh {task-dir} {PHASE} {STATUS} {message...}
# Example: log.sh ./.starsieve/my-task PHASE0 OK "gh authenticated as @user"
#          log.sh ./.starsieve/my-task PHASE2 FALLBACK "Ollama unavailable, LLM classifying"
set -euo pipefail

TASK_DIR="$1"
PHASE="$2"
STATUS="$3"
shift 3
MSG="$*"
LOG_FILE="$TASK_DIR/run.log"

mkdir -p "$TASK_DIR"
TS=$(date -u +"%Y-%m-%dT%H:%M:%SZ")
echo "[$TS] [$PHASE] [$STATUS] $MSG" >> "$LOG_FILE"