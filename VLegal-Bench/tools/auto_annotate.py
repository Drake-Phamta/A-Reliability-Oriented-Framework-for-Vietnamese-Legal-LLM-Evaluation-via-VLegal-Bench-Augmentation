#!/usr/bin/env python3
"""
Auto-Annotation Pipeline for VLegal-Bench Reliability Labels

Bước 1: Regex extract citation từ câu hỏi
Bước 2: Crawl thuvienphapluat.vn lấy metadata temporal
Bước 3: Output intermediate JSONL cho LLM assessment (Colab)

Usage:
    python tools/auto_annotate.py --task 1.4
    python tools/auto_annotate.py --task all
    python tools/auto_annotate.py --task 1.4 --skip-crawl
"""

import json
import os
import re
import sys
import time
import argparse
from datetime import datetime
from urllib.parse import quote

if sys.platform == "win32":
    sys.stdout.reconfigure(encoding='utf-8')

try:
    import requests
    from bs4 import BeautifulSoup
    HAS_DEPS = True
except ImportError:
    HAS_DEPS = False

# ============================================================
# REGEX PATTERNS
# ============================================================

# Document name patterns
DOC_PATTERNS = [
    # Luật
    r'(Luật\s+(?:số\s+)?[\d/]+(?:/QH\d+)?(?:\s+[\w\s,]+?)?(?:\s+\d{4})?)',
    r'(Luật\s+[\w\s]+?\d{4})',
    # Nghị định
    r'(Nghị\s+định\s+(?:số\s+)?[\d/]+(?:/NĐ-CP|/HĐBT|/CP))',
    # Thông tư
    r'(Thông\s+tư\s+(?:số\s+)?[\d/]+(?:/TT-[A-Z]+|/UB-LXT))',
    # Quyết định
    r'(Quyết\s+định\s+(?:số\s+)?[\d/]+(?:/QĐ-[A-Z]+|/QĐ-TTg))',
    # Pháp lệnh
    r'(Pháp\s+lệnh\s+(?:số\s+)?[\d/]+(?:/PL-UBTVQH\d+)?)',
    # Nghị quyết
    r'(Nghị\s+quyết\s+(?:số\s+)?[\d/]+(?:/NQ-[A-Z]+|/NQ-CP)?)',
    # Văn bản hợp nhất
    r'(Văn\s+bản\s+hợp\s+nhất\s+[\d/]+(?:/VBHN-[A-Z]+)?)',
    # Công văn
    r'(Công\s+văn\s+(?:số\s+)?[\d/]+(?:/CV-[A-Z]+)?)',
    # Bộ luật
    r'(Bộ\s+luật\s+[\w\s]+?\d{4})',
]

# Article/Clause patterns
ARTICLE_PATTERN = r'(?:Điều|Dieu)\s+(\d+)'
CLAUSE_PATTERN = r'(?:Khoản|Khoan)\s+(\d+)'
POINT_PATTERN = r'(?:Điểm|Diem)\s+([a-zđ])'

# Task-specific patterns
TASK_PATTERNS = {
    '1.4': {
        'focus': 'article_recall',
        'description': 'Câu hỏi hỏi về điều luật cụ thể',
        'extract_from': 'question',
    },
    '1.5': {
        'focus': 'schema_recall',
        'description': 'Câu hỏi hỏi về văn bản thuộc lĩnh vực nào',
        'extract_from': 'question',
    },
    '3.1': {
        'focus': 'clause_prediction',
        'description': 'Câu hỏi hỏi về khoản cụ thể trong điều luật',
        'extract_from': 'question',
    },
    '3.3': {
        'focus': 'multi_hop',
        'description': 'Câu hỏi yêu cầu suy luận nhiều bước',
        'extract_from': 'question',
    },
    '4.1': {
        'focus': 'summarization',
        'description': 'Câu hỏi yêu cầu tóm tắt văn bản pháp luật',
        'extract_from': 'content',
    },
    '4.2': {
        'focus': 'judicial_reasoning',
        'description': 'Câu hỏi yêu cầu phân tích pháp lý IRAC',
        'extract_from': 'description',
    },
}


# ============================================================
# STEP 1: REGEX EXTRACT
# ============================================================

