
from config.settings import Settings
from ingestion.chunking import RecursiveChunker, SectionAwareChunker
from ingestion.corpus_manifest import DOCUMENTS
from rag.indexer import index_corpus
from rag.store import VectorStore

# statute/amendments have clean section numbering; guidelines/notices don't
SECTIONED_COLLECTIONS = {"statute", "amendments"}


def _build_store() -> VectorStore:
    settings = Settings()
    if settings.use_local_embedder or not settings.gemini_api_key:
        from rag.embeddings import LocalEmbedder
        embedder = LocalEmbedder()
        print("[pipeline] embedder: local (all-MiniLM-L6-v2)")
    else:
        from google import genai
        from rag.embeddings import GeminiEmbedder
        embedder = GeminiEmbedder(genai.Client(api_key=settings.gemini_api_key))
        print("[pipeline] embedder: gemini text-embedding-004")
    return VectorStore(settings.chroma_path, embedder)


def _chunker_for(collection: str):
    if collection in SECTIONED_COLLECTIONS:
        return SectionAwareChunker()
    return RecursiveChunker()


def main():
    store = _build_store()
    indexed = index_corpus(store, DOCUMENTS, _chunker_for)
    print("\n[pipeline] indexed this run:", indexed or "nothing new")
    print("[pipeline] collection counts:", store.counts())


if __name__ == "__main__":
    main()
