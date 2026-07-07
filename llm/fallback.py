"""Failover LLM client: primary vendor first, OpenRouter on any failure.

The fallback is itself a BaseLLMClient, so swapping it in required zero
changes to any agent — the Adapter pattern doing its job.
"""
import logging

import requests

from llm.client import BaseLLMClient
from telemetry.metrics import SystemMetrics

logger = logging.getLogger(__name__)

_OPENROUTER_URL = "https://openrouter.ai/api/v1/chat/completions"


class FallbackLLMClient(BaseLLMClient):
    """Try primary; on quota/network error, switch to OpenRouter. The switch is
    logged — showing it fire during the viva turns an outage into a feature."""

    def __init__(self, primary: BaseLLMClient, secondary_key: str,
                 secondary_model: str = "google/gemini-2.0-flash-exp:free"):
        self._primary = primary
        self._secondary_key = secondary_key
        self._secondary_model = secondary_model
        self.raw_client = getattr(primary, "raw_client", None)   # embedder reuse

    def generate(self, prompt: str, system: str = "", json_mode: bool = False) -> str:
        try:
            return self._primary.generate(prompt, system, json_mode)
        except Exception as exc:
            logger.warning("Primary LLM failed (%s: %s) — switching to OpenRouter",
                           type(exc).__name__, exc)
            return self._openrouter(prompt, system, json_mode)

    def _openrouter(self, prompt: str, system: str = "", json_mode: bool = False) -> str:
        messages = []
        if system:
            messages.append({"role": "system", "content": system})
        messages.append({"role": "user", "content": prompt})
        payload = {"model": self._secondary_model, "messages": messages}
        if json_mode:
            payload["response_format"] = {"type": "json_object"}
        resp = requests.post(
            _OPENROUTER_URL, json=payload, timeout=60,
            headers={"Authorization": f"Bearer {self._secondary_key}"})
        resp.raise_for_status()
        data = resp.json()
        SystemMetrics().record(
            "llm", vendor="openrouter", model=self._secondary_model,
            tokens=data.get("usage", {}).get("total_tokens", 0))
        return data["choices"][0]["message"]["content"]
