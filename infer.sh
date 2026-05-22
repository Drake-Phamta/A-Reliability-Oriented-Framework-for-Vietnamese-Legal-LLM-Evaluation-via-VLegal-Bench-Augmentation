#!/bin/bash
if [ -f .env ]; then
  export $(echo $(grep -v '^#' .env | xargs))
fi
# ===== CONFIG =====
TASK=${1:-"1.1"}
TASK_FILE="${TASK//./_}"
BATCH_SIZE=${BATCH_SIZE:-4}
MODEL_NAME=${MODEL_NAME:-"gemma4:e4b-it-q8_0"}
MAX_MODEL_LEN=${MAX_MODEL_LEN:-32768}
PROMPT_MODE=${PROMPT_MODE:-reasoning}
REASONING_MAX_TOKENS=${REASONING_MAX_TOKENS:-2048}

# === New option — default false ===
USE_REMOVE_CONTENT=${USE_REMOVE_CONTENT:-false}

# ===== FILE MATCHING =====
verified_no_remove=($(ls ./${TASK}/${TASK_FILE}*verified_reformatted.jsonl 2>/dev/null | grep -v "remove_content"))
verified_remove=($(ls ./${TASK}/${TASK_FILE}*remove_content_verified_reformatted.jsonl 2>/dev/null))
no_verified=($(ls ./${TASK}/${TASK_FILE}*reformatted.jsonl 2>/dev/null | grep -v "remove_content"))
base_jsonl=($(ls ./${TASK}/${TASK_FILE}*.jsonl 2>/dev/null | grep -v -E "remove_content|reformatted"))

# ===== SELECT DATASET =====
if [ "$USE_REMOVE_CONTENT" = true ]; then
    echo "[INFO] USE_REMOVE_CONTENT=true → ưu tiên file remove_content"
    if [ -f "${verified_remove[0]}" ]; then
        DATASET_FILE="${verified_remove[0]}"
    else
        echo "[WARN] Không tìm thấy file remove_content, fallback sang file thường."
        DATASET_FILE="${verified_no_remove[0]:-${base_jsonl[0]}}"
    fi
else
    echo "[INFO] USE_REMOVE_CONTENT=false → ưu tiên file không remove_content"
    if [ -n "${verified_no_remove[0]}" ]; then
        DATASET_FILE="${verified_no_remove[0]}"
    else
        echo "[WARN] Không có file thường, dùng file normal."
        DATASET_FILE="${no_verified[0]:-${base_jsonl[0]}}"
    fi
fi

echo "[INFO] Using dataset: $DATASET_FILE"
echo "[INFO] Model: $MODEL_NAME"
echo "[INFO] Batch size: $BATCH_SIZE | Max model len: $MAX_MODEL_LEN"
echo "[INFO] Prompt mode: $PROMPT_MODE"
echo "[INFO] Reasoning max tokens: $REASONING_MAX_TOKENS"
echo "[INFO] OPENAI_BASE_URL: ${OPENAI_BASE_URL:-"(default from inference.py)"}"

if [ -z "$DATASET_FILE" ]; then
    echo "[ERROR] Không tìm thấy dataset cho task $TASK"
    exit 1
fi

# ===== RUN LOCAL LLM =====
.venv/bin/python inference.py \
       --dataset_path "$DATASET_FILE" \
       --model_name "$MODEL_NAME" \
       --max_model_len "$MAX_MODEL_LEN" \
       --batch_size "$BATCH_SIZE" \
       --prompt_mode "$PROMPT_MODE" \
       --reasoning_max_tokens "$REASONING_MAX_TOKENS"