def extract_document_name(text: str) -> list:
    """Extract legal document names from text."""
    found = []
    for pattern in DOC_PATTERNS:
        matches = re.findall(pattern, text, re.IGNORECASE)
        for m in matches:
            cleaned = m.strip()
            if len(cleaned) > 10 and cleaned not in found:
                found.append(cleaned)
    return found


def extract_article(text: str) -> list:
    """Extract article numbers from text."""
    matches = re.findall(ARTICLE_PATTERN, text, re.IGNORECASE)
    return [f"Điều {m}" for m in matches]


def extract_clause(text: str) -> list:
    """Extract clause numbers from text."""
    matches = re.findall(CLAUSE_PATTERN, text, re.IGNORECASE)
    return [f"Khoản {m}" for m in matches]


def extract_point(text: str) -> list:
    """Extract point letters from text."""
    matches = re.findall(POINT_PATTERN, text, re.IGNORECASE)
    return [f"Điểm {m}" for m in matches]


def extract_citation_from_sample(item: dict, task: str) -> dict:
    """Extract citation info from a sample using regex."""
    # Determine which field to extract from
    task_info = TASK_PATTERNS.get(task, {})
    extract_field = task_info.get('extract_from', 'question')

    text_fields = ['question', 'instruction', 'content', 'description', 'article']
    texts_to_search = []

    # Primary field
    primary = item.get(extract_field, '')
    if primary:
        texts_to_search.append(primary)

    # Also search in question for all tasks
    if extract_field != 'question':
        q = item.get('question', '')
        if q:
            texts_to_search.append(q)

    full_text = ' '.join(texts_to_search)

    # Extract
    docs = extract_document_name(full_text)
    articles = extract_article(full_text)
    clauses = extract_clause(full_text)
    points = extract_point(full_text)

    citation = {
        'document_names': docs,
        'primary_document': docs[0] if docs else None,
        'articles': articles,
        'primary_article': articles[0] if articles else None,
        'clauses': clauses,
        'primary_clause': clauses[0] if clauses else None,
        'points': points,
        'extraction_confidence': 'high' if docs and articles else ('medium' if docs else 'low'),
    }

    return citation


# ============================================================
# STEP 2: CRAWL thuvienphapluat.vn
# ============================================================

SEARCH_URL = "https://thuvienphapluat.vn/page/tim-van-ban.aspx"
HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
    'Accept': 'text/html,application/xhtml+xml',
    'Accept-Language': 'vi-VN,vi;q=0.9',
}

# Cache to avoid re-searching
_cache = {}


def search_document(doc_name: str) -> dict:
    """Search thuvienphapluat.vn for a document and extract metadata."""
    if not HAS_DEPS:
        return {'error': 'requests/bs4 not installed'}

    if doc_name in _cache:
        return _cache[doc_name]

    result = {
        'document_name': doc_name,
        'url': None,
        'promulgation_date': None,
        'effective_date': None,
        'status': None,
        'issuing_body': None,
        'found': False,
    }

    try:
        params = {
            'keyword': doc_name,
            'match': 'True',
            'area': '0',
        }
        resp = requests.get(SEARCH_URL, params=params, headers=HEADERS, timeout=15)

        if resp.status_code != 200:
            result['error'] = f'HTTP {resp.status_code}'
            _cache[doc_name] = result
            return result

        soup = BeautifulSoup(resp.text, 'html.parser')

        # Find first search result link
        result_link = None
        for a in soup.find_all('a', href=True):
            href = a['href']
            if '/van-ban/' in href and href.endswith('.aspx'):
                result_link = href
                break

        if not result_link:
            result['error'] = 'No results found'
            _cache[doc_name] = result
            return result

        # Make absolute URL
        if not result_link.startswith('http'):
            result_link = 'https://thuvienphapluat.vn' + result_link

        result['url'] = result_link
        result['found'] = True

        # Fetch document page for metadata
        doc_resp = requests.get(result_link, headers=HEADERS, timeout=15)
        if doc_resp.status_code == 200:
            doc_soup = BeautifulSoup(doc_resp.text, 'html.parser')
            page_text = doc_soup.get_text()

            # Extract dates
            date_patterns = [
                (r'Ngày\s+ban\s+hành[:\s]+(\d{1,2}/\d{1,2}/\d{4})', 'promulgation_date'),
                (r'Ngày\s+(\d{1,2}/\d{1,2}/\d{4})', 'promulgation_date'),
                (r'Hiệu\s+lực[:\s]+(\d{1,2}/\d{1,2}/\d{4})', 'effective_date'),
                (r'Có\s+hiệu\s+lực\s+từ[:\s]+(\d{1,2}/\d{1,2}/\d{4})', 'effective_date'),
            ]

            for pattern, field in date_patterns:
                match = re.search(pattern, page_text, re.IGNORECASE)
                if match and not result[field]:
                    result[field] = match.group(1)

            # Extract status
            status_patterns = [
                r'(Còn\s+hiệu\s+lực)',
                r'(Hết\s+hiệu\s+lực)',
                r'(Bị\s+thay\s+thế)',
                r'(Đã\s+bãi\s+bỏ)',
            ]
            for pattern in status_patterns:
                match = re.search(pattern, page_text, re.IGNORECASE)
                if match:
                    result['status'] = match.group(1)
                    break

            # Extract issuing body
            ib_patterns = [
                r'Cơ\s+quan\s+ban\s+hành[:\s]+([^\n]+)',
                r'(Bộ\s+[\w\s]+?)(?:\s+ban\s+hành|\s+Ngày)',
                r'(Ủy\s+ban\s+[\w\s]+?)(?:\s+ban\s+hành)',
            ]
            for pattern in ib_patterns:
                match = re.search(pattern, page_text, re.IGNORECASE)
                if match:
                    result['issuing_body'] = match.group(1).strip()
                    break

    except Exception as e:
        result['error'] = str(e)

    _cache[doc_name] = result
    return result


