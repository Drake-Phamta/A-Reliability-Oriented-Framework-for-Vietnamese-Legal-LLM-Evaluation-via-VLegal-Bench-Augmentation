#!/bin/bash
set -u

# Danh sách các task
TASKS=(
  "1.1" "1.2" "1.3" "1.4" "1.5"
  "2.1" "2.2" "2.3" "2.4" "2.5"
  "3.1" "3.2" "3.3" "3.4" "3.5"
  "4.1" "4.2" "4.3"
  "5.1" "5.2" "5.3" "5.4"
)

# ===== EVAL OUTPUT =====
EVAL_FILE="EVAL.md"
# Nếu KEEP_OLD_EVAL=true thì giữ nội dung cũ, mặc định tạo file mới cho mỗi lượt run_all
KEEP_OLD_EVAL=${KEEP_OLD_EVAL:-false}

if [ "$KEEP_OLD_EVAL" != true ]; then
    if [ -f "$EVAL_FILE" ]; then
        cp "$EVAL_FILE" "${EVAL_FILE}.bak.$(date +%Y%m%d_%H%M%S)"
    fi
    {
        echo "| Task | Model | Accuracy | Precision | Recall | F1-Score | Macro-F1 | BLEU | ROUGE |"
        echo "|---|---|---|---|---|---|---|---|---|"
    } > "$EVAL_FILE"
    echo "[INFO] Reset $EVAL_FILE for this run."
else
    echo "[INFO] KEEP_OLD_EVAL=true -> append/update existing $EVAL_FILE."
fi

# Chạy lần lượt
for task in "${TASKS[@]}"; do
    echo "======================================"
    echo ">>> Đang chạy Task $task ..."
    echo "======================================"
    bash infer.sh "$task"
    if [ $? -ne 0 ]; then
        echo "Lỗi khi chạy Task $task. Tiếp tục với task khác..."
    fi
done

echo "Đã chạy xong tất cả các task! Kết quả được cập nhật trong $EVAL_FILE"
