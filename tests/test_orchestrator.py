from agents.base import BaseAgent
from agents.orchestrator import Orchestrator
from shared.contracts import AgentState


class FakeAgent(BaseAgent):
    """Real BaseAgent subclass so run() produces genuine trace entries."""

    def __init__(self, name: str, verdict: str | None = None):
        self.name = name
        self._verdict = verdict
        self.runs = 0

    def _execute(self, state: AgentState) -> AgentState:
        self.runs += 1
        if self._verdict:
            state.verdict = self._verdict
        return state


def _orchestrator(verifier_verdict: str, max_retries: int = 2) -> Orchestrator:
    return Orchestrator(
        retrieval=FakeAgent("retrieval"),
        synthesis=FakeAgent("synthesis"),
        temporal=FakeAgent("temporal"),
        verification=FakeAgent("verification", verdict=verifier_verdict),
        intent_llm=None,          # keyword classifier — deterministic in tests
        max_retries=max_retries,
    )


def test_terminates_within_max_retries_when_verifier_always_retries():
    orch = _orchestrator("retry", max_retries=2)
    state = orch.run(AgentState(query="What are the data subject rights?"))
    assert state.verdict == "abstain"
    assert state.retries == 2                       # bounded — no infinite loop
    assert orch.retrieval.runs == 3                 # initial + 2 retries


def test_out_of_scope_short_circuits_before_retrieval():
    orch = _orchestrator("grounded")
    state = orch.run(AgentState(query="Should I sue my employer for reading my emails?"))
    assert state.intent == "out_of_scope"
    assert state.verdict == "abstain"
    assert "not legal advice" in state.draft
    assert orch.retrieval.runs == 0                 # no retrieval spend


def test_grounded_answer_exits_on_first_pass():
    orch = _orchestrator("grounded")
    state = orch.run(AgentState(query="What is the penalty for non-compliance?"))
    assert state.intent == "penalty"
    assert state.verdict == "grounded"
    assert state.retries == 0
    assert orch.retrieval.runs == 1


def test_trace_has_one_entry_per_agent_run_including_retries():
    orch = _orchestrator("retry", max_retries=1)
    state = orch.run(AgentState(query="What are the data subject rights?"))
    per_agent = {}
    for entry in state.trace:
        per_agent[entry["agent"]] = per_agent.get(entry["agent"], 0) + 1
    # 2 passes (initial + 1 retry) → 2 entries for each specialist
    for agent in ("retrieval", "synthesis", "temporal", "verification"):
        assert per_agent[agent] == 2, state.trace


def test_query_widening_changes_the_retry_query():
    orch = _orchestrator("retry", max_retries=1)
    state = AgentState(query="What are the data subject rights?",
                       sub_queries=["right of access", "right to erasure"])
    state = orch.run(state)
    assert "right of access" in state.query         # widened, not identical rerun
