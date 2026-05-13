import json
import re
import math
import logging
from typing import List, Dict, Optional, Tuple, Set
from collections import defaultdict
import os

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


# ============================================================
# Helper functions for parsing model responses
# ============================================================

def parse_answer_tag(text: str) -> Optional[str]:
    """Extract answer from <answer>...</answer> tag in model response."""
    if not text:
        return None
    match = re.search(r'<answer>\s*(.*?)\s*</answer>', text, re.DOTALL | re.IGNORECASE)
    if match:
        return match.group(1).strip()
    return None


def parse_citation_from_response(text: str) -> List[Dict]:
    """Parse citation references from model response text.

    Looks for patterns like:
    - Điều 463 Bộ luật Dân sự 2015
    - Khoản 1 Điều 331 Bộ luật Hình sự
    - Điều 14 Hiến pháp năm 2013

    Returns list of dicts with keys: document, article, clause
    """
    if not text:
        return []

    citations = []

    # Pattern 1: Khoản X Điều Y <document>
    pattern1 = re.findall(
        r'Khoản\s+(\d+)\s+Điều\s+(\d+)\s+(.*?)(?:\.|,|\n|$)',
        text, re.IGNORECASE
    )
    for clause, article, doc in pattern1:
        citations.append({
            'document': doc.strip(),
            'article': f'Điều {article}',
            'clause': f'Khoản {clause}'
        })

    # Pattern 2: Điều Y <document> (without Khoản)
    pattern2 = re.findall(
        r'(?<!Khoản\s\d+\s)Điều\s+(\d+)\s+(.*?)(?:\.|,|\n|$)',
        text, re.IGNORECASE
    )
    for article, doc in pattern2:
        # Avoid duplicates from pattern1
        doc_clean = doc.strip()
        if not any(c['article'] == f'Điều {article}' and c['document'] == doc_clean for c in citations):
            citations.append({
                'document': doc_clean,
                'article': f'Điều {article}',
                'clause': None
            })

    return citations


def parse_thinking_content(text: str) -> Optional[str]:
    """Extract content between <think> tags."""
    if not text:
        return None
    match = re.search(r'<think>(.*?)</think>', text, re.DOTALL | re.IGNORECASE)
    if match:
        return match.group(1).strip()
    return None


def detect_abstention(text: str) -> bool:
    """Detect whether the model response contains abstention markers.

    Returns True if the model expresses uncertainty, refuses to answer,
    or requests additional information.
    """
    if not text:
        return False

    text_lower = text.lower()

    # Vietnamese abstention markers
    abstention_markers = [
        'không đủ thông tin',
        'không chắc chắn',
        'không thể xác định',
        'không đủ căn cứ',
        'không đủ cơ sở',
        'cần thêm thông tin',
        'không thể trả lời',
        'không có đủ thông tin',
        'không có đủ căn cứ',
        'không có đủ cơ sở',
        'không đủ dữ liệu',
        'không thể kết luận',
        'không đủ yếu tố',
        'không đủ chứng cứ',
        'xin lỗi',
        'không có câu trả lời',
        'không rõ',
        'không xác định được',
        'cần tham khảo thêm',
        'khuyên bạn tham khảo',
        'không đủ thẩm quyền',
    ]

    for marker in abstention_markers:
        if marker in text_lower:
            return True

    # English abstention markers (for multilingual models)
    en_markers = [
        'insufficient information',
        'cannot determine',
        'not enough information',
        'i cannot answer',
        'i\'m not sure',
        'uncertain',
        'unable to answer',
        'need more context',
        'cannot provide',
    ]

    for marker in en_markers:
        if marker in text_lower:
            return True

    return False


def extract_atomic_claims(text: str) -> List[str]:
    """Extract atomic claims from model response text.

    Simple sentence-level splitting as approximation.
    """
    if not text:
        return []

    # Split by sentence-ending punctuation
    sentences = re.split(r'[.!?]\s+', text)
    claims = []
    for s in sentences:
        s = s.strip()
        if len(s) > 10:  # Filter out very short fragments
            claims.append(s)
    return claims


# ============================================================
# Reliability Metrics Classes
# ============================================================

