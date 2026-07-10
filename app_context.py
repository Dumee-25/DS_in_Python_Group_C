from config.settings import Settings


def make_primary_llm(settings: Settings):
    """The vendor switch: LLM_VENDOR picks which client answers.

    Pure DI — agents only ever see BaseLLMClient, so changing vendor is a
    one-line .env edit ("local 7B for development, frontier model for the
    final evaluation, behind one adapter").
    """
    if settings.llm_vendor == "ollama":
        from llm.ollama_client import OllamaClient
        return OllamaClient(settings.ollama_model, settings.ollama_host)
    if settings.llm_vendor == "anthropic":
        from llm.anthropic_client import AnthropicClient
        return AnthropicClient(settings.anthropic_api_key, settings.anthropic_model)
    if settings.llm_vendor == "gemini":
        from llm.gemini import GeminiClient
        return GeminiClient(settings.gemini_api_key)
    raise ValueError(
        f"Unknown LLM_VENDOR {settings.llm_vendor!r} — use ollama | gemini | anthropic")


class AppContext:
    def __init__(self, settings: Settings | None = None):
        self.settings = settings or Settings()

        # llm layer
        from llm.fallback import FallbackLLMClient
        self.llm = FallbackLLMClient(
            primary=make_primary_llm(self.settings),
            secondary_key=self.settings.openrouter_api_key,
        )

        # rag layer
        from rag.embeddings import GeminiEmbedder, LocalEmbedder
        from rag.store import VectorStore
        if self.settings.use_local_embedder:
            embedder = LocalEmbedder()
        else:
            # Gemini embeddings need a genai client; when the generation
            # vendor isn't Gemini there's no raw_client to reuse, so build
            # one just for the embedder.
            raw = self.llm.raw_client
            if raw is None:
                from llm.gemini import GeminiClient
                raw = GeminiClient(self.settings.gemini_api_key).raw_client
            embedder = GeminiEmbedder(raw)
        self.store = VectorStore(self.settings.chroma_path, embedder)

        from rag.hybrid import HybridRetriever
        from rag.indexer import load_indexed_chunks
        self.retriever = HybridRetriever(self.store, load_indexed_chunks(self.store))

        # agents (specialists + orchestrator)
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
