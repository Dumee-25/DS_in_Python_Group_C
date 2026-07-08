from ingestion.chunking import RecursiveChunker, SectionAwareChunker
from rag.embeddings import BaseEmbedder
from rag.hybrid import HybridRetriever
from rag.store import VectorStore
from shared.contracts import Chunk


# chunking

def test_section_chunker_preserves_citation_keys():
    text = ("1. Short title.\nThis Act may be cited as the PDPA.\n"
            "2. Application.\nThis Act applies to processing...")
    chunks = SectionAwareChunker().chunk(text, "act.pdf", "statute",
                                         "2026-07-01", True)
    assert [c.section for c in chunks] == ["s.1", "s.2"]


def test_section_chunker_splits_long_sections_keeping_key():
    text = "1. Short title.\n" + ("lawful processing " * 400)   # > 1800 chars
    chunks = SectionAwareChunker().chunk(text, "act.pdf", "statute",
                                         "2026-07-01", True)
    assert len(chunks) > 1
    assert all(c.section == "s.1" for c in chunks)


def test_recursive_chunker_overlaps():
    text = "".join(chr(65 + i % 26) for i in range(300))  
    chunker = RecursiveChunker(size=100, overlap=20)
    chunks = chunker.chunk(text, "doc.pdf", "guidelines", "2026-07-01", True)
    assert len(chunks) >= 3
    assert chunks[0].text[-20:] == chunks[1].text[:20]      # shared overlap


# store round-trip 

class FakeEmbedder(BaseEmbedder):
    """Deterministic 4-d embedding — no network, no model download."""
    dim = 4

    def embed(self, texts):
        return [[(hash(t) % 97) / 97, len(t) % 89 / 89,
                 (hash(t[::-1]) % 83) / 83, 0.5] for t in texts]


def _chunk(text, section, collection="statute"):
    return Chunk(text=text, source_doc="act.pdf", section=section,
                 collection=collection, snapshot_date="2026-07-01",
                 in_force=True)


def test_store_round_trips_a_chunk(tmp_path):
    store = VectorStore(str(tmp_path / "chroma"), FakeEmbedder())
    store.add([_chunk("A controller shall process data lawfully.", "s.5")])
    out = store.query("lawful processing", top_k=1, collections=["statute"])
    assert out[0].section == "s.5"
    assert out[0].source_doc == "act.pdf"
    assert out[0].in_force is True


def test_all_chunks_returns_everything(tmp_path):
    store = VectorStore(str(tmp_path / "chroma"), FakeEmbedder())
    store.add([_chunk("text one", "s.1"), _chunk("text two", "s.2")])
    assert {c.section for c in store.all_chunks()} == {"s.1", "s.2"}


# hybrid beats vector-only 

TARGET = "special categories of personal data include biometric data"


class RiggedEmbedder(BaseEmbedder):
    """Adversarial: the target chunk is embedded FAR from every query, so
    pure vector search must rank it last; BM25 should rescue it."""
    dim = 2

    def embed(self, texts):
        return [[1.0, 0.0] if t == TARGET else [0.0, 1.0] for t in texts]


def test_hybrid_beats_vector_only_on_exact_phrase(tmp_path):
    chunks = [
        _chunk(TARGET, "s.26"),
        _chunk("controllers must notify the authority of breaches", "s.23"),
        _chunk("data subjects may request rectification of records", "s.15"),
        _chunk("the authority may impose administrative penalties", "s.38"),
    ]
    store = VectorStore(str(tmp_path / "chroma"), RiggedEmbedder())
    store.add(chunks)

    query = "special categories of personal data"
    vector_only = store.query(query, top_k=2, collections=["statute"])
    assert all(c.section != "s.26" for c in vector_only)     # vector misses it

    hybrid = HybridRetriever(store, store.all_chunks())
    fused = hybrid.retrieve(query, top_k=2, collections=["statute"])
    assert any(c.section == "s.26" for c in fused)           # BM25 rescues it
