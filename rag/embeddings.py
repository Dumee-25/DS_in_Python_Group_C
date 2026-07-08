from abc import ABC, abstractmethod


class BaseEmbedder(ABC):
    dim: int

    @abstractmethod
    def embed(self, texts: list[str]) -> list[list[float]]: ...


class GeminiEmbedder(BaseEmbedder):
    dim = 768

    def __init__(self, client):            # injected — no API key handling here
        self._client = client

    def embed(self, texts):
        resp = self._client.models.embed_content(
            model="text-embedding-004", contents=texts)
        return [e.values for e in resp.embeddings]


class LocalEmbedder(BaseEmbedder):
    
    dim = 384

    def __init__(self):
        from sentence_transformers import SentenceTransformer
        self._m = SentenceTransformer("all-MiniLM-L6-v2")

    def embed(self, texts):
        return self._m.encode(texts, normalize_embeddings=True).tolist()
