from shared.contracts import AgentState, Chunk


class StubOrchestrator:
    name = "orchestrator-stub"

    def run(self, state: AgentState) -> AgentState:
        state.intent = "definition"
        state.retrieved = [
            Chunk(text="'processing' means any operation performed on personal data...",
                  source_doc="pdpa_act_9_2022.pdf", section="s.56",
                  collection="statute", snapshot_date="2026-07-01",
                  in_force=True, score=0.91),
            Chunk(text="A controller shall process personal data lawfully...",
                  source_doc="pdpa_act_9_2022.pdf", section="s.5",
                  collection="statute", snapshot_date="2026-07-01",
                  in_force=True, score=0.84),
        ]
        state.draft = ("Processing means any operation performed on personal data "
                       "[s.56], and controllers must process lawfully [s.5].")
        state.cited_sections = ["s.56", "s.5"]
        state.verdict = "grounded"
        state.trace.append({"agent": self.name, "status": "stub"})
        return state