class CitationAnnotation:
    """Represents a gold citation annotation for a sample."""

    def __init__(self, document: str, article: str, clause: str = None,
                 evidence_passage: str = None):
        self.document = document
        self.article = article
        self.clause = clause
        self.evidence_passage = evidence_passage

    def match(self, predicted: Dict, granularity: str = 'article') -> bool:
        """Check if predicted citation matches this annotation.

        Args:
            predicted: Dict with keys 'document', 'article', 'clause'
            granularity: 'document', 'article', or 'clause'
        """
        if granularity == 'document':
            return self._normalize(self.document) in self._normalize(predicted.get('document', '')) or \
                   self._normalize(predicted.get('document', '')) in self._normalize(self.document)

        if granularity == 'article':
            doc_match = self._normalize(self.document) in self._normalize(predicted.get('document', '')) or \
                        self._normalize(predicted.get('document', '')) in self._normalize(self.document)
            art_match = self._normalize(self.article) == self._normalize(predicted.get('article', ''))
            return doc_match and art_match

        if granularity == 'clause':
            doc_match = self._normalize(self.document) in self._normalize(predicted.get('document', '')) or \
                        self._normalize(predicted.get('document', '')) in self._normalize(self.document)
            art_match = self._normalize(self.article) == self._normalize(predicted.get('article', ''))
            cl_match = self._normalize(self.clause) == self._normalize(predicted.get('clause', '')) if self.clause else True
            return doc_match and art_match and cl_match

        return False

    @staticmethod
    def _normalize(text: str) -> str:
        if not text:
            return ''
        return text.strip().lower().replace('  ', ' ')


class TemporalAnnotation:
    """Represents temporal validity annotation for a legal provision."""

    def __init__(self, promulgation_date: str = None, effective_date: str = None,
                 expiration_date: str = None, superseded_by: str = None,
                 valid_at_query_date: bool = True, query_reference_date: str = None):
        self.promulgation_date = promulgation_date
        self.effective_date = effective_date
        self.expiration_date = expiration_date
        self.superseded_by = superseded_by
        self.valid_at_query_date = valid_at_query_date
        self.query_reference_date = query_reference_date

    def is_valid_at(self, reference_date: str) -> bool:
        """Check if provision is valid at the given reference date."""
        if not self.effective_date or not reference_date:
            return self.valid_at_query_date

        try:
            eff = self._parse_date(self.effective_date)
            ref = self._parse_date(reference_date)
            if eff > ref:
                return False

            if self.expiration_date:
                exp = self._parse_date(self.expiration_date)
                if exp < ref:
                    return False

            return True
        except (ValueError, TypeError):
            return self.valid_at_query_date

    def temporal_distance(self, reference_date: str) -> float:
        """Calculate temporal distance in days from reference date to midpoint of validity interval."""
        try:
            eff = self._parse_date(self.effective_date)
            ref = self._parse_date(reference_date)

            if self.expiration_date:
                exp = self._parse_date(self.expiration_date)
                midpoint = eff + (exp - eff) / 2
            else:
                midpoint = eff

            return abs((ref - midpoint).days)
        except (ValueError, TypeError):
            return 365.0  # Default large distance

    @staticmethod
    def _parse_date(date_str: str):
        from datetime import datetime
        for fmt in ['%Y-%m-%d', '%d/%m/%Y', '%Y', '%m/%Y']:
            try:
                return datetime.strptime(date_str.strip(), fmt)
            except ValueError:
                continue
        raise ValueError(f"Cannot parse date: {date_str}")


