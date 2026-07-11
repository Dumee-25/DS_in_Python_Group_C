<!-- TODO: drop in the architecture PNG (docs/architecture.png) and the video link before submission. -->

# PDPA Agent: Multi-Agent RAG for Sri Lanka's Personal Data Protection Act

A multi-agent retrieval-augmented system that answers questions about the
Personal Data Protection Act No. 9 of 2022, as amended by Act No. 22 of 2025,
with **cited sections**, **gazette-backed in-force warnings**, and
**verified grounding**. It refuses questions it cannot answer from the corpus.

Why not just ask an LLM? The Act was amended after every model's training
cutoff, and its core parts (rights, obligations, penalties) are **still not
in force**: the 18 March 2025 appointed date was repealed four days early by
Gazette 2427/34, and no fresh Order exists. A plain LLM answers from stale
training data as if all of it were law. This system answers only from the
corpus, dates every answer to the corpus snapshot, and warns section by
section about what is not yet in operation.

**Final evaluation: 20/20 refusal accuracy, citation F1 0.75, faithfulness
1.00 on every judged answer across all seven committed runs.** Full evidence
in [`evaluation/`](evaluation/).

## Quickstart (easiest path: Ollama, free, no API keys)

The fastest way to run the system is with an Ollama cloud model. It is free,
needs no GPU, and no API keys.

1. **Install Ollama**: download from [ollama.com/download](https://ollama.com/download)
2. **Create an Ollama account and sign in** (cloud models need it):
   ```bash
   ollama signin
   ```
3. **Set up the project**:
   ```bash
   git clone https://github.com/Dumee-25/DS_in_Python_Group_C.git
   cd DS_in_Python_Group_C
   python -m venv .venv
   .venv\Scripts\activate            # Windows   (source .venv/bin/activate on Linux/macOS)
   pip install -r requirements.txt
   copy .env.example .env            # cp on Linux/macOS
   ```
4. **Point `.env` at the cloud model** (already the shipped default apart
   from the model name):
   ```env
   LLM_VENDOR=ollama
   OLLAMA_MODEL=gemma4:31b-cloud
   USE_LOCAL_EMBEDDER=true
   ```
5. **Index the corpus and ask something**:
   ```bash
   python -m ingestion.pipeline      # chunks the two statute PDFs into ChromaDB
   python main.py                    # CLI: ask questions, Ctrl+C to exit
   ```

Embeddings run fully offline (a local MiniLM model), so the only network
dependency is the Ollama cloud call for generation.

### Alternatives

| Option | `.env` | Notes |
|---|---|---|
| Local model, fully offline generation | `OLLAMA_MODEL=qwen2.5:7b-instruct` after `ollama pull qwen2.5:7b-instruct` | needs roughly 5 GB of VRAM or patience on CPU |
| Gemini | `LLM_VENDOR=gemini` + `GEMINI_API_KEY` | free tier is about 100 requests/day |
| Anthropic | `LLM_VENDOR=anthropic` + `ANTHROPIC_API_KEY` | used for the LLM judges in the final graded run |

The vendor switch is one line in `.env`; no code changes. An OpenRouter
fallback (`OPENROUTER_API_KEY`) wraps whichever vendor you pick and takes
over, with a logged switch, if the primary fails.

## Four front-ends, one core

```bash
python main.py                                   # CLI
python -m uvicorn api.server:create_app --factory
#   web UI  -> http://127.0.0.1:8000/            (answers, warnings, agent trace)
#   REST    -> POST /ask, GET /status            (interactive docs at /docs)
python -m mcp_server.server                      # MCP tools: ask_pdpa, search_corpus, list_in_force
python -m evaluation.runner                      # the evaluation harness
```

All four consume the same `AppContext` composition root; adding a surface
touches zero agents.

> Tip: if you have several Pythons installed, prefer `python -m uvicorn ...`
> over bare `uvicorn` so the right interpreter serves the app.

## Architecture

<!-- TODO: embed the architecture diagram: ![architecture](docs/architecture.png) -->

User question
→ **Orchestrator** (intent gate, bounded reflect-retry loop, max 2 retries)
→ **Retrieval Agent** (hybrid BM25 + vector, fused with RRF, intent-routed
ChromaDB collections: statute, amendments, definitions)
→ **Synthesis Agent** (grounded JSON draft with [s.X] citations, versioned
prompts in `llm/prompts/`)
→ **Temporal Agent** (in-force check against the hand-verified commencement
manifest; attaches gazette-cited warnings; no LLM call)
→ **Verification Agent** (two layers: deterministic fabricated-citation
check, then claim-level LLM grounding; failures widen the retry, exhausted
budgets abstain)

Design notes:

- **Contracts first**: every layer codes against the frozen ABCs and
  dataclasses in `shared/contracts.py`
- **Section-aware chunking**: chunks carry their citation key (`s.16`);
  the interpretation section is split one chunk per defined term
- **Traceability**: `AgentState.trace` records every agent's latency, hits
  and verdict; it is returned by the REST API and rendered in the web UI
- **Prompt versioning**: prompts are files with pinned live versions;
  iteration history and measured effects in
  [`llm/prompts/CHANGELOG.md`](llm/prompts/CHANGELOG.md)

## Evaluation

```bash
python -m evaluation.runner            # full run: 20 Q/A pairs, 5 metrics
python -m evaluation.runner --smoke    # CI wiring check, no API keys needed
```

Twenty gold question-answer pairs, hand-audited against the statute text,
scored on citation F1, refusal accuracy (over-refusal counts as a failure),
and LLM-judged correctness, faithfulness and relevancy. Results land in
`evaluation/results.md`; the seven committed tables
(`results_v1_baseline.md` through `results_v7_prompt_v2.md`) document the
diagnose-fix-rerun iteration that took refusal accuracy from an honest
11/20 to 20/20 and citation F1 from 0.36 to 0.75.

## Tests and CI

```bash
python -m ruff check .
python -m pytest tests/ -q            # 56 tests, all mocked, no network
```

CI runs lint, the test suite and a dependency-free smoke evaluation on every
push and pull request.

## Project structure

```
agents/       orchestrator + four specialist agents
api/          FastAPI: REST endpoints + web UI (api/static/)
config/       Settings, read from .env
corpus/       official statute PDFs (parliament.lk)
evaluation/   qa_pairs, metrics, runner, result tables
ingestion/    loaders, OCR fallback, chunkers, corpus manifest
llm/          vendor clients, fallback, versioned prompts
mcp_server/   MCP tools
rag/          embedders, ChromaDB store, hybrid retriever
shared/       frozen contracts: ABCs + dataclasses
telemetry/    token and latency metrics
tests/        56 unit tests
main.py       CLI entry point
```

## Team (Group C)

| Package | What | Owner |
| --- | --- | --- |
| `ingestion/`, `rag/` | PDF to section-aware chunks to hybrid retrieval | Sanith |
| `shared/`, `agents/orchestrator*`, `app_context.py`, `telemetry/` | contracts, DI, agent loop | Gagani |
| `llm/`, `agents/*_agent.py`, `api/static/` | LLM adapter + fallback, four specialist agents, web UI | Dumindu |
| `evaluation/`, `api/`, `mcp_server/`, CI | metrics, runner, REST + MCP surfaces | Kaarthi |

## Video

<!-- TODO: unlisted YouTube link -->

## Ethics

See [ETHICS.md](ETHICS.md): information-not-advice, as-of dating, abstention
over fabrication, traceability, no personal-data ingestion. Every answer
carries the disclaimer that this system provides information about the Act,
not legal advice.
