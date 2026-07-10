"""LLM client base and versioned prompt loading.

BaseLLMClient is defined once in shared/contracts.py (the frozen contract)
and re-exported here so LLM-layer code can import everything it needs from
llm.client.
"""
from pathlib import Path

from shared.contracts import BaseLLMClient

__all__ = ["BaseLLMClient", "load_prompt"]

_PROMPTS_DIR = Path(__file__).parent / "prompts"

# Once a prompt is iterated it gets a _vN suffix and a pin here; earlier
# versions stay in the repo as the iteration record (see prompts/CHANGELOG.md).
# A/B-ing a prompt version is a one-line change.
ACTIVE_VERSIONS = {"synthesis": 2}


def load_prompt(name: str, **kwargs) -> str:
    """Versioned prompt loader. kwargs fill {placeholders} in the template.

    Prompts live in llm/prompts/<name>.txt (or <name>_v<N>.txt once versioned
    and pinned in ACTIVE_VERSIONS), never inline in code — editing behaviour
    means editing a text file, not touching Python.
    """
    version = ACTIVE_VERSIONS.get(name)
    filename = f"{name}_v{version}.txt" if version else f"{name}.txt"
    tpl = (_PROMPTS_DIR / filename).read_text(encoding="utf-8")
    return tpl.format(**kwargs)
