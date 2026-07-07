"""Frozen interface contracts — the constitution of the codebase.

Agreed by all four members in Phase 0. Changing anything in this file
requires a PR approved by the whole team (see Master Plan §4).

Ownership of implementations:
    Chunk / BaseRetriever  -> Person A (ingestion, rag)
    AgentState / BaseAgent -> Person B (orchestrator, telemetry)
    BaseLLMClient          -> Person C (llm, specialist agents)
    Eval/API consumers     -> Person D (evaluation, api, mcp_server)
"""
from abc import ABC, abstractmethod
from dataclasses import dataclass, field


@dataclass
class Chunk:
    text: str
    source_doc: str          # "pdpa_act_9_2022.pdf"
    section: str             # "s.21(2)" — the citation key
    collection: str          # statute | amendments | gazettes | guidelines | definitions
    snapshot_date: str       # ISO date of the corpus snapshot
    in_force: bool
    score: float = 0.0       # filled by retrieval


@dataclass
class AgentState:            # owned by Person B, read by everyone
    query: str
    intent: str = ""
    sub_queries: list[str] = field(default_factory=list)
    retrieved: list[Chunk] = field(default_factory=list)
    draft: str = ""
    cited_sections: list[str] = field(default_factory=list)
    temporal_notes: list[str] = field(default_factory=list)
    verdict: str = ""        # grounded | retry | abstain
    retries: int = 0
    trace: list[dict] = field(default_factory=list)   # per-step log → traceability


class BaseAgent(ABC):
    name: str = "base"

    @abstractmethod
    def run(self, state: AgentState) -> AgentState: ...


class BaseRetriever(ABC):
    @abstractmethod
    def retrieve(self, query: str, top_k: int, collections: list[str]) -> list[Chunk]: ...


class BaseLLMClient(ABC):
    """Adapter: agents call generate(); which vendor answers is invisible to them."""

    @abstractmethod
    def generate(self, prompt: str, system: str = "", json_mode: bool = False) -> str: ...
