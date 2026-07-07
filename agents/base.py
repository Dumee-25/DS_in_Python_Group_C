"""STUB — Person B owns this file (Template Method for the agent lifecycle).

Minimal placeholder so Person C's specialist agents can run and be tested.
B: replace run() with the real template (timing, telemetry, error handling)
without changing the _execute() hook the specialists implement.
"""
from abc import abstractmethod

from shared.contracts import AgentState
from shared.contracts import BaseAgent as ContractBaseAgent


class BaseAgent(ContractBaseAgent):
    name: str = "base"

    def run(self, state: AgentState) -> AgentState:
        state.trace.append({"agent": self.name, "event": "run"})
        return self._execute(state)

    @abstractmethod
    def _execute(self, state: AgentState) -> AgentState: ...
