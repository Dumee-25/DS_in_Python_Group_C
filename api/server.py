"""FastAPI surface — traceability exposed at the API level.

Run: uvicorn api.server:create_app --factory
"""
from fastapi import FastAPI
from pydantic import BaseModel

from app_context import AppContext
from shared.contracts import AgentState


def create_app() -> FastAPI:
    app, ctx = FastAPI(title="PDPA Agent"), AppContext()

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
