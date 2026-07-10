import hashlib
import json
import re
from dataclasses import asdict, replace
from pathlib import Path

from shared.contracts import Chunk

# "“controller” means, ..." — each defined term opens with the term in
# smart quotes followed by "means".
_DEFINITION_START_RE = re.compile(r"(?=[“\"][^”\"]{2,60}[”\"]\s+means)")


def _explode_definitions(chunks: list[Chunk]) -> list[Chunk]:
    """One chunk per defined term. A 1800-char wall of mixed definitions is
    invisible to both retrieval legs: the embedder can't represent which
    term it defines, and glossary words ('controller', 'processing') are so
    common corpus-wide that BM25's IDF gives them no weight. Small
    single-definition chunks make the term dominate both signals."""
    joined = " ".join(c.text for c in chunks)
    pieces = [p.strip() for p in _DEFINITION_START_RE.split(joined)
              if len(p.strip()) > 20]
    seen, out = set(), []
    template = chunks[0]
    for piece in pieces:
        key = piece[:60]                    # dedupe splitter-overlap copies
        if key not in seen:
            seen.add(key)
            out.append(replace(template, text=piece))
    return out


def _file_hash(path: str) -> str:
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def _registry_path(store) -> Path:
    return Path(store.path) / "indexed_hashes.json"


def _load_registry(store) -> dict:
    p = _registry_path(store)
    return json.loads(p.read_text(encoding="utf-8")) if p.exists() else {}


def _save_registry(store, registry: dict) -> None:
    p = _registry_path(store)
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(registry, indent=2), encoding="utf-8")


def _chunks_path(store) -> Path:
    return Path(store.path) / "chunks.json"


def _load_chunk_registry(store) -> dict:
    p = _chunks_path(store)
    return json.loads(p.read_text(encoding="utf-8")) if p.exists() else {}


def _save_chunk_registry(store, chunks_by_doc: dict) -> None:
    p = _chunks_path(store)
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(chunks_by_doc, indent=2), encoding="utf-8")


def index_corpus(store, documents: list[dict], chunker_for) -> dict[str, int]:
    
    from ingestion.loaders import load_document

    registry = _load_registry(store)
    chunk_registry = _load_chunk_registry(store)
    indexed: dict[str, int] = {}
    for entry in documents:
        path = entry["path"]
        if not Path(path).exists():
            print(f"[indexer] MISSING {path} — download it to corpus/ first")
            continue
        digest = _file_hash(path)
        if registry.get(path) == digest:
            print(f"[indexer] skip {path} (already indexed)")
            continue

        print(f"[indexer] loading {path} ...")
        text = load_document(path)
        chunker = chunker_for(entry["collection"])
        chunks = chunker.chunk(text, source_doc=Path(path).name,
                               collection=entry["collection"],
                               snapshot_date=entry["snapshot_date"],
                               in_force=entry["in_force"])
        for c in chunks:   # manifest-driven per-section collection overrides
            c.collection = entry.get("reroute_sections", {}).get(
                c.section, c.collection)
        rerouted = [c for c in chunks if c.collection == "definitions"]
        if rerouted:
            chunks = [c for c in chunks if c.collection != "definitions"]
            chunks += _explode_definitions(rerouted)
        for c in chunks[:3]:                       # narrate for the video
            print(f"    [{c.section or 'n/a'}] {c.text[:80]!r}...")
        store.add(chunks)
        registry[path] = digest
        chunk_registry[path] = [asdict(c) for c in chunks]
        indexed[path] = len(chunks)
        print(f"[indexer] {path}: {len(chunks)} chunks -> '{entry['collection']}'")

    _save_registry(store, registry)
    _save_chunk_registry(store, chunk_registry)
    return indexed


def load_indexed_chunks(store) -> list[Chunk]:
    """All stored chunks — app_context feeds these to HybridRetriever.

    Reads the chunks.json sidecar written at index time rather than bulk-
    reading Chroma: in chromadb 1.5.x, collection.get() across two or more
    collections corrupts the client's hnsw segment readers, and every later
    query() in the process fails with "Nothing found on disk". Falls back to
    store.all_chunks() only for stores indexed before the sidecar existed
    (re-run `python -m ingestion.pipeline` to generate it).
    """
    chunk_registry = _load_chunk_registry(store)
    if chunk_registry:
        return [Chunk(**d) for doc_chunks in chunk_registry.values()
                for d in doc_chunks]
    return store.all_chunks()
