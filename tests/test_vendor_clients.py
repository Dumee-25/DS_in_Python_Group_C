"""Vendor switch + Ollama/Anthropic clients — all HTTP mocked, no network."""
import pytest

from app_context import make_primary_llm
from config.settings import Settings
from llm.fallback import FallbackLLMClient
from llm.ollama_client import OllamaClient


class _FakeResponse:
    def __init__(self, data):
        self._data = data

    def raise_for_status(self):
        pass

    def json(self):
        return self._data


def test_ollama_sends_chat_payload(monkeypatch):
    captured = {}

    def fake_post(url, json=None, timeout=None):
        captured["url"] = url
        captured["payload"] = json
        return _FakeResponse({"message": {"content": "s.13 grants access."},
                              "prompt_eval_count": 10, "eval_count": 5})

    monkeypatch.setattr("llm.ollama_client.requests.post", fake_post)
    client = OllamaClient(model="qwen2.5:7b-instruct")
    out = client.generate("What does s.13 say?", system="You are a PDPA assistant.")

    assert out == "s.13 grants access."
    assert captured["url"] == "http://localhost:11434/api/chat"
    assert captured["payload"]["model"] == "qwen2.5:7b-instruct"
    assert captured["payload"]["messages"][0] == {
        "role": "system", "content": "You are a PDPA assistant."}
    assert captured["payload"]["stream"] is False
    assert "format" not in captured["payload"]


def test_ollama_json_mode_sets_format(monkeypatch):
    captured = {}

    def fake_post(url, json=None, timeout=None):
        captured["payload"] = json
        return _FakeResponse({"message": {"content": "{}"}})

    monkeypatch.setattr("llm.ollama_client.requests.post", fake_post)
    OllamaClient().generate("q", json_mode=True)
    assert captured["payload"]["format"] == "json"


def test_ollama_json_mode_strips_markdown_fences(monkeypatch):
    """-cloud models ignore format:"json" and may fence the JSON."""
    fenced = '```json\n{"verdict": "grounded"}\n```'

    def fake_post(url, json=None, timeout=None):
        return _FakeResponse({"message": {"content": fenced}})

    monkeypatch.setattr("llm.ollama_client.requests.post", fake_post)
    assert OllamaClient().generate("q", json_mode=True) == '{"verdict": "grounded"}'
    # without json_mode the content passes through untouched
    assert OllamaClient().generate("q") == fenced


def test_ollama_down_triggers_openrouter_fallback(monkeypatch):
    """The viva demo: local model unreachable -> logged switch to cloud."""
    import requests

    def fake_post(url, json=None, timeout=None):
        raise requests.ConnectionError("Ollama is not running")

    monkeypatch.setattr("llm.ollama_client.requests.post", fake_post)
    client = FallbackLLMClient(OllamaClient(), secondary_key="test-key")
    monkeypatch.setattr(client, "_openrouter",
                        lambda prompt, system="", json_mode=False: "cloud answer")
    assert client.generate("hello") == "cloud answer"


def test_vendor_switch_selects_ollama():
    primary = make_primary_llm(Settings(llm_vendor="ollama"))
    assert isinstance(primary, OllamaClient)


def test_vendor_switch_selects_gemini():
    from llm.gemini import GeminiClient
    primary = make_primary_llm(Settings(llm_vendor="gemini", gemini_api_key="k"))
    assert isinstance(primary, GeminiClient)


def test_vendor_switch_rejects_unknown_vendor():
    with pytest.raises(ValueError, match="Unknown LLM_VENDOR"):
        make_primary_llm(Settings(llm_vendor="chatgpt"))


def test_anthropic_client_extracts_text_and_nudges_json(monkeypatch):
    pytest.importorskip("anthropic")
    from llm.anthropic_client import AnthropicClient

    captured = {}

    class _Block:
        type = "text"
        text = "judged: grounded"

    class _Usage:
        input_tokens = 10
        output_tokens = 5

    class _FakeMessages:
        def create(self, **kwargs):
            captured.update(kwargs)
            return type("R", (), {"content": [_Block()], "usage": _Usage()})()

    client = AnthropicClient(api_key="test-key")
    monkeypatch.setattr(client, "_client",
                        type("C", (), {"messages": _FakeMessages()})())

    out = client.generate("judge this", system="You are a strict judge.",
                          json_mode=True)
    assert out == "judged: grounded"
    assert captured["model"] == "claude-haiku-4-5"
    assert captured["system"].startswith("You are a strict judge.")
    assert "valid JSON object" in captured["system"]
