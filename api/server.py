"""FastAPI surface — traceability exposed at the API level.

Run: uvicorn api.server:create_app --factory
Web UI at /, interactive API docs at /docs.
"""
from pathlib import Path

from fastapi import FastAPI
from fastapi.responses import HTMLResponse
from pydantic import BaseModel

from app_context import AppContext
from shared.contracts import AgentState

_INDEX = Path(__file__).parent / "static" / "index.html"


def create_app() -> FastAPI:
    app, ctx = FastAPI(title="PDPA Agent"), AppContext()

    @app.get("/", response_class=HTMLResponse)
    def index():
        return _INDEX.read_text(encoding="utf-8")

    class Ask(BaseModel):
        question: str

    @app.post("/ask")
    def ask(body: Ask):
        s = ctx.orchestrator.run(AgentState(query=body.question))
        return {"answer": s.draft, "cited_sections": s.cited_sections,
                "temporal_notes": s.temporal_notes, "verdict": s.verdict,
                "trace": s.trace}          # traceability at the API surface

    @app.get("/status")
    def status():
        from telemetry.metrics import SystemMetrics
        m = SystemMetrics()
        return {"calls": m.calls, "tokens": m.tokens}

    return app
