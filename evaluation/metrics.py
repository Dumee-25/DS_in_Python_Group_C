"""The five metrics. Two deterministic, three LLM-judged.

Judge with a DIFFERENT model than the generator (use the fallback client's
secondary) — say why in §IV: reduces self-preference bias.
"""
import json
import re

from llm.client import load_prompt

_BARE_SECTION_RE = re.compile(r"s\.\d+")


def _bare_section(key: str) -> str:
    """'s.38(7)' -> 's.38': gold governing_sections are bare, so a
    subsection-precise citation must count as a hit, not a miss."""
    m = _BARE_SECTION_RE.match(str(key))
    return m.group(0) if m else str(key)


def citation_f1(cited: list[str], governing: list[str]) -> dict:
    """Deterministic — no LLM. Precision/recall/F1 of cited vs gold sections,
    compared at section level (subsections stripped)."""
    c = {_bare_section(x) for x in cited}
    g = {_bare_section(x) for x in governing}
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

# TODO: manual sanity layer — hand-score 5 of the 20 and report agreement
# with the judge in one §IV sentence. Big credibility win.
