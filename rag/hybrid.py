
from rank_bm25 import BM25Okapi

from shared.contracts import BaseRetriever, Chunk


class HybridRetriever(BaseRetriever):
   #Strategy #2 for retrieval: BM25 + vector, fused with RRF (k=60).

    def __init__(self, store, all_chunks: list[Chunk]):
        self._store = store
        self._chunks = all_chunks
        self._bm25 = BM25Okapi([c.text.lower().split() for c in all_chunks])

    def retrieve(self, query, top_k, collections):
        vec = self._store.query(query, top_k * 2, collections)
        scores = self._bm25.get_scores(query.lower().split())
        kw_ranked = sorted(range(len(scores)), key=lambda i: scores[i],
                           reverse=True)[:top_k * 2]
        kw = [self._chunks[i] for i in kw_ranked
              if self._chunks[i].collection in collections]

        fused: dict[str, float] = {}
        pool: dict[str, Chunk] = {}
        for rank_list in (vec, kw):
            for rank, c in enumerate(rank_list):
                key = f"{c.source_doc}:{c.section}:{c.text[:40]}"
                fused[key] = fused.get(key, 0) + 1 / (60 + rank)
                pool[key] = c
        best = sorted(fused, key=fused.get, reverse=True)[:top_k]
        return [pool[k] for k in best]


