#!/bin/bash
set -euo pipefail

# Run all task folders that match X.Y (for example: 1.1, 3.4, 5.3)
# You can override task list by setting TASKS_CSV manually.

BATCH_SIZE="${BATCH_SIZE:-1}"
MODEL_NAME="${OLLAMA_MODEL:-gemma4:e4b}"
OLLAMA_BASE_URL="${OLLAMA_BASE_URL:-http://localhost:11434}"
MAX_MODEL_LEN="${MAX_MODEL_LEN:-8192}"
MAX_OUTPUT_TOKENS="${MAX_OUTPUT_TOKENS:-128}"
MAX_RETRY="${MAX_RETRY:-1}"
PROMPT_MODE="${PROMPT_MODE:-fewshot}"  # zero_shot, fewshot, reasoning, reliability
TASKS_CSV="${TASKS_CSV:-}"

if [[ -z "$TASKS_CSV" ]]; then
  declare -a TASKS=()
  for d in */; do
    task="${d%/}"
    if [[ "$task" =~ ^[0-9]+\.[0-9]+$ ]]; then
      TASKS+=("$task")
    fi
  done

  if [[ ${#TASKS[@]} -eq 0 ]]; then
    echo "[ERROR] No task directories found (expected pattern X.Y)."
    exit 1
  fi

  mapfile -t TASKS_SORTED < <(printf "%s\n" "${TASKS[@]}" | sort -V)
  TASKS_CSV="$(IFS=,; echo "${TASKS_SORTED[*]}")"
fi

echo "[INFO] Running tasks: ${TASKS_CSV}"
echo "[INFO] Model config: model=${MODEL_NAME}, batch_size=${BATCH_SIZE}, max_model_len=${MAX_MODEL_LEN}, max_output_tokens=${MAX_OUTPUT_TOKENS}, max_retry=${MAX_RETRY}, prompt_mode=${PROMPT_MODE}"

python inference.py \
  --tasks "${TASKS_CSV}" \
  --model_name "${MODEL_NAME}" \
  --base_url "${OLLAMA_BASE_URL}" \
  --max_model_len "${MAX_MODEL_LEN}" \
  --max_output_tokens "${MAX_OUTPUT_TOKENS}" \
  --max_retry "${MAX_RETRY}" \
  --batch_size "${BATCH_SIZE}" \
  --prompt_mode "${PROMPT_MODE}"
