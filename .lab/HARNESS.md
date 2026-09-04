# Catfish Lab Harness Guide

This file is the portable handoff contract for any tool-capable coding agent working in this project.

1. Run `lab init`, then read `lab inbox --json`.
2. Act only on a story's `requested_action`; an empty `stories` list means nothing is queued.
3. Read its `request_artifact`, `.lab/project.md`, `.lab/constitution.md`, and cited artifacts.
   If the inbox includes `feedback`, its reason and artifact are required remediation context.
4. Perform repository edits and deterministic checks with your normal tools. Text-only Lab roles must
   never pretend that a patch was applied.
5. Report a blocker immediately with `lab delay US-NNN --reason "concise diagnostic"`.
6. Re-read the inbox after each action. Continue only within the user's request and stop at every
   human approval gate.
7. Before a completion claim, run the project's checks, `lab index-evidence US-NNN`, and `lab doctor`.

Never place secrets, credentials, private prompts, or hidden conversational state in Lab artifacts.
The ledger and sealed artifacts are authoritative; Logbook narration is a derived reading aid.

OpenCode users may launch this repository's bundled tool-capable proxy with
`opencode --agent catfish .`; its instruction lives at `.opencode/agents/catfish.md`.
