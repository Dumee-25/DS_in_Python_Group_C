# Ethics Statement

## Information, not advice

This system explains the content of Sri Lanka's Personal Data Protection Act,
No. 9 of 2022 (as amended). It does not provide legal advice, predict the
outcome of any person's case, or draft legal documents. Questions seeking
advice about a specific situation are refused with a standard message that
directs the user to a qualified lawyer — this behaviour is enforced by the
orchestrator's intent gate and measured by the evaluation suite's refusal-
accuracy metric.

## As-of dating

The Act commences in stages, so "what the law says" is time-dependent. Every
answer carries the corpus snapshot date, and a dedicated Temporal Agent
annotates any cited provision that is not yet in operation as of that date.
The system never presents a not-yet-commenced provision as current law.

## Abstention over fabrication

A Verification Agent checks every draft answer at the claim level against the
retrieved statutory text, and deterministically rejects citations to sections
that were never retrieved. Drafts that cannot be grounded are retried within
a fixed budget and then refused. The system prefers saying "I can't answer
that reliably" to inventing an answer.

## Traceability

Every answer exposes the passages it was built from: the CLI prints retrieved
sections before the answer, and the API returns the full per-agent trace with
each response. Nothing the system asserts is unattributable.

## No personal data ingestion

The corpus consists solely of published legislation, gazettes, and regulator
guidance. The system does not ingest, store, or profile any individual's
personal data; user questions are processed in-session and only aggregate
telemetry (call counts, token totals) is retained.
