# §IV Empirical Evaluation — results skeleton

<!-- TODO: runner fills the table; add method + failure analysis. -->

## Method

<!-- 5 metrics: correctness / citation F1 / faithfulness / relevancy / refusal
     accuracy. Judge model = fallback secondary (different from generator —
     self-preference bias). Manual agreement check: hand-scored 5 of 20,
     agreement = TODO. -->

## Results

| ID  | Question | Response (truncated) | Cit. F1 | Corr. | Faith. | Rel. | Refusal OK |
| --- | -------- | -------------------- | ------- | ----- | ------ | ---- | ---------- |

<!-- runner output pastes here — ≥10 rows required -->

**Summary:** mean correctness TODO · mean citation F1 TODO · mean faithfulness
TODO · mean relevancy TODO · refusal accuracy TODO/20

## Failure analysis

<!-- TODO: two case studies. For each: the failing item, the diagnosis
     (retrieval miss / routing loop / prompt grounding / bad gold),
     the fix, and the re-run delta. "F1 went 0.61 → 0.84 after X" is the
     strongest sentence available. -->
