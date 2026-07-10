"""Verifier must catch fabricated citations before spending an LLM call,
then defer to the LLM judge for claim-level grounding."""
import json

from agents.verification_agent import VerificationAgent
from llm.client import BaseLLMClient
from shared.contracts import AgentState, Chunk


class CannedLLM(BaseLLMClient):
    def __init__(self, response):
        self._response = response
        self.calls = 0

    def generate(self, prompt, system="", json_mode=False):
        self.calls += 1
        return self._response


def _state(cited):
    chunk = Chunk(text="text", source_doc="doc.pdf", section="s.2",
                  collection="statute", snapshot_date="2026-01-01", in_force=True)
    return AgentState(query="q", draft="draft [s.2]", retrieved=[chunk],
                      cited_sections=cited)


def test_fabricated_citation_fails_without_llm_call():
    llm = CannedLLM("should never be used")
    state = VerificationAgent(llm).run(_state(cited=["s.2", "s.99"]))
    assert state.verdict == "retry"
    assert llm.calls == 0
    assert any("s.99" in t.get("fabricated_citations", []) for t in state.trace)


def test_grounded_answer_passes():
    llm = CannedLLM(json.dumps({"claims": [], "all_supported": True}))
    state = VerificationAgent(llm).run(_state(cited=["s.2"]))
    assert state.verdict == "grounded"
    assert llm.calls == 1


def test_unsupported_claims_flag_retry():
    llm = CannedLLM(json.dumps({"claims": [], "all_supported": False}))
    state = VerificationAgent(llm).run(_state(cited=["s.2"]))
    assert state.verdict == "retry"


def test_malformed_judge_output_flags_retry():
    llm = CannedLLM("not json at all")
    state = VerificationAgent(llm).run(_state(cited=["s.2"]))
    assert state.verdict == "retry"


def test_subsection_citations_of_retrieved_sections_are_not_fabricated():
    """Chunk labels are bare 's.N'; a draft citing 's.2(3)' is more precise
    than the label, not fabricated — it must reach the LLM judge."""
    llm = CannedLLM(json.dumps({"all_supported": True}))
    state = VerificationAgent(llm).run(_state(cited=["s.2(3)", "s.2"]))
    assert state.verdict == "grounded"
    assert llm.calls == 1
