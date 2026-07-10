# Prompt iteration log

Prompts are versioned files: once a prompt is iterated it gets a `_vN`
suffix, the live version is pinned in `llm/client.py::ACTIVE_VERSIONS`, and
earlier versions stay in the repo as the iteration record. Switching a
version (for an A/B or a rollback) is a one-line change.

## synthesis

### v2 (2026-07-10) — bare citation keys
**Diagnosis (from the full-eval failure analysis):** models copy the context
line format into `cited_sections` — the context shows passages as
`[s.16] (pdpa_act_9_2022.pdf) ...`, and drafts came back citing
`"s.16 (pdpa_act_9_2022.pdf)"` or `"[s.16]"`. The verifier compares citations
against bare `Chunk.section` keys, so every decorated citation read as
fabricated, burned the bounded retry budget, and produced wrongful
abstentions (observed on the penalty-appeal question: three identical
rejections → abstain on a correct answer).

**Change:** an explicit output-format rule with a WRONG/RIGHT example pair —
bare keys only in `cited_sections`.

**Defence in depth:** the code-side normalisation (`agents/synthesis_agent.py`)
stays. The prompt reduces the failure at the source; the normaliser catches
whatever slips through.

**Measured (full 20-question eval, `results_v7_prompt_v2.md` vs
`results_v6_final.md`, same corpus and code):** refusal accuracy held at
20/20, citation F1 unchanged at 0.749, correctness 0.856 → 0.863,
faithfulness 1.00. No regression; the improvement is robustness at the
source rather than headline metrics, since the normaliser already masked
the failure downstream.

### v1 — original
Grounded-draft prompt: answer only from numbered context passages, cite
`[s.X]` inline, `INSUFFICIENT_CONTEXT` escape hatch, information-not-advice
rule, JSON output contract.

## verification / intent / judge_*

Still v1 (unversioned filenames). The verification prompt already demands
claim-by-claim support decisions; no eval failure has yet motivated an
iteration, so none was invented.
