import pathlib
import sys
import types
import unittest


ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

# Provide minimal stubs so we can import evaluation.py without full runtime deps.
if "rouge_score" not in sys.modules:
    rouge_score_mod = types.ModuleType("rouge_score")
    rouge_scorer_mod = types.ModuleType("rouge_scorer")
    rouge_score_mod.rouge_scorer = rouge_scorer_mod
    sys.modules["rouge_score"] = rouge_score_mod
    sys.modules["rouge_score.rouge_scorer"] = rouge_scorer_mod

if "nltk.translate.bleu_score" not in sys.modules:
    nltk_mod = types.ModuleType("nltk")
    translate_mod = types.ModuleType("nltk.translate")
    bleu_mod = types.ModuleType("nltk.translate.bleu_score")

    def sentence_bleu(*args, **kwargs):
        return 0.0

    class SmoothingFunction:
        pass

    bleu_mod.sentence_bleu = sentence_bleu
    bleu_mod.SmoothingFunction = SmoothingFunction
    translate_mod.bleu_score = bleu_mod
    nltk_mod.translate = translate_mod
    sys.modules["nltk"] = nltk_mod
    sys.modules["nltk.translate"] = translate_mod
    sys.modules["nltk.translate.bleu_score"] = bleu_mod

if "openai" not in sys.modules:
    openai_mod = types.ModuleType("openai")

    class OpenAI:
        pass

    openai_mod.OpenAI = OpenAI
    sys.modules["openai"] = openai_mod

from evaluation import parse_single_choice_strict


class TestStrictSingleChoiceParser(unittest.TestCase):
    def setUp(self):
        self.labels_abcd = {"A", "B", "C", "D"}
        self.labels_abcdef = {"A", "B", "C", "D", "E", "F"}

    def test_thinking_process_with_choice_list_returns_none(self):
        text = "Thinking Process:\n1) The output must be one letter (A, B, C, or D)."
        self.assertIsNone(parse_single_choice_strict(text, self.labels_abcd))

    def test_output_tag_returns_label(self):
        self.assertEqual(
            parse_single_choice_strict("<output>C</output>", self.labels_abcd), "C"
        )

    def test_answer_tag_supports_a_to_f(self):
        self.assertEqual(
            parse_single_choice_strict("<answer>E</answer>", self.labels_abcdef), "E"
        )

    def test_last_non_empty_line_returns_label(self):
        text = "Reasoning goes here.\nC"
        self.assertEqual(parse_single_choice_strict(text, self.labels_abcd), "C")

    def test_declare_answer_sentence_is_non_compliant(self):
        text = "Đáp án là C"
        self.assertIsNone(parse_single_choice_strict(text, self.labels_abcd))

    def test_abbreviation_does_not_leak_label(self):
        text = "Các nạn nhân gồm N.B.A và N.T.M trong vụ việc."
        self.assertIsNone(parse_single_choice_strict(text, self.labels_abcd))

    def test_markdown_wrapper_on_last_line_is_supported(self):
        text = "Suy luận...\n**A**"
        self.assertEqual(parse_single_choice_strict(text, self.labels_abcd), "A")


if __name__ == "__main__":
    unittest.main()
