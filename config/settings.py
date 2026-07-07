import os
from dataclasses import dataclass

from dotenv import load_dotenv

load_dotenv()


@dataclass(frozen=True)
class Settings:
    gemini_api_key: str = os.getenv("GEMINI_API_KEY", "")
    openrouter_api_key: str = os.getenv("OPENROUTER_API_KEY", "")
    chroma_path: str = os.getenv("CHROMA_PATH", "./chroma_db")
    top_k: int = int(os.getenv("TOP_K", "6"))
    max_retries: int = int(os.getenv("MAX_AGENT_RETRIES", "2"))
    snapshot_date: str = os.getenv("CORPUS_SNAPSHOT_DATE", "2026-07-01")
    use_local_embedder: bool = os.getenv("USE_LOCAL_EMBEDDER", "false") == "true"

# TODO(B): mirror any new variable in .env.example — named brief requirement.