# ============================================================
# STEP 3: PREPARE FOR LLM ASSESSMENT
# ============================================================

def prepare_llm_input(item: dict, citation: dict, temporal: dict, task: str) -> dict:
    """Prepare intermediate data for LLM reliability assessment."""
    question = item.get('question', item.get('description', ''))
    instruction = item.get('instruction', '')
    ground_truth = item.get('ground_truth', item.get('answer', ''))
    content = item.get('content', '')
    answers = item.get('answers', '')

    # Build context for LLM
    llm_input = {
        'sample_id': item.get('sample_id', ''),
        'task': task,
        'task_type': TASK_PATTERNS.get(task, {}).get('focus', 'unknown'),
        'question': question,
        'instruction': instruction,
        'ground_truth': ground_truth,
        'answers': answers,
        'content': content[:2000] if content else '',  # Limit length
        'extracted_citation': citation,
        'extracted_temporal': temporal,
    }

    return llm_input


# ============================================================
# MAIN PIPELINE
# ============================================================

TASK_FILES = {
    '1.4': '1.4/1_4.jsonl',
    '1.5': '1.5/1_5.jsonl',
    '3.1': '3.1/3_1.jsonl',
    '3.3': '3.3/3_3.jsonl',
    '4.1': '4.1/4_1.jsonl',
    '4.2': '4.2/4_2.jsonl',
}


