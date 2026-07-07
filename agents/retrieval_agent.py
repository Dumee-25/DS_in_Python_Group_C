"""Retrieval specialist: routes the query to the right collections by intent."""
from agents.base import BaseAgent
from shared.contracts import AgentState, BaseRetriever

ROUTING = {
    "definition": ["definitions", "statute"],
    "right": ["statute", "amendments"],
    "obligation": ["statute", "amendments", "guidelines"],
    "penalty": ["statute", "amendments"],
    "scenario": ["statute", "amendments", "definitions", "gazettes"],
}

DEFAULT_COLLECTIONS = ["statute"]


class RetrievalAgent(BaseAgent):
    name = "retrieval"

    def __init__(self, retriever: BaseRetriever, top_k: int):
        self._retriever = retriever
        self._top_k = top_k

    def _execute(self, state: AgentState) -> AgentState:
        collections = ROUTING.get(state.intent, DEFAULT_COLLECTIONS)
        state.retrieved = self._retriever.retrieve(state.query, self._top_k, collections)
        state.trace.append({"agent": self.name, "collections": collections,
                            "hits": len(state.retrieved)})
        return state
