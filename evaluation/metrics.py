"""The five metrics. Two deterministic, three LLM-judged.

Judge with a DIFFERENT model than the generator (use the fallback client's
secondary) — say why in §IV: reduces self-preference bias.
"""
import json

from llm.client import load_prompt


def citation_f1(cited: list[str], governing: list[str]) -> dict:
    """Deterministic — no LLM. Precision/recall/F1 of cited vs gold sections."""
    c, g = set(cited), set(governing)
    if not c and not g:
        return {"precision": 1.0, "recall": 1.0, "f1": 1.0}
    tp = len(c & g)
    p = tp / len(c) if c else 0.0
    r = tp / len(g) if g else 0.0
    f1 = 2 * p * r / (p + r) if (p + r) else 0.0
    return {"precision": round(p, 2), "recall": round(r, 2), "f1": round(f1, 2)}


def refusal_accuracy(expected: str, verdict: str) -> bool:
    """The metric almost no group measures. Correct when the system abstains on
    abstain-expected items AND answers on answer-expected items — so it also
    penalises over-refusal, not just hallucination."""
    return (expected == "abstain") == (verdict == "abstain")


def llm_judge(llm, kind: str, **kwargs) -> dict:
    """One judge function, three prompt files in llm/prompts/:
       judge_correctness.txt  — placeholders: question, reference, answer
       judge_faithfulness.txt — placeholders: answer, context
       judge_relevancy.txt    — placeholders: question, answer
    All return JSON with a "score" key (0.0-1.0)."""
    raw = llm.generate(load_prompt(kind, **kwargs), json_mode=True)
    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        return {"score": None, "reason": "judge output unparseable"}

# TODO(D): manual sanity layer — hand-score 5 of the 20 and report agreement
# with the judge in one §IV sentence. Big credibility win.
