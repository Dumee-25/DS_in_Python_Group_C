"""Synthesis agent must survive malformed LLM output and honour the escape hatch."""
import json

from agents.synthesis_agent import SynthesisAgent
from llm.client import BaseLLMClient
from shared.contracts import AgentState, Chunk


class CannedLLM(BaseLLMClient):
    def __init__(self, response):
        self._response = response
        self.last_prompt = None

    def generate(self, prompt, system="", json_mode=False):
        self.last_prompt = prompt
        return self._response


def _state():
    chunk = Chunk(text="A data controller determines purposes and means.",
                  source_doc="pdpa_act_9_2022.pdf", section="s.2",
                  collection="statute", snapshot_date="2026-01-01", in_force=True)
    return AgentState(query="What is a data controller?", retrieved=[chunk])


def test_valid_json_sets_draft_and_citations():
    llm = CannedLLM(json.dumps(
        {"answer": "A controller decides purposes [s.2].", "cited_sections": ["s.2"]}))
    state = SynthesisAgent(llm).run(_state())
    assert state.draft == "A controller decides purposes [s.2]."
    assert state.cited_sections == ["s.2"]
    assert state.verdict == ""


def test_malformed_json_does_not_crash_and_flags_retry():
    state = SynthesisAgent(CannedLLM("this is not JSON {")).run(_state())
    assert state.draft == ""
    assert state.verdict == "retry"


def test_missing_answer_key_flags_retry():
    state = SynthesisAgent(CannedLLM('{"cited_sections": []}')).run(_state())
    assert state.verdict == "retry"


def test_insufficient_context_flags_retry():
    llm = CannedLLM(json.dumps(
        {"answer": "INSUFFICIENT_CONTEXT", "cited_sections": []}))
    state = SynthesisAgent(llm).run(_state())
    assert state.verdict == "retry"


def test_code_fenced_json_is_tolerated():
    fenced = "```json\n" + json.dumps(
        {"answer": "ok [s.2]", "cited_sections": ["s.2"]}) + "\n```"
    state = SynthesisAgent(CannedLLM(fenced)).run(_state())
    assert state.draft == "ok [s.2]"


def test_retrieved_chunks_reach_the_prompt():
    llm = CannedLLM(json.dumps({"answer": "x", "cited_sections": []}))
    SynthesisAgent(llm).run(_state())
    assert "[s.2]" in llm.last_prompt
    assert "What is a data controller?" in llm.last_prompt
