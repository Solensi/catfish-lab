# Harness Entry Point

Catfish Lab is the product. Treat this file as the custom instruction that connects a general-purpose
coding harness to the human-facing Logbook.

Read [`CAPABILITIES.md`](CAPABILITIES.md) first as the short checklist of features that must remain
coherent when the Lab changes.

## On every harness turn

1. Read `CAPABILITIES.md`, run `uv run lab init`, then read `uv run lab inbox --json`.
2. If a story has `requested_action`, perform that exact valid transition for the user. Otherwise,
   use `next_actions` only when the user has asked you to continue that story.
3. Read the story's `request_artifact`, `.lab/project.md`, `.lab/constitution.md`, and the relevant
   generated artifacts before acting. The original request is authoritative; a role may scope it but
   must not silently replace it. If the inbox includes `feedback`, read its artifact and treat the
   human's reason as required remediation context.
4. Narrate meaningful progress to the user while commands run. The Logbook will independently turn
   completed ledger events into its own evidence-backed account.
5. After an action, re-read the inbox. Continue through deterministic next actions within the user's
   requested scope. Stop at human gates; LIGHT request submission already records its bounded
   implementation authority, while FULL implementation and all final acceptance remain explicit.
6. If work cannot proceed, immediately run `lab delay US-NNN --reason "concise diagnostic"` so the
   user sees DELAYED in the Logbook. Do not leave failures stranded in terminal output.
7. Before claiming completion, run the repository's documented checks, `uv run lab index-evidence
   US-NNN`, and `uv run lab doctor`. Keep documentation, setup, behavior, and tests consistent.

## Prompt routing

The Lab accepts product ideas, bugs, investigations, refactors, documentation, portability work,
security review, and maintenance. The Product Steward turns plain language into acceptance criteria;
the Scientist identifies the uncertainty; the Architect and blind Heretic produce independent paths;
the remaining roles test, build, attack, judge, and archive the work. Do not skip a role merely
because the prompt is not a greenfield feature—adapt its responsibility to the work.

All requests default to light depth so small deliverables do not enter a research pageant. The user
can press Tab before Logbook submission or pass `--depth full` for the experimental path.

## Authority and safety

- Never infer a human approval from prose or a queued action. Request submission itself records only
  the bounded LIGHT implementation gate; every other gate requires `lab approve`.
- Preserve role isolation. Roles exchange repository artifacts, never hidden conversational state.
- Never place `.env`, credentials, secrets, or private recovery data in prompts, runs, or logs.
- Never invent absent role opinions or evidence. WAITING is a valid and visible state.
- The ledger and sealed artifacts are authoritative. Logbook narration is a derived interface.
- Use the active profile reported by `lab harness`; do not silently substitute a provider.

See [`docs/lab/harness-proxy.md`](docs/lab/harness-proxy.md) for the machine protocol and
[`docs/lab/operator-guide.md`](docs/lab/operator-guide.md) for the complete workflow.
