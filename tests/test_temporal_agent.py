"""Temporal agent must annotate cited sections that are not yet in force."""
from agents.temporal_agent import TemporalAgent
from shared.contracts import AgentState

COMMENCEMENT = {
    "s.20-s.27": {"in_force": False,
                  "note": "commences on a date appointed by Gazette Order"},
    "s.35": {"in_force": True, "note": "in force since 2023-07-17"},
}


def _agent():
    return TemporalAgent(snapshot_date="2026-07-07", commencement=COMMENCEMENT)


def test_not_in_force_section_gets_a_note():
    state = AgentState(query="q", cited_sections=["s.21(2)"])
    state = _agent().run(state)
    assert len(state.temporal_notes) == 1
    assert "s.21(2)" in state.temporal_notes[0]
    assert "2026-07-07" in state.temporal_notes[0]


def test_range_boundaries_match():
    for section in ("s.20", "s.27"):
        state = _agent().run(AgentState(query="q", cited_sections=[section]))
        assert state.temporal_notes, f"{section} should fall inside s.20-s.27"


def test_in_force_section_gets_no_note():
    state = _agent().run(AgentState(query="q", cited_sections=["s.35"]))
    assert state.temporal_notes == []


def test_unknown_section_gets_no_note():
    state = _agent().run(AgentState(query="q", cited_sections=["s.99"]))
    assert state.temporal_notes == []


def test_subsection_of_exact_key_matches():
    state = _agent().run(AgentState(query="q", cited_sections=["s.35(1)"]))
    assert state.temporal_notes == []   # matched s.35, which is in force
