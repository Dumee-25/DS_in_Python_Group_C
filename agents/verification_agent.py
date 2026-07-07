"""Verification specialist: the reflection pass and hallucination guard.

Two layers, cheapest first:
1. Deterministic fabricated-citation check — any cited section that was never
   actually retrieved fails the draft immediately, no LLM call spent.
2. LLM-judge claim-level grounding check (llm/prompts/verification.txt).

Ungrounded → 'retry' (orchestrator re-retrieves) or 'abstain' once Person B's
loop exhausts the retry budget.
"""
import json

from agents.base import BaseAgent
from agents.synthesis_agent import _strip_code_fences
from llm.client import BaseLLMClient, load_prompt
from shared.contracts import AgentState


class VerificationAgent(BaseAgent):
    name = "verification"

    def __init__(self, llm: BaseLLMClient):
        self._llm = llm

    def _execute(self, state: AgentState) -> AgentState:
        retrieved_keys = {c.section for c in state.retrieved}
        fabricated = [s for s in state.cited_sections if s not in retrieved_keys]
        if fabricated:
            state.trace.append({"agent": self.name,
                                "fabricated_citations": fabricated})
            state.verdict = "retry"
            return state

        context = "\n".join(f"[{c.section}] {c.text}" for c in state.retrieved)
        raw = self._llm.generate(
            load_prompt("verification", answer=state.draft, context=context),
            json_mode=True)
        try:
            result = json.loads(_strip_code_fences(raw))
            state.verdict = "grounded" if result["all_supported"] else "retry"
        except (json.JSONDecodeError, KeyError, TypeError):
            state.verdict = "retry"
            state.trace.append({"agent": self.name, "error": "malformed_llm_output"})
        return state
