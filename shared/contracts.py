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
class AgentState:            # shared pipeline state, read by every agent
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
