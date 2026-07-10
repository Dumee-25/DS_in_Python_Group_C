"""Temporal/applicability specialist — the differentiator.

Annotates which cited provisions are actually in force as of the corpus
snapshot date. No LLM call: it's a metadata lookup against the
corpus manifest. This is what a plain LLM cannot do for a 2025-amended Act.
"""
import re

from agents.base import BaseAgent
from shared.contracts import AgentState

_SECTION_RE = re.compile(r"s\.(\d+)")


def _section_number(section_key: str) -> int | None:
    """'s.21(2)' -> 21; returns None for keys that don't carry a number."""
    m = _SECTION_RE.match(section_key.strip())
    return int(m.group(1)) if m else None


class TemporalAgent(BaseAgent):
    name = "temporal"

    def __init__(self, snapshot_date: str, commencement: dict | None = None):
        """commencement maps section keys/ranges to in-force metadata, e.g.
        {"s.20-s.27": {"in_force": False, "note": "..."}}. Injected here;
        app_context wires in ingestion.corpus_manifest.COMMENCEMENT.
        """
        self._snapshot = snapshot_date
        if commencement is None:
            from ingestion.corpus_manifest import COMMENCEMENT
            commencement = COMMENCEMENT
        self._commencement = commencement

    def _execute(self, state: AgentState) -> AgentState:
        for section in state.cited_sections:
            info = self._lookup(section)
            if info and not info["in_force"]:
                state.temporal_notes.append(
                    f"{section} is not yet in operation as of {self._snapshot}: "
                    f"{info['note']}")
        state.trace.append({"agent": self.name, "notes": len(state.temporal_notes)})
        return state

    def _lookup(self, section: str) -> dict | None:
        """Match 's.21(2)' against exact keys ('s.21') and ranges ('s.20-s.27')."""
        num = _section_number(section)
        for key, info in self._commencement.items():
            if "-" in key:
                lo, hi = (_section_number(part) for part in key.split("-", 1))
                if num is not None and lo is not None and hi is not None \
                        and lo <= num <= hi:
                    return info
            elif key == section or (num is not None and _section_number(key) == num):
                return info
        return None
