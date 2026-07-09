"""Person D's unit tests — deterministic metrics + judge parse guard."""
from evaluation.metrics import citation_f1, llm_judge, refusal_accuracy
from llm.client import BaseLLMClient


def test_citation_f1_perfect_match():
    assert citation_f1(["s.2", "s.5"], ["s.2", "s.5"])["f1"] == 1.0


def test_citation_f1_partial():
    r = citation_f1(["s.2", "s.99"], ["s.2", "s.5"])
    assert r["precision"] == 0.5 and r["recall"] == 0.5


def test_citation_f1_both_empty_is_perfect():
    assert citation_f1([], [])["f1"] == 1.0


def test_citation_f1_empty_cited_vs_nonempty_gold_is_zero():
    assert citation_f1([], ["s.2"])["f1"] == 0.0


def test_refusal_accuracy_penalises_over_refusal():
    assert refusal_accuracy("answer", "abstain") is False   # over-refusal
    assert refusal_accuracy("abstain", "abstain") is True
    assert refusal_accuracy("abstain", "grounded") is False # hallucination path
    assert refusal_accuracy("answer", "grounded") is True


class CannedLLM(BaseLLMClient):
    def __init__(self, response):
        self._response = response

    def generate(self, prompt, system="", json_mode=False):
        return self._response


def test_llm_judge_parses_score():
    llm = CannedLLM('{"score": 0.8, "reason": "mostly right"}')
    assert llm_judge(llm, "judge_relevancy", question="q", answer="a")["score"] == 0.8


def test_llm_judge_survives_unparseable_output():
    llm = CannedLLM("I am not JSON")
    result = llm_judge(llm, "judge_relevancy", question="q", answer="a")
    assert result["score"] is None
