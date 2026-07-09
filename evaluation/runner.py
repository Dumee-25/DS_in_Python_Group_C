"""Runs the eval suite end-to-end and emits the Report §IV table as markdown.

Usage: python -m evaluation.runner [--smoke]

Smoke mode (what CI runs): first 3 pairs against the dependency-free stub
context, deterministic metrics only — catches wiring breaks with no API keys.
Full mode: all pairs through the real AppContext + the three LLM judges.
"""
import argparse
import json
import statistics
from pathlib import Path

RESULTS_PATH = Path("evaluation/results.md")
NUMERIC_METRICS = ["f1", "correctness", "faithfulness", "relevancy"]


def main(smoke: bool = False) -> None:
    from evaluation.metrics import citation_f1, llm_judge, refusal_accuracy
    from shared.contracts import AgentState

    if smoke:
        from app_context import stub_context
        ctx = stub_context()
    else:
        from app_context import AppContext
        ctx = AppContext()

    pairs = json.loads(Path("evaluation/qa_pairs.json").read_text(encoding="utf-8"))
    if smoke:
        pairs = pairs[:3]

    rows = []
    for p in pairs:
        state = ctx.orchestrator.run(AgentState(query=p["question"]))
        row = {"id": p["id"], "question": p["question"],
               "response": state.draft[:120],
               "refusal_ok": refusal_accuracy(p["expected_behavior"], state.verdict)}
        if p["expected_behavior"] == "answer" and state.verdict == "grounded":
            row |= citation_f1(state.cited_sections, p["governing_sections"])
            if not smoke:
                context = "\n".join(c.text for c in state.retrieved)
                # judge_correctness.txt takes reference=, not gold=
                row["correctness"] = llm_judge(
                    ctx.llm, "judge_correctness", question=p["question"],
                    answer=state.draft, reference=p["gold_answer"])["score"]
                row["faithfulness"] = llm_judge(
                    ctx.llm, "judge_faithfulness",
                    answer=state.draft, context=context)["score"]
                row["relevancy"] = llm_judge(
                    ctx.llm, "judge_relevancy",
                    question=p["question"], answer=state.draft)["score"]
        rows.append(row)

    _write_markdown_table(rows)
    _print_summary(rows, smoke)


def _cell(row: dict, key: str) -> str:
    v = row.get(key)
    if v is None:
        return "—"
    if isinstance(v, bool):
        return "yes" if v else "**NO**"
    if isinstance(v, float):
        return f"{v:.2f}"
    return str(v)


def _write_markdown_table(rows: list[dict]) -> None:
    header = ("| ID | Question | Response (truncated) | Cit. F1 | Corr. "
              "| Faith. | Rel. | Refusal OK |")
    sep = "|---|---|---|---|---|---|---|---|"
    lines = [header, sep]
    for r in rows:
        q = r["question"][:60].replace("|", "/")
        resp = r["response"][:60].replace("|", "/").replace("\n", " ")
        lines.append(
            f"| {r['id']} | {q} | {resp} | {_cell(r, 'f1')} "
            f"| {_cell(r, 'correctness')} | {_cell(r, 'faithfulness')} "
            f"| {_cell(r, 'relevancy')} | {_cell(r, 'refusal_ok')} |")
    RESULTS_PATH.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"[runner] table written to {RESULTS_PATH}")


def _print_summary(rows: list[dict], smoke: bool) -> None:
    print("\n=== summary ===")
    for metric in NUMERIC_METRICS:
        values = [r[metric] for r in rows
                  if isinstance(r.get(metric), (int, float))]
        if values:
            print(f"mean {metric}: {statistics.mean(values):.3f}  (n={len(values)})")
    refusals_ok = sum(1 for r in rows if r["refusal_ok"])
    print(f"refusal accuracy: {refusals_ok}/{len(rows)}")
    if smoke:
        # Smoke gates on wiring, not quality: reaching here means the
        # orchestrator, contracts, metrics and dataset all still fit together.
        print("SMOKE OK")


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--smoke", action="store_true")
    main(ap.parse_args().smoke)
