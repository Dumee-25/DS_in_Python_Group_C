"""Synthesis specialist: grounded draft with structured [s.X] citations.

The prompt (llm/prompts/synthesis.txt) is the craft here; the code is small.
"""
import json
import re

from agents.base import BaseAgent
from llm.client import BaseLLMClient, load_prompt
from shared.contracts import AgentState

_SECTION_KEY_RE = re.compile(r"s\.\d+(?:\(\d+\))?")


def _strip_code_fences(raw: str) -> str:
    """Some vendors wrap JSON in ```json fences despite json_mode."""
    raw = raw.strip()
    if raw.startswith("```"):
        raw = raw.split("\n", 1)[-1]
        raw = raw.rsplit("```", 1)[0]
    return raw.strip()


def _normalise_citation(key) -> str:
    """'s.14 (pdpa_act_9_2022.pdf)' / '[s.14]' -> 's.14'.

    Models copy the context line format ('[s.X] (doc.pdf) ...') into their
    cited_sections; the verifier compares keys against bare Chunk.section
    values, so decoration here reads as a fabricated citation and burns a
    retry on a perfectly grounded draft.
    """
    m = _SECTION_KEY_RE.search(str(key))
    return m.group(0) if m else str(key)


class SynthesisAgent(BaseAgent):
    name = "synthesis"

    def __init__(self, llm: BaseLLMClient):
        self._llm = llm

    def _execute(self, state: AgentState) -> AgentState:
        context = "\n\n".join(
            f"[{c.section}] ({c.source_doc}) {c.text}" for c in state.retrieved)
        raw = self._llm.generate(
            load_prompt("synthesis", question=state.query, context=context),
            json_mode=True)
        try:
            data = json.loads(_strip_code_fences(raw))
            state.draft = data["answer"]
            cited = [_normalise_citation(k) for k in data.get("cited_sections", [])]
            state.cited_sections = list(dict.fromkeys(cited))   # dedupe, keep order
        except (json.JSONDecodeError, KeyError, TypeError):
            state.draft, state.verdict = "", "retry"     # malformed output → loop handles it
            state.trace.append({"agent": self.name, "error": "malformed_llm_output"})
            return state
        if state.draft.strip() == "INSUFFICIENT_CONTEXT":
            state.verdict = "retry"
        return state