def load_jsonl(path: str) -> list:
    data = []
    with open(path, 'r', encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            if line:
                data.append(json.loads(line))
    return data


def process_task(task: str, skip_crawl: bool = False, crawl_delay: float = 2.0) -> dict:
    """Process a single task through the pipeline."""
    filepath = TASK_FILES.get(task)
    if not filepath or not os.path.exists(filepath):
        return {'error': f'Task file not found: {filepath}'}

    data = load_jsonl(filepath)
    print(f"\n{'='*60}")
    print(f"Task {task}: {len(data)} samples")
    print(f"{'='*60}")

    results = []
    stats = {
        'total': len(data),
        'citation_extracted': 0,
        'citation_failed': 0,
        'crawl_success': 0,
        'crawl_failed': 0,
        'crawl_skipped': 0,
    }

    for idx, item in enumerate(data):
        sample_id = item.get('sample_id', f'{task}_{idx:04d}')

        # Step 1: Regex extract
        citation = extract_citation_from_sample(item, task)

        if citation['primary_document']:
            stats['citation_extracted'] += 1
        else:
            stats['citation_failed'] += 1

        # Step 2: Crawl temporal metadata
        temporal = {
            'promulgation_date': None,
            'effective_date': None,
            'expiration_date': None,
            'status': None,
            'source': None,
        }

        if not skip_crawl and citation['primary_document']:
            doc_meta = search_document(citation['primary_document'])
            if doc_meta.get('found'):
                temporal['promulgation_date'] = doc_meta.get('promulgation_date')
                temporal['effective_date'] = doc_meta.get('effective_date')
                temporal['status'] = doc_meta.get('status')
                temporal['source'] = doc_meta.get('url')
                stats['crawl_success'] += 1
            else:
                stats['crawl_failed'] += 1
            time.sleep(crawl_delay)  # Rate limiting
        else:
            stats['crawl_skipped'] += 1

        # Step 3: Prepare LLM input
        llm_input = prepare_llm_input(item, citation, temporal, task)

        result = {
            'sample_id': sample_id,
            'task': task,
            'citation_extracted': citation,
            'temporal_extracted': temporal,
            'llm_input': llm_input,
        }
        results.append(result)

        # Progress
        if (idx + 1) % 50 == 0 or idx == len(data) - 1:
            print(f"  [{idx+1}/{len(data)}] citation: {stats['citation_extracted']}, "
                  f"crawl: {stats['crawl_success']}/{stats['crawl_success']+stats['crawl_failed']}")

    return {
        'task': task,
        'stats': stats,
        'results': results,
    }


def save_intermediate(results: dict, output_dir: str):
    """Save intermediate results for Colab LLM assessment."""
    task = results['task']
    os.makedirs(output_dir, exist_ok=True)

    # Save full results
    output_path = os.path.join(output_dir, f'{task.replace(".", "_")}_extracted.jsonl')
    with open(output_path, 'w', encoding='utf-8') as f:
        for r in results['results']:
            f.write(json.dumps(r, ensure_ascii=False) + '\n')

    # Save LLM input only (lighter, for Colab)
    llm_path = os.path.join(output_dir, f'{task.replace(".", "_")}_llm_input.jsonl')
    with open(llm_path, 'w', encoding='utf-8') as f:
        for r in results['results']:
            f.write(json.dumps(r['llm_input'], ensure_ascii=False) + '\n')

    # Save stats
    stats_path = os.path.join(output_dir, f'{task.replace(".", "_")}_stats.json')
    with open(stats_path, 'w', encoding='utf-8') as f:
        json.dump(results['stats'], f, ensure_ascii=False, indent=2)

    print(f"\n  Saved: {output_path}")
    print(f"  Saved: {llm_path}")
    print(f"  Saved: {stats_path}")


def main():
    parser = argparse.ArgumentParser(description="Auto-Annotation Pipeline")
    parser.add_argument("--task", type=str, required=True,
                        choices=['1.4', '1.5', '3.1', '3.3', '4.1', '4.2', 'all'],
                        help="Task to process")
    parser.add_argument("--output", type=str, default="annotations/auto_extracted",
                        help="Output directory for intermediate results")
    parser.add_argument("--skip-crawl", action="store_true",
                        help="Skip crawling thuvienphapluat.vn")
    parser.add_argument("--crawl-delay", type=float, default=2.0,
                        help="Delay between crawl requests (seconds)")
    args = parser.parse_args()

    tasks = list(TASK_FILES.keys()) if args.task == 'all' else [args.task]

    print(f"Auto-Annotation Pipeline")
    print(f"Tasks: {tasks}")
    print(f"Output: {args.output}")
    print(f"Crawl: {'disabled' if args.skip_crawl else f'enabled (delay={args.crawl_delay}s)'}")
    print(f"Started: {datetime.now().isoformat()}")

    all_stats = {}
    for task in tasks:
        results = process_task(task, skip_crawl=args.skip_crawl, crawl_delay=args.crawl_delay)
        if 'error' in results:
            print(f"  ERROR: {results['error']}")
            continue
        save_intermediate(results, args.output)
        all_stats[task] = results['stats']

    # Summary
    print(f"\n{'='*60}")
    print("SUMMARY")
    print(f"{'='*60}")
    for task, stats in all_stats.items():
        print(f"Task {task}: {stats['total']} samples, "
              f"citation: {stats['citation_extracted']}/{stats['total']}, "
              f"crawl: {stats['crawl_success']}/{stats['crawl_success']+stats['crawl_failed']}")

    print(f"\nNext: Upload {args.output}/*.jsonl to Colab for LLM assessment")
    print(f"Finished: {datetime.now().isoformat()}")


if __name__ == "__main__":
    main()
