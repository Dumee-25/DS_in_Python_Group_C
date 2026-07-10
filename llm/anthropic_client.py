"""Anthropic implementation of the LLM adapter.

Reserved for the LLM judges and the final graded eval run: judging with a
different vendor than the generator avoids self-preference bias.
Haiku 4.5 keeps a full ~200-call eval run around $1.
"""
from llm.client import BaseLLMClient
from telemetry.metrics import SystemMetrics

_JSON_NUDGE = "Respond with a single valid JSON object and nothing else."


class AnthropicClient(BaseLLMClient):
    def __init__(self, api_key: str, model: str = "claude-haiku-4-5",
                 max_tokens: int = 4096):
        # Imported lazily so the package is only required when
        # LLM_VENDOR=anthropic is actually selected.
        import anthropic
        self._client = anthropic.Anthropic(api_key=api_key)
        self._model = model
        self._max_tokens = max_tokens
        self.raw_client = None   # embedder reuse is Gemini-specific

    def generate(self, prompt: str, system: str = "", json_mode: bool = False) -> str:
        if json_mode:
            system = f"{system}\n\n{_JSON_NUDGE}".strip()
        kwargs = {
            "model": self._model,
            "max_tokens": self._max_tokens,
            "messages": [{"role": "user", "content": prompt}],
        }
        if system:
            kwargs["system"] = system
        resp = self._client.messages.create(**kwargs)
        SystemMetrics().record(
            "llm", vendor="anthropic", model=self._model,
            tokens=resp.usage.input_tokens + resp.usage.output_tokens)
        return "".join(b.text for b in resp.content if b.type == "text")
