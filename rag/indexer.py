import hashlib
import json
from pathlib import Path

from shared.contracts import Chunk


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


def index_corpus(store, documents: list[dict], chunker_for) -> dict[str, int]:
    
    from ingestion.loaders import load_document

    registry = _load_registry(store)
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
        for c in chunks[:3]:                       # narrate for the video
            print(f"    [{c.section or 'n/a'}] {c.text[:80]!r}...")
        store.add(chunks)
        registry[path] = digest
        indexed[path] = len(chunks)
        print(f"[indexer] {path}: {len(chunks)} chunks -> '{entry['collection']}'")

    _save_registry(store, registry)
    return indexed


def load_indexed_chunks(store) -> list[Chunk]:
    """All stored chunks — app_context (Person B) feeds these to HybridRetriever."""
    return store.all_chunks()
