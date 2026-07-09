"""Ollama implementation of the LLM adapter.

Development and eval iteration run against a model served by the local
Ollama daemon — free and quota-less, so the eval loop can run all day.
Ollama's cloud models (tags ending in "-cloud", after `ollama signin`)
are served through the same local API, so they need no code changes here:
they're just a different OLLAMA_MODEL value.
"""
import re

import requests

from llm.client import BaseLLMClient
from telemetry.metrics import SystemMetrics

# Local models honour format:"json" (grammar-constrained decoding), but the
# -cloud models ignore it and may wrap the JSON in a markdown code fence.
_FENCE_RE = re.compile(r"^```(?:json)?\s*(.*?)\s*```$", re.DOTALL)


class OllamaClient(BaseLLMClient):
    def __init__(self, model: str = "qwen2.5:7b-instruct",
                 host: str = "http://localhost:11434", num_ctx: int = 8192):
        # num_ctx capped at 8192: a 7B Q4 model + KV cache has to fit in 6 GB
        # of VRAM. Check `ollama ps` — if the split shows CPU%, lower this.
        self._model = model
        self._url = f"{host.rstrip('/')}/api/chat"
        self._num_ctx = num_ctx
        self.raw_client = None   # embedder reuse is Gemini-specific

    def generate(self, prompt: str, system: str = "", json_mode: bool = False) -> str:
        messages = []
        if system:
            messages.append({"role": "system", "content": system})
        messages.append({"role": "user", "content": prompt})
        payload = {
            "model": self._model,
            "messages": messages,
            "stream": False,
            "options": {"num_ctx": self._num_ctx},
        }
        if json_mode:
            payload["format"] = "json"
        resp = requests.post(self._url, json=payload, timeout=300)
        resp.raise_for_status()
        data = resp.json()
        SystemMetrics().record(
            "llm", vendor="ollama", model=self._model,
            tokens=data.get("prompt_eval_count", 0) + data.get("eval_count", 0))
        content = data["message"]["content"]
        if json_mode:
            m = _FENCE_RE.match(content.strip())
            if m:
                content = m.group(1)
        return content
