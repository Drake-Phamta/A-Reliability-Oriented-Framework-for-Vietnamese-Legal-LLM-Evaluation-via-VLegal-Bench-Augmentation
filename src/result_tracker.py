import json
from pathlib import Path
from typing import Dict, List


RESULT_COLUMNS = [
    "task",
    "accuracy",
    "precision",
    "recall",
    "f1-score",
    "BLEU",
    "ROUGE",
    "Macro-F1",
]

PLACEHOLDER = "-"


def _split_markdown_row(line: str) -> List[str]:
    content = line.strip()
    if not content.startswith("|") or not content.endswith("|"):
        return []
    content = content[1:-1]

    cells = []
    current = []
    escaped = False
    for ch in content:
        if escaped:
            current.append(ch)
            escaped = False
            continue
        if ch == "\\":
            escaped = True
            continue
        if ch == "|":
            cells.append("".join(current).strip())
            current = []
            continue
        current.append(ch)
    cells.append("".join(current).strip())
    return cells


def _escape_cell(value: str) -> str:
    return value.replace("|", r"\|").replace("\n", "<br>")


def _unescape_cell(value: str) -> str:
    return value.replace(r"\|", "|").replace("<br>", "\n")


def _is_separator_row(cells: List[str]) -> bool:
    if not cells:
        return False
    for cell in cells:
        stripped = cell.replace("-", "").replace(":", "").strip()
        if stripped:
            return False
    return True


def _read_existing_rows(result_md_path: Path) -> Dict[str, Dict[str, str]]:
    if not result_md_path.exists():
        return {}

    lines = result_md_path.read_text(encoding="utf-8").splitlines()
    rows_by_task: Dict[str, Dict[str, str]] = {}
    expected_header = [c.lower() for c in RESULT_COLUMNS]
    in_table = False

    for line in lines:
        line = line.strip()
        if not line.startswith("|"):
            if in_table:
                break
            continue

        cells = _split_markdown_row(line)
        if not cells:
            continue

        if not in_table:
            header = [c.strip().lower() for c in cells]
            if header == expected_header:
                in_table = True
            continue

        if _is_separator_row(cells):
            continue

        if len(cells) < len(RESULT_COLUMNS):
            cells += [PLACEHOLDER] * (len(RESULT_COLUMNS) - len(cells))
        elif len(cells) > len(RESULT_COLUMNS):
            cells = cells[: len(RESULT_COLUMNS)]

        row = {col: _unescape_cell(cells[idx]) for idx, col in enumerate(RESULT_COLUMNS)}
        task_id = row.get("task", "").strip()
        if task_id:
            rows_by_task[task_id] = row

    return rows_by_task


def _task_sort_key(task_id: str):
    parts = task_id.split(".")
    key = []
    for part in parts:
        if part.isdigit():
            key.append((0, int(part)))
        else:
            key.append((1, part))
    return key


def _format_metric_value(value) -> str:
    if value is None:
        return PLACEHOLDER
    if isinstance(value, dict):
        return json.dumps(value, ensure_ascii=False, sort_keys=True)
    if isinstance(value, list):
        return json.dumps(value, ensure_ascii=False)
    if isinstance(value, (int, float)):
        return str(value)
    text = str(value).strip()
    return text if text else PLACEHOLDER


def upsert_task_metrics(result_md_path: str, task_id: str, metric_results: Dict) -> None:
    path = Path(result_md_path)
    rows_by_task = _read_existing_rows(path)

    if task_id in rows_by_task:
        row = rows_by_task[task_id]
    else:
        row = {col: PLACEHOLDER for col in RESULT_COLUMNS}
        row["task"] = task_id

    for metric_name, metric_value in (metric_results or {}).items():
        if metric_name not in RESULT_COLUMNS or metric_name == "task":
            continue
        row[metric_name] = _format_metric_value(metric_value)

    rows_by_task[task_id] = row
    ordered_tasks = sorted(rows_by_task.keys(), key=_task_sort_key)

    output_lines = [
        "| " + " | ".join(RESULT_COLUMNS) + " |",
        "| " + " | ".join(["---"] * len(RESULT_COLUMNS)) + " |",
    ]
    for tid in ordered_tasks:
        row = rows_by_task[tid]
        cells = [_escape_cell(str(row.get(col, PLACEHOLDER))) for col in RESULT_COLUMNS]
        output_lines.append("| " + " | ".join(cells) + " |")

    path.write_text("\n".join(output_lines) + "\n", encoding="utf-8")
