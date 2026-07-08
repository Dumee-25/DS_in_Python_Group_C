import chromadb

from shared.contracts import Chunk


class VectorStore:
    def __init__(self, path: str, embedder):
        self.path = path
        self._client = chromadb.PersistentClient(path=path)
        self._embedder = embedder
        self._heal_dimension_mismatches()

    def _heal_dimension_mismatches(self) -> None:
        
        for coll in self._client.list_collections():
            stored_dim = (coll.metadata or {}).get("dim")
            if stored_dim is not None and stored_dim != self._embedder.dim:
                print(f"[store] '{coll.name}' indexed at dim={stored_dim}, "
                      f"active embedder dim={self._embedder.dim} — dropping "
                      f"for re-index")
                self._client.delete_collection(coll.name)

    def _collection(self, name: str):
        return self._client.get_or_create_collection(
            name, metadata={"dim": self._embedder.dim})

    def add(self, chunks: list[Chunk]) -> None:
        by_coll: dict[str, list[Chunk]] = {}
        for c in chunks:
            by_coll.setdefault(c.collection, []).append(c)
        for coll_name, cs in by_coll.items():
            coll = self._collection(coll_name)
            offset = coll.count()          # keep ids unique across add() calls
            coll.add(
                ids=[f"{c.source_doc}:{c.section}:{offset + i}"
                     for i, c in enumerate(cs)],
                documents=[c.text for c in cs],
                embeddings=self._embedder.embed([c.text for c in cs]),
                metadatas=[{"section": c.section, "source_doc": c.source_doc,
                            "snapshot_date": c.snapshot_date,
                            "in_force": c.in_force} for c in cs],
            )

    def query(self, text: str, top_k: int, collections: list[str]) -> list[Chunk]:
        results: list[Chunk] = []
        emb = self._embedder.embed([text])[0]
        for name in collections:
            coll = self._collection(name)
            if coll.count() == 0:
                continue
            r = coll.query(query_embeddings=[emb],
                           n_results=min(top_k, coll.count()))
            for doc, meta, dist in zip(r["documents"][0], r["metadatas"][0],
                                       r["distances"][0]):
                results.append(Chunk(text=doc, source_doc=meta["source_doc"],
                                     section=meta["section"], collection=name,
                                     snapshot_date=meta["snapshot_date"],
                                     in_force=meta["in_force"], score=1 - dist))
        return sorted(results, key=lambda c: c.score, reverse=True)[:top_k]

    def all_chunks(self) -> list[Chunk]:
        """Everything in the store — HybridRetriever builds its BM25 index
        from this at startup."""
        chunks: list[Chunk] = []
        for coll in self._client.list_collections():
            data = coll.get()
            for doc, meta in zip(data["documents"], data["metadatas"]):
                chunks.append(Chunk(text=doc, source_doc=meta["source_doc"],
                                    section=meta["section"], collection=coll.name,
                                    snapshot_date=meta["snapshot_date"],
                                    in_force=meta["in_force"]))
        return chunks

    def counts(self) -> dict[str, int]:
        return {c.name: c.count() for c in self._client.list_collections()}
