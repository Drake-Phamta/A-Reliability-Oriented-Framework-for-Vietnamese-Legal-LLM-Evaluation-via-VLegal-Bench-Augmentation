# Directory Structure

**Last updated**: 2026-05-26

## Root: `D:\AI_LEGAL\`

```
D:\AI_LEGAL\
├── README.md                    Project overview & quick start
├── PROJECT_STATUS.md            Current progress, results, known issues
├── ROADMAP.md                   Next steps & pending tasks
├── DIRECTORY_STRUCTURE.md       This file
├── agent.md                     Workstation SSH connection rules
├── .claude/                     Claude Code config
│
├── paper/                       Paper submission
│   ├── main.tex                 LaTeX source (ICIS 2026)
│   └── references/              Reference documents
│       ├── icis2026_lkg__Copy_.pdf
│       └── legal_llm_paper_ptit.docx
│
├── scripts/                     Executable scripts
│   ├── inference/               Model inference scripts
│   │   ├── run_inference.py     Main inference runner
│   │   ├── run_improved_inference.py  Enhanced prompt inference
│   │   ├── run_41_proposed.py   Task 4.1 proposed method
│   │   ├── run_41_recovery.py   Task 4.1 recovery
│   │   ├── run_42_recovery.py   Task 4.2 recovery
│   │   └── merge_adapter.py     LoRA adapter merging
│   ├── evaluation/              Metrics & evaluation
│   │   └── run_metrics_when_ready.py
│   └── launchers/               Batch/PowerShell launchers
│       ├── launch.bat
│       ├── launch2.bat
│       ├── run_inference.bat
│       ├── run_inference_b3_*.bat  (5 variants)
│       ├── run_inference_proposed.bat
│       ├── run_inference_reliability.bat
│       ├── run_inference_remaining.bat
│       ├── run_inference_test.bat
│       ├── run_metrics.bat
│       ├── run_rel_launcher.bat
│       ├── run_rel_temp.bat
│       ├── run_reliability.ps1
│       ├── run_reliability_inf.bat
│       ├── run_reliability_ws.bat
│       ├── launch_reliability.ps1
│       ├── launch_reliability.py
│       ├── setup_inference_task.ps1
│       ├── setup_test_inference.ps1
│       ├── test_load.bat
│       └── merge_adapter.bat
│
├── data/                        Project data
│   ├── annotations/             Annotated reliability data
│   │   ├── 1_4_annotated.jsonl
│   │   ├── 1_5_annotated.jsonl
│   │   ├── 3_1_annotated.jsonl
│   │   ├── 3_3_annotated.jsonl
│   │   ├── 4_1_annotated.jsonl
│   │   └── 4_2_annotated.jsonl
│   └── raft_at/                 RAFT-AT training data
│       └── raft_at_proposed.jsonl
│
└── VLegal-Bench/                Main benchmark (inherited + extended)
    ├── README.md                Original benchmark docs
    ├── TEAM_GUIDE.md            Team workflow
    ├── pyproject.toml           Python project config
    ├── requirements.txt         Dependencies
    ├── LICENSE.txt              License
    ├── .env.example             Environment template
    ├── setup.bat / setup.sh     Setup scripts
    ├── vllm_serving.sh          VLLM server launcher
    │
    ├── src/                     Core library
    │   ├── evaluation.py        Main evaluation logic
    │   ├── reliability_metrics.py  Reliability metric computation
    │   ├── calculate_all_metrics.py  Aggregate metrics
    │   ├── calculate_core_metrics_v2.py  Core metrics v2
    │   ├── calculate_core_metrics.py  Core metrics v1
    │   └── analyze_results.py   Result analysis
    │
    ├── tools/                   Utility scripts
    │   ├── finetune_lora.py     Original LoRA fine-tuning
    │   ├── finetune_raft_at.py  RAFT-AT fine-tuning (novel)
    │   ├── prepare_raft_at_data.py  RAFT-AT data preparation
    │   ├── auto_annotate.py     Auto-annotation with LLM
    │   ├── annotation_tool.py   Manual annotation CLI
    │   ├── calculate_iaa.py     Inter-annotator agreement
    │   ├── run_experiments.py   Experiment runner
    │   ├── evaluate_experiments.py  Experiment evaluation
    │   ├── generate_tables.py   LaTeX table generation
    │   ├── generate_figure1.py  Framework figure
    │   ├── create_tracking_doc.py  Paper tracking
    │   ├── create_annotation_subset.py  Annotation subsets
    │   ├── update_annotation_protocol.py  Protocol updater
    │   ├── fill_paper_details.py  Paper detail filler
    │   ├── generate_section5_draft.py  Section 5 draft
    │   ├── verify_experiments.py  Experiment verification
    │   ├── progress.py          Progress tracking
    │   └── colab_annotate.py    Colab annotation helper
    │
    ├── annotations/             Annotation subsets & manual labels
    │   ├── *_annotated.jsonl    Manual annotations (5 files)
    │   ├── *_subset.jsonl       Annotation subsets (6 files)
    │   ├── auto_extracted/      Auto-extracted annotations
    │   └── note.md              Annotation notes
    │
    ├── colab_annotation/        Colab annotation pipeline
    │   ├── *_llm_input.jsonl    LLM inputs (6 files)
    │   ├── *_stats.json         Statistics (6 files)
    │   ├── colab_notebook.py    Colab notebook
    │   ├── manual_annotations/  Manual annotations from Colab
    │   └── README.md            Pipeline docs
    │
    ├── data/                    Training data
    │   ├── raft_at_proposed.jsonl  RAFT-AT training data (41MB)
    │   └── raft_at_proposed_stats.json
    │
    ├── docs/                    Documentation
    │   ├── annotation_guideline.md
    │   ├── annotation_protocol_final.md
    │   ├── GITHUB_ISSUES.md
    │   ├── PLAN_2WEEKS.md
    │   └── section5_draft.md
    │
    ├── templates/               Jinja prompt templates (10 files)
    │   ├── gemma.jinja
    │   ├── vlsp-qwen3-4b.jinja
    │   └── ... (8 more)
    │
    ├── experiments/             Experiment artifacts
    │   ├── latex/
    │   │   └── figure1_framework.png
    │   ├── logs/                (empty)
    │   ├── models/              (empty)
    │   └── results/             (empty)
    │
    ├── kaggle_finetune/         Kaggle fine-tuning scripts
    │   ├── finetune_gemma4.py
    │   ├── train.py
    │   └── README.md
    │
    ├── EVAL/                    Evaluation docs
    │   └── EVAL_zeroshot.md
    │
    ├── paper/                   Paper artifacts (inside VLegal-Bench)
    │   ├── paper_tieng_viet.md  Vietnamese paper draft
    │   ├── PAPER_TRACKING.docx  Tracking doc
    │   └── legal_llm_paper_ptit.docx  (duplicate)
    │
    ├── 1.1/ ... 5.4/           19 task folders
    │   ├── {x_y}.jsonl          Benchmark dataset
    │   ├── prompt_{x_y}.py      Prompt template
    │   ├── {x_y}_llm_test_results_baseline_3.json
    │   ├── {x_y}_llm_test_results_proposed.json
    │   ├── {x_y}_llm_test_results_*_reliability.json
    │   └── {x_y}_llm_test.log  Inference logs
    │
    ├── core_metrics_results.json    Core evaluation results
    ├── reliability_results.json     Reliability metrics (baseline + proposed)
    └── reliability_results_v1_backup.json  V1 results backup
```

## Naming Conventions

- **Task folders**: `{category}.{task}/` (e.g., `1.4/`, `3.1/`)
- **Dataset files**: `{category}_{task}.jsonl` (e.g., `1_4.jsonl`)
- **Prompt files**: `prompt_{category}_{task}.py` (e.g., `prompt_1_4.py`)
- **Result files**: `{category}_{task}_llm_test_results_{mode}.json`
- **Reliability files**: `{category}_{task}_llm_test_results_{mode}_reliability.json`
- **Annotated files**: `{category}_{task}_annotated.jsonl`

## Mode Naming

- `baseline_3` — LoRA r=8, α=16, standard training
- `proposed` — LoRA r=16, α=32, enhanced prompts
- `gemma4_e4b` — Base model, few-shot (no fine-tuning)
- `raft_at_proposed` — RAFT-AT training (planned)
