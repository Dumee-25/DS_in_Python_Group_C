"""Gemini implementation of the LLM adapter."""
from google import genai

from llm.client import BaseLLMClient
from telemetry.metrics import SystemMetrics


class GeminiClient(BaseLLMClient):
    def __init__(self, api_key: str, model: str = "gemini-2.0-flash"):
        self.raw_client = genai.Client(api_key=api_key)   # embedder reuses this
        self._model = model

    def generate(self, prompt: str, system: str = "", json_mode: bool = False) -> str:
        cfg = {"system_instruction": system} if system else {}
        if json_mode:
            cfg["response_mime_type"] = "application/json"
        resp = self.raw_client.models.generate_content(
            model=self._model, contents=prompt, config=cfg)
        SystemMetrics().record(
            "llm", vendor="gemini", model=self._model,
            tokens=getattr(resp.usage_metadata, "total_token_count", 0) or 0)
        return resp.text or ""
