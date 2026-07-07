"""Retrieval agent must route collections by intent and fall back to statute."""
from agents.retrieval_agent import RetrievalAgent
from shared.contracts import AgentState, BaseRetriever, Chunk


class RecordingRetriever(BaseRetriever):
    def __init__(self):
        self.last_collections = None

    def retrieve(self, query, top_k, collections):
        self.last_collections = collections
        return [Chunk(text="t", source_doc="d", section="s.1",
                      collection=collections[0], snapshot_date="2026-01-01",
                      in_force=True)]


def _run(intent):
    retriever = RecordingRetriever()
    agent = RetrievalAgent(retriever, top_k=5)
    state = agent.run(AgentState(query="q", intent=intent))
    return retriever, state


def test_right_intent_routes_to_statute_and_amendments():
    retriever, state = _run("right")
    assert retriever.last_collections == ["statute", "amendments"]
    assert len(state.retrieved) == 1


def test_unknown_intent_falls_back_to_statute():
    retriever, _ = _run("nonsense")
    assert retriever.last_collections == ["statute"]


def test_scenario_intent_searches_widest():
    retriever, _ = _run("scenario")
    assert set(retriever.last_collections) == {"statute", "amendments",
                                               "definitions", "gazettes"}


def test_trace_records_routing():
    _, state = _run("penalty")
    assert any(t.get("collections") == ["statute", "amendments"] for t in state.trace)
