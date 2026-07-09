<!-- This becomes the repo-root README.md. TODO(D): drop in B's architecture
     PNG and the video link before submission. -->

# PDPA Agent — Multi-Agent RAG for Sri Lanka's Personal Data Protection Act

A multi-agent retrieval-augmented system that answers questions about the
Personal Data Protection Act No. 9 of 2022 (as amended in 2025) with **cited
sections**, **as-of-date commencement warnings**, and **verified grounding**
— and refuses questions it cannot answer from the corpus.

Why not just ask an LLM? The Act was amended in 2025 and phases into force
through 2026. A plain LLM confidently answers from stale training data; this
system answers only from the corpus, dates every answer, and flags provisions
that are not yet law.

## Architecture

<!-- TODO(D): embed B's exported diagram: ![architecture](docs/architecture.png) -->

User → **Orchestrator** (intent gate · bounded reflect-retry loop)
→ **Retrieval Agent** (hybrid BM25 + vector + RRF over ChromaDB)
→ **Synthesis Agent** (grounded draft with [s.X] citations)
→ **Temporal Agent** (in-force check vs the corpus snapshot date)
→ **Verification Agent** (claim-level grounding; abstains when ungrounded)

## Quickstart

```bash
git clone <repo-url> && cd <repo>
python -m venv .venv
.venv/Scripts/pip install -r requirements.txt      # Windows
cp .env.example .env                                # add your API keys
python -m ingestion.pipeline                        # index the corpus
python main.py                                      # ask questions
```

Runs fully offline for embeddings with `USE_LOCAL_EMBEDDER=true` in `.env`.

## Evaluation

```bash
python -m evaluation.runner            # full run: 20 Q/A pairs, 5 metrics
python -m evaluation.runner --smoke    # CI wiring check, no API keys needed
```

Metrics: correctness, citation F1, faithfulness, answer relevancy, and
refusal accuracy (the system must abstain on advice-seeking questions AND
answer in-scope ones). Results land in `evaluation/results.md`.

## Project structure & ownership

| Package                                                           | What                                           | Owner    |
| ----------------------------------------------------------------- | ---------------------------------------------- | -------- |
| `ingestion/`, `rag/`                                              | PDF → section-aware chunks → hybrid retrieval  | Person A |
| `shared/`, `agents/orchestrator*`, `app_context.py`, `telemetry/` | contracts, DI, agent loop                      | Person B |
| `llm/`, `agents/*_agent.py`                                       | LLM adapter + fallback, four specialist agents | Person C |
| `evaluation/`, `api/`, `mcp_server/`, CI                          | metrics, runner, REST + MCP surfaces           | Person D |

## API & MCP

```bash
uvicorn api.server:create_app --factory    # POST /ask, GET /status
python -m mcp_server.server                # MCP tools: ask_pdpa, search_corpus, list_in_force
```

## Video

<!-- TODO(D): unlisted YouTube link -->

## Ethics

See [ETHICS.md](ETHICS.md): information-not-advice, as-of dating, abstention
over fabrication, traceability, no personal-data ingestion.
