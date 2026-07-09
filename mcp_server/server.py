"""MCP server — the same AppContext behind a third front-end (CLI, REST, MCP).

Run: python -m mcp_server.server   (add `mcp` to requirements.txt — your dep)
One line for §II: exposing the system over MCP touched zero agents.
"""
from mcp.server.fastmcp import FastMCP

mcp = FastMCP("pdpa-agent")

_ctx = None


def _get_ctx():
    global _ctx
    if _ctx is None:                        # lazy: build once, on first tool call
        from app_context import AppContext
        _ctx = AppContext()
    return _ctx


@mcp.tool()
def ask_pdpa(question: str) -> dict:
    """Ask a question about Sri Lanka's Personal Data Protection Act.
    Returns a cited answer with temporal notes, or an abstention."""
    from shared.contracts import AgentState
    s = _get_ctx().orchestrator.run(AgentState(query=question))
    return {"answer": s.draft, "cited_sections": s.cited_sections,
            "temporal_notes": s.temporal_notes, "verdict": s.verdict}


@mcp.tool()
def search_corpus(query: str, top_k: int = 6) -> list[dict]:
    """Retrieve raw corpus passages (hybrid BM25 + vector search) without
    generating an answer."""
    chunks = _get_ctx().retriever.retrieve(
        query, top_k,
        ["statute", "amendments", "definitions", "gazettes", "guidelines"])
    return [{"section": c.section, "source_doc": c.source_doc,
             "score": round(c.score, 3), "text": c.text} for c in chunks]


@mcp.tool()
def list_in_force() -> dict:
    """The commencement table: which provisions are (not) in force as of the
    corpus snapshot date."""
    from ingestion.corpus_manifest import COMMENCEMENT, SNAPSHOT_DATE
    return {"snapshot_date": SNAPSHOT_DATE, "commencement": COMMENCEMENT}


if __name__ == "__main__":
    mcp.run()
