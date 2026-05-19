#!/bin/bash

# ===== CONFIG =====
# Điền danh sách task tại đây
TASKS=("1.1")

BATCH_SIZE=1
MODEL_NAME=${OLLAMA_MODEL:-"gemma4:e4b-it-q8_0"}
OLLAMA_BASE_URL=${OLLAMA_BASE_URL:-"http://localhost:11434"}
MAX_MODEL_LEN=${MAX_MODEL_LEN:-8192}
MAX_OUTPUT_TOKENS=${MAX_OUTPUT_TOKENS:-128}
MAX_RETRY=${MAX_RETRY:-1}
PROMPT_MODE=${PROMPT_MODE:-"fewshot"}  # options: zero_shot, fewshot, reasoning, reliability

if [ ${#TASKS[@]} -eq 0 ]; then
    echo "[ERROR] TASKS đang rỗng. Hãy thêm ít nhất 1 task."
    exit 1
fi

TASKS_CSV=$(IFS=,; echo "${TASKS[*]}")

echo "[INFO] Using tasks: ${TASKS_CSV}"
echo "[INFO] Model config: model=${MODEL_NAME}, batch_size=${BATCH_SIZE}, max_model_len=${MAX_MODEL_LEN}, max_output_tokens=${MAX_OUTPUT_TOKENS}, max_retry=${MAX_RETRY}, prompt_mode=${PROMPT_MODE}"

# ===== RUN LOCAL LLM =====
python inference.py \
       --tasks "$TASKS_CSV" \
       --model_name "$MODEL_NAME" \
       --base_url "$OLLAMA_BASE_URL" \
       --max_model_len "$MAX_MODEL_LEN" \
       --max_output_tokens "$MAX_OUTPUT_TOKENS" \
       --max_retry "$MAX_RETRY" \
       --batch_size "$BATCH_SIZE" \
       --prompt_mode "$PROMPT_MODE"
