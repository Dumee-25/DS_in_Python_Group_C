"""LLM client base and versioned prompt loading.

BaseLLMClient is defined once in shared/contracts.py (the frozen contract)
and re-exported here so LLM-layer code can import everything it needs from
llm.client.
"""
from pathlib import Path

from shared.contracts import BaseLLMClient

__all__ = ["BaseLLMClient", "load_prompt"]

_PROMPTS_DIR = Path(__file__).parent / "prompts"


def load_prompt(name: str, **kwargs) -> str:
    """Versioned prompt loader. kwargs fill {placeholders} in the template.

    Prompts live in llm/prompts/<name>.txt, never inline in code — editing
    behaviour means editing a text file, not touching Python.
    """
    tpl = (_PROMPTS_DIR / f"{name}.txt").read_text(encoding="utf-8")
    return tpl.format(**kwargs)
