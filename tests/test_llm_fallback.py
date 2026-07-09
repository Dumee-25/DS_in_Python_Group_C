"""Fallback client must switch vendors when the primary raises."""

from llm.client import BaseLLMClient
from llm.fallback import FallbackLLMClient


class FailingPrimary(BaseLLMClient):
    raw_client = "sentinel-raw-client"

    def generate(self, prompt, system="", json_mode=False):
        raise RuntimeError("429 quota exceeded")


class HealthyPrimary(BaseLLMClient):
    raw_client = "sentinel-raw-client"

    def generate(self, prompt, system="", json_mode=False):
        return "primary answer"


def test_switches_to_openrouter_when_primary_raises(monkeypatch):
    client = FallbackLLMClient(FailingPrimary(), secondary_key="test-key")
    monkeypatch.setattr(client, "_openrouter",
                        lambda prompt, system="", json_mode=False: "fallback answer")
    assert client.generate("hello") == "fallback answer"


def test_uses_primary_when_healthy():
    client = FallbackLLMClient(HealthyPrimary(), secondary_key="test-key")
    assert client.generate("hello") == "primary answer"


def test_exposes_primary_raw_client_for_embedder_reuse():
    client = FallbackLLMClient(HealthyPrimary(), secondary_key="test-key")
    assert client.raw_client == "sentinel-raw-client"


def test_switch_is_logged(monkeypatch, caplog):
    client = FallbackLLMClient(FailingPrimary(), secondary_key="test-key")
    monkeypatch.setattr(client, "_openrouter",
                        lambda prompt, system="", json_mode=False: "fallback answer")
    with caplog.at_level("WARNING", logger="llm.fallback"):
        client.generate("hello")
    assert any("switching to OpenRouter" in r.message for r in caplog.records)
