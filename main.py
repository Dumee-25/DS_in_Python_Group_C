from app_context import AppContext
from shared.contracts import AgentState


def _print_result(state: AgentState, snapshot_date: str) -> None:
    if state.verdict == "abstain":
        print(f"\n{state.draft}")
        return

    print("\nRetrieved passages:")
    for c in state.retrieved:
        preview = c.text[:100].replace("\n", " ")
        print(f"  [{c.section}] ({c.source_doc}, score={c.score:.2f}) {preview}...")

    print(f"\nAnswer:\n{state.draft}")

    for note in state.temporal_notes:
        print(f"\n!! {note}")

    print(f"\n(As of corpus snapshot {snapshot_date}. This is information "
          f"about the Act, not legal advice.)")


def main():
    ctx = AppContext()
    print("PDPA Agent — ask about Sri Lanka's Personal Data Protection Act "
          "(Ctrl+C to exit)")
    while True:
        try:
            query = input("\n> ").strip()
        except (KeyboardInterrupt, EOFError):
            print()
            break
        if not query:
            continue
        state = ctx.orchestrator.run(AgentState(query=query))
        _print_result(state, ctx.settings.snapshot_date)


if __name__ == "__main__":
    main()
