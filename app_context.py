from config.settings import Settings


class AppContext:
    def __init__(self, settings: Settings | None = None):
        self.settings = settings or Settings()

        # llm layer (Person C's classes)
        from llm.fallback import FallbackLLMClient
        from llm.gemini import GeminiClient
        self.llm = FallbackLLMClient(
            primary=GeminiClient(self.settings.gemini_api_key),
            secondary_key=self.settings.openrouter_api_key,
        )

        # rag layer (Person A's classes)
        from rag.embeddings import GeminiEmbedder, LocalEmbedder
        from rag.store import VectorStore
        embedder = (LocalEmbedder() if self.settings.use_local_embedder
                    else GeminiEmbedder(self.llm.raw_client))
        self.store = VectorStore(self.settings.chroma_path, embedder)

        from rag.hybrid import HybridRetriever
        from rag.indexer import load_indexed_chunks
        self.retriever = HybridRetriever(self.store, load_indexed_chunks(self.store))

        # agents (Person C's specialists + the orchestrator)
        from agents.orchestrator import Orchestrator
        from agents.retrieval_agent import RetrievalAgent
        from agents.synthesis_agent import SynthesisAgent
        from agents.temporal_agent import TemporalAgent
        from agents.verification_agent import VerificationAgent
        from ingestion.corpus_manifest import COMMENCEMENT
        self.orchestrator = Orchestrator(
            retrieval=RetrievalAgent(self.retriever, self.settings.top_k),
            synthesis=SynthesisAgent(self.llm),
            temporal=TemporalAgent(self.settings.snapshot_date,
                                   commencement=COMMENCEMENT),
            verification=VerificationAgent(self.llm),
            intent_llm=self.llm,
            max_retries=self.settings.max_retries,
        )


def stub_context():
    """Dependency-free context: canned orchestrator, no LLM, no store.
    CI's eval smoke mode and pre-integration development run against this,
    which is why CI needs no API keys."""
    import types

    from agents.orchestrator_stub import StubOrchestrator
    return types.SimpleNamespace(
        settings=Settings(),
        llm=None,
        orchestrator=StubOrchestrator(),
    )
