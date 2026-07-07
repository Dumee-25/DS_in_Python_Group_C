import time
from abc import abstractmethod

from shared.contracts import AgentState
from shared.contracts import BaseAgent as ContractBaseAgent


class BaseAgent(ContractBaseAgent):
    name: str = "base"

    def run(self, state: AgentState) -> AgentState:
        t0 = time.perf_counter()
        try:
            state = self._execute(state)
            status = "ok"
        except Exception as e:                 # fail loud into the trace, not silently
            state.verdict, status = "abstain", f"error: {e}"
        state.trace.append({
            "agent": self.name,
            "ms": round((time.perf_counter() - t0) * 1000),
            "status": status,
            "retrieved_sections": [c.section for c in state.retrieved],
            "verdict": state.verdict,
        })
        return state

    @abstractmethod
    def _execute(self, state: AgentState) -> AgentState: ...
