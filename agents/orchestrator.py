import json

from agents.base import BaseAgent
from shared.contracts import AgentState

INTENTS = ["definition", "right", "obligation", "penalty", "scenario", "out_of_scope"]

_KEYWORDS = [   # fallback classifier: first match wins. Topic keywords
    # (penalty/right/obligation) outrank question-form keywords ("what is"),
    # so "What is the penalty for X?" routes to penalty, not definition.
    ("out_of_scope", ("should i", "can i sue", "sue ", "legal advice",
                      "my case", "will i win")),
    ("penalty", ("penalt", "fine", "offence", "offense", "punish", "sanction")),
    ("right", ("right", "access my", "erasure", "rectif", "withdraw consent",
               "data subject")),
    ("obligation", ("obligat", "must ", "duty", "duties", "comply", "required to",
                    "shall ")),
    ("definition", ("what is", "what does", "what are", "define", "meaning of",
                    "definition")),
]


class Orchestrator(BaseAgent):
    name = "orchestrator"

    def __init__(self, retrieval, synthesis, temporal, verification,
                 intent_llm=None, max_retries: int = 2):
        self.retrieval, self.synthesis = retrieval, synthesis
        self.temporal, self.verification = temporal, verification
        self._intent_llm = intent_llm
        self.max_retries = max_retries

    def _execute(self, state: AgentState) -> AgentState:
        state = self._classify_intent(state)
        if state.intent == "out_of_scope":
            state.verdict, state.draft = "abstain", self._abstain_message()
            return state

        while True:
            state = self.retrieval.run(state)
            state = self.synthesis.run(state)
            state = self.temporal.run(state)
            state = self.verification.run(state)
            if state.verdict == "grounded":
                return state
            if state.verdict == "abstain" or state.retries >= self.max_retries:
                state.verdict, state.draft = "abstain", self._abstain_message()
                return state
            state.retries += 1
            state = self._widen(state)
            state.verdict = ""            # clear the stale 'retry' for the next pass

    def _widen(self, state: AgentState) -> AgentState:
        """A retry that changes nothing can't succeed: broaden the retrieval
        query with any decomposed sub-queries, or fall back to the section
        keys the draft tried to cite (they name the topic even when the
        passages retrieved for them were wrong)."""
        extras = state.sub_queries or state.cited_sections
        if extras:
            state.query = state.query + " " + " ".join(extras)
        state.trace.append({"agent": self.name, "retry": state.retries,
                            "widened_query": state.query})
        return state

    def _classify_intent(self, state: AgentState) -> AgentState:
        intent = ""
        if self._intent_llm is not None:
            intent = self._llm_intent(state.query)
        if intent not in INTENTS:
            intent = self._keyword_intent(state.query)
        state.intent = intent
        state.trace.append({"agent": self.name, "intent": intent})
        return state

    def _llm_intent(self, query: str) -> str:
        from llm.client import load_prompt
        try:
            raw = self._intent_llm.generate(
                load_prompt("intent", question=query), json_mode=True)
            return json.loads(raw.strip()).get("intent", "")
        except Exception:                 # malformed output → keyword fallback
            return ""

    @staticmethod
    def _keyword_intent(query: str) -> str:
        q = query.lower()
        for intent, needles in _KEYWORDS:
            if any(n in q for n in needles):
                return intent
        return "scenario"                 # concrete situations are the residual

    @staticmethod
    def _abstain_message() -> str:
        return ("I can't answer that reliably from the PDPA corpus. "
                "This system provides information about the Act, not legal advice — "
                "please consult a qualified lawyer.")