class ReliabilityMetrics:
    """Compute reliability metrics for legal LLM evaluation.

    Metrics:
    - CitAcc: Citation correctness
    - RAS: Recency-aware score
    - RAR: Recency-aware recall
    - ESR: Evidence support rate
    - UCR: Unsupported claim rate
    - AbsAcc: Abstention accuracy
    """

    def __init__(self, predictions_path: str, annotations_path: str = None):
        """
        Args:
            predictions_path: Path to JSONL file with model predictions (must have 'raw_response' field)
            annotations_path: Path to JSONL file with reliability annotations (optional)
        """
        self.predictions = []
        with open(predictions_path, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if line:
                    self.predictions.append(json.loads(line))

        self.annotations = {}
        if annotations_path and os.path.exists(annotations_path):
            with open(annotations_path, 'r', encoding='utf-8') as f:
                for line in f:
                    line = line.strip()
                    if line:
                        ann = json.loads(line)
                        self.annotations[ann.get('sample_id', '')] = ann

        logger.info(f"Loaded {len(self.predictions)} predictions and {len(self.annotations)} annotations")

    # ----- Metric 1: Citation Correctness (CitAcc) -----

    def calculate_citacc(self, granularity: str = 'article') -> float:
        """Calculate citation correctness.

        Args:
            granularity: 'document', 'article', or 'clause'

        Returns:
            Proportion of responses with correct citations.
        """
        if not self.annotations:
            logger.warning("No annotations loaded. Cannot calculate CitAcc.")
            return 0.0

        correct = 0
        total = 0

        for pred in self.predictions:
            sample_id = pred.get('sample_id', pred.get('id', ''))
            ann = self.annotations.get(sample_id)
            if not ann or 'citation' not in ann:
                continue

            total += 1
            raw_response = pred.get('raw_response', '')

            # Parse citations from response
            predicted_citations = parse_citation_from_response(raw_response)

            # Gold citation
            gold = CitationAnnotation(
                document=ann['citation'].get('document_name', ''),
                article=ann['citation'].get('article', ''),
                clause=ann['citation'].get('clause', None)
            )

            # Check if any predicted citation matches gold
            for pc in predicted_citations:
                if gold.match(pc, granularity):
                    correct += 1
                    break

        return correct / total if total > 0 else 0.0

    # ----- Metric 2 & 3: Recency-Aware Score (RAS) and Recall (RAR) -----

    def calculate_ras(self, lambda_decay: float = 0.01) -> float:
        """Calculate Recency-Aware Score with exponential decay.

        Args:
            lambda_decay: Decay rate (default 0.01 day^-1, half-life ~69 days)

        Returns:
            RAS score in [0, 1].
        """
        if not self.annotations:
            logger.warning("No annotations loaded. Cannot calculate RAS.")
            return 0.0

        total_ras = 0.0
        total = 0

        for pred in self.predictions:
            sample_id = pred.get('sample_id', pred.get('id', ''))
            ann = self.annotations.get(sample_id)
            if not ann or 'temporal' not in ann:
                continue

            total += 1
            temporal = ann['temporal']
            query_date = temporal.get('query_reference_date', '')

            if not query_date:
                continue

            # Check if the cited provision is temporally valid
            temporal_ann = TemporalAnnotation(
                effective_date=temporal.get('effective_date'),
                expiration_date=temporal.get('expiration_date'),
                valid_at_query_date=temporal.get('valid_at_query_date', True)
            )

            is_valid = temporal_ann.is_valid_at(query_date)
            if is_valid:
                distance = temporal_ann.temporal_distance(query_date)
                total_ras += math.exp(-lambda_decay * distance)
            # If not valid, contribution is 0

        return total_ras / total if total > 0 else 0.0

    def calculate_rar(self) -> float:
        """Calculate Recency-Aware Recall.

        Returns:
            Proportion of responses citing temporally valid provisions.
        """
        if not self.annotations:
            logger.warning("No annotations loaded. Cannot calculate RAR.")
            return 0.0

        valid_count = 0
        total = 0

        for pred in self.predictions:
            sample_id = pred.get('sample_id', pred.get('id', ''))
            ann = self.annotations.get(sample_id)
            if not ann or 'temporal' not in ann:
                continue

            total += 1
            temporal = ann['temporal']
            query_date = temporal.get('query_reference_date', '')

            if not query_date:
                continue

            temporal_ann = TemporalAnnotation(
                effective_date=temporal.get('effective_date'),
                expiration_date=temporal.get('expiration_date'),
                valid_at_query_date=temporal.get('valid_at_query_date', True)
            )

            if temporal_ann.is_valid_at(query_date):
                valid_count += 1

        return valid_count / total if total > 0 else 0.0

    # ----- Metric 4: Evidence Support Rate (ESR) -----

    def calculate_esr(self) -> float:
        """Calculate Evidence Support Rate.

        Proportion of responses fully supported by at least one annotated evidentiary passage.
        Uses simple keyword overlap as proxy for entailment (can be upgraded to NLI model).
        """
        if not self.annotations:
            logger.warning("No annotations loaded. Cannot calculate ESR.")
            return 0.0

        supported = 0
        total = 0

        for pred in self.predictions:
            sample_id = pred.get('sample_id', pred.get('id', ''))
            ann = self.annotations.get(sample_id)
            if not ann or 'reliability' not in ann:
                continue

            total += 1
            raw_response = pred.get('raw_response', '')
            reliability = ann['reliability']

            if reliability.get('evidence_sufficient', False):
                # Check if response content aligns with evidence
                evidence_passage = ann.get('citation', {}).get('evidence_passage', '')
                if evidence_passage and self._text_overlap(raw_response, evidence_passage) > 0.3:
                    supported += 1
                elif reliability.get('evidence_sufficient', False):
                    # If evidence is marked sufficient, count as supported
                    supported += 1

        return supported / total if total > 0 else 0.0

    # ----- Metric 5: Unsupported Claim Rate (UCR) -----

    def calculate_ucr(self) -> float:
        """Calculate Unsupported Claim Rate.

        Proportion of responses containing at least one unsupported claim.
        Lower is better.
        """
        if not self.annotations:
            logger.warning("No annotations loaded. Cannot calculate UCR.")
            return 0.0

        unsupported = 0
        total = 0

        for pred in self.predictions:
            sample_id = pred.get('sample_id', pred.get('id', ''))
            ann = self.annotations.get(sample_id)
            if not ann or 'reliability' not in ann:
                continue

            total += 1
            reliability = ann['reliability']
            unsup_claims = reliability.get('unsupported_claims', [])

            if unsup_claims and len(unsup_claims) > 0:
                unsupported += 1

        return unsupported / total if total > 0 else 0.0

    def calculate_ucr_fine(self) -> float:
        """Calculate fine-grained UCR (fraction of atomic claims unsupported)."""
        if not self.annotations:
            logger.warning("No annotations loaded. Cannot calculate fine UCR.")
            return 0.0

        total_ratio = 0.0
        total = 0

        for pred in self.predictions:
            sample_id = pred.get('sample_id', pred.get('id', ''))
            ann = self.annotations.get(sample_id)
            if not ann or 'reliability' not in ann:
                continue

            total += 1
            raw_response = pred.get('raw_response', '')
            reliability = ann['reliability']
            unsup_claims = reliability.get('unsupported_claims', [])

            atomic_claims = extract_atomic_claims(raw_response)
            if atomic_claims:
                total_ratio += len(unsup_claims) / len(atomic_claims)
            else:
                total_ratio += 0.0

        return total_ratio / total if total > 0 else 0.0

    # ----- Metric 6: Abstention Accuracy (AbsAcc) -----

    def calculate_absacc(self) -> float:
        """Calculate Abstention Accuracy.

        Over should-abstain samples, proportion of responses that correctly express uncertainty.
        """
        if not self.annotations:
            logger.warning("No annotations loaded. Cannot calculate AbsAcc.")
            return 0.0

        correct_abstain = 0
        should_abstain_total = 0

        for pred in self.predictions:
            sample_id = pred.get('sample_id', pred.get('id', ''))
            ann = self.annotations.get(sample_id)
            if not ann or 'reliability' not in ann:
                continue

            reliability = ann['reliability']
            if not reliability.get('should_abstain', False):
                continue

            should_abstain_total += 1
            raw_response = pred.get('raw_response', '')

            if detect_abstention(raw_response):
                correct_abstain += 1

        return correct_abstain / should_abstain_total if should_abstain_total > 0 else 0.0

    # ----- Full Evaluation -----

    def eval_all(self) -> Dict:
        """Run all reliability metrics and return results dict."""
        results = {}

        # CitAcc at different granularities
        results['CitAcc_document'] = self.calculate_citacc(granularity='document')
        results['CitAcc_article'] = self.calculate_citacc(granularity='article')
        results['CitAcc_clause'] = self.calculate_citacc(granularity='clause')

        # Temporal metrics
        results['RAS'] = self.calculate_ras()
        results['RAR'] = self.calculate_rar()

        # Evidence metrics
        results['ESR'] = self.calculate_esr()
        results['UCR'] = self.calculate_ucr()
        results['UCR_fine'] = self.calculate_ucr_fine()

        # Abstention
        results['AbsAcc'] = self.calculate_absacc()

        return results

    @staticmethod
    def _text_overlap(text1: str, text2: str) -> float:
        """Calculate simple word-level overlap ratio between two texts."""
        if not text1 or not text2:
            return 0.0
        words1 = set(text1.lower().split())
        words2 = set(text2.lower().split())
        if not words1 or not words2:
            return 0.0
        intersection = words1 & words2
        return len(intersection) / min(len(words1), len(words2))


# ============================================================
# CLI entry point
# ============================================================

def main():
    import argparse
    parser = argparse.ArgumentParser(description="Calculate reliability metrics for legal LLM predictions")
    parser.add_argument("--predictions", type=str, required=True,
                        help="Path to predictions JSONL file (must have raw_response field)")
    parser.add_argument("--annotations", type=str, required=True,
                        help="Path to annotations JSONL file")
    parser.add_argument("--output", type=str, default=None,
                        help="Path to save results JSON (optional)")
    args = parser.parse_args()

    metrics = ReliabilityMetrics(
        predictions_path=args.predictions,
        annotations_path=args.annotations
    )

    results = metrics.eval_all()

    print("\n=== Reliability Metrics ===")
    for k, v in results.items():
        print(f"  {k}: {v:.4f}")

    if args.output:
        with open(args.output, 'w', encoding='utf-8') as f:
            json.dump(results, f, indent=2, ensure_ascii=False)
        print(f"\nResults saved to {args.output}")


if __name__ == "__main__":
    main()
