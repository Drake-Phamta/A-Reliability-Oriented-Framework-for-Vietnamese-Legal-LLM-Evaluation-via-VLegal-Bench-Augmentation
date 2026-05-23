# Huong Dan Tinh Chinh Ollama Tren Ubuntu (de chay GPU thue)

Tai lieu nay viet cho Ubuntu va theo kieu "copy-paste tung lenh".
Muc tieu la tang toc do nhung van on dinh (khong OOM, khong bi rong prediction).

## 1) Kiem tra nhanh truoc khi tuning

Chay lan luot:

```bash
cd /path/to/A-Reliability-Oriented-Framework-for-Vietnamese-Legal-LLM-Evaluation-via-VLegal-Bench-Augmentation

which ollama
ollama --version
systemctl status ollama --no-pager
nvidia-smi
```

Neu `systemctl status ollama` chua la `active (running)`, chay:

```bash
sudo systemctl start ollama
sudo systemctl status ollama --no-pager
```

## 2) Chay baseline (de so sanh truoc/sau)

Muc dich: ghi thoi gian goc truoc khi tuning.

```bash
cd /path/to/A-Reliability-Oriented-Framework-for-Vietnamese-Legal-LLM-Evaluation-via-VLegal-Bench-Augmentation

time PROMPT_MODE=reasoning \
BATCH_SIZE=1 \
MAX_CONCURRENCY=1 \
REASONING_FAST_TOKENS=256 \
REASONING_FALLBACK_TOKENS=2048 \
bash infer.sh 1.2
```

Ban ghi lai:

- Tong thoi gian (`real` trong output `time`)
- Co bi prediction rong hay khong
- GPU VRAM trong luc chay (`watch -n 1 nvidia-smi`)

## 3) Tinh chinh Ollama tam thoi (cho current shell)

Buoc nay de thu nghiem nhanh.

```bash
export OLLAMA_NUM_PARALLEL=2
export OLLAMA_KEEP_ALIVE=-1
export OLLAMA_CONTEXT_LENGTH=8192
export OLLAMA_MAX_QUEUE=512
export OLLAMA_FLASH_ATTENTION=1
# Chi bat neu server/model ho tro:
# export OLLAMA_KV_CACHE_TYPE=q8_0
```

Sau do restart service:

```bash
sudo systemctl restart ollama
sleep 2
systemctl status ollama --no-pager
```

## 4) Dat cau hinh vinh vien cho systemd (khuyen dung tren server)

Tao file override:

```bash
sudo mkdir -p /etc/systemd/system/ollama.service.d
sudo tee /etc/systemd/system/ollama.service.d/override.conf > /dev/null <<'EOF'
[Service]
Environment="OLLAMA_NUM_PARALLEL=2"
Environment="OLLAMA_KEEP_ALIVE=-1"
Environment="OLLAMA_CONTEXT_LENGTH=8192"
Environment="OLLAMA_MAX_QUEUE=512"
Environment="OLLAMA_FLASH_ATTENTION=1"
# Environment="OLLAMA_KV_CACHE_TYPE=q8_0"
EOF
```

Ap dung cau hinh:

```bash
sudo systemctl daemon-reload
sudo systemctl restart ollama
sudo systemctl status ollama --no-pager
```

Kiem tra bien da vao service chua:

```bash
systemctl show ollama --property=Environment
```

## 5) Lenh chay repo sau tuning

### 5.1 Test reasoning mode (co speedup + fallback)

```bash
cd /path/to/A-Reliability-Oriented-Framework-for-Vietnamese-Legal-LLM-Evaluation-via-VLegal-Bench-Augmentation

time PROMPT_MODE=reasoning \
BATCH_SIZE=4 \
MAX_CONCURRENCY=4 \
REASONING_FAST_TOKENS=256 \
REASONING_FALLBACK_TOKENS=2048 \
MAX_EMPTY_RETRIES=1 \
bash infer.sh 1.2
```

### 5.2 Test non-reasoning mode (khong bat speedup reasoning)

```bash
time PROMPT_MODE=fewshot \
BATCH_SIZE=4 \
MAX_CONCURRENCY=4 \
bash infer.sh 1.2
```

### 5.3 Chay full task

```bash
time bash run_all_task.sh
```

## 6) Cach tang dan de tranh OOM

Lam theo thu tu nay, moi lan doi 1 tham so roi benchmark lai:

1. Bat dau an toan:
   - `OLLAMA_NUM_PARALLEL=1`
   - `BATCH_SIZE=2`
   - `MAX_CONCURRENCY=2`
2. Neu on dinh, tang:
   - `OLLAMA_NUM_PARALLEL` len `2`, roi `3`
3. Neu van on, tang tiep:
   - `BATCH_SIZE` len `4`
   - `MAX_CONCURRENCY` len `4`
4. Neu gap loi (OOM/timeout/rong output):
   - Giam `OLLAMA_NUM_PARALLEL` truoc
   - Roi giam `MAX_CONCURRENCY`
   - Cuoi cung moi giam `OLLAMA_CONTEXT_LENGTH`

## 7) Bang cau hinh goi y ban dau (de copy nhanh)

Neu GPU tam 24GB-48GB, thu bo nay truoc:

```bash
export OLLAMA_NUM_PARALLEL=2
export OLLAMA_KEEP_ALIVE=-1
export OLLAMA_CONTEXT_LENGTH=8192
export OLLAMA_MAX_QUEUE=512
export OLLAMA_FLASH_ATTENTION=1

export BATCH_SIZE=4
export MAX_CONCURRENCY=4
export REASONING_FAST_TOKENS=256
export REASONING_FALLBACK_TOKENS=2048
export MAX_EMPTY_RETRIES=1
```

## 8) Neu muon quay lai mac dinh

Xoa override systemd:

```bash
sudo rm -f /etc/systemd/system/ollama.service.d/override.conf
sudo systemctl daemon-reload
sudo systemctl restart ollama
```

Xoa bien hien tai trong shell:

```bash
unset OLLAMA_NUM_PARALLEL
unset OLLAMA_KEEP_ALIVE
unset OLLAMA_CONTEXT_LENGTH
unset OLLAMA_MAX_QUEUE
unset OLLAMA_FLASH_ATTENTION
unset OLLAMA_KV_CACHE_TYPE
```

## 9) Nho nhanh

- `REASONING_FALLBACK_TOKENS` de cao de tranh prediction rong.
- Uu tien giam parallel/concurrency truoc khi giam token fallback.
- Moi khi doi model/quant/GPU, benchmark lai tu dau.
