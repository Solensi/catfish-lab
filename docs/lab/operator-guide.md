# Catfish Lab Operator Guide

Catfish Lab coordinates isolated model roles through files. Roles do not share memory, and model
confidence is never treated as evidence. The human operating the Lab remains the final authority.

## Install and inspect

```bash
uv sync
uv run lab init
uv run lab doctor
uv run lab logbook
```

`init` creates only missing files, including `.lab/project.md`: the concise charter every role sees.
`doctor` checks configuration, schemas, stories, context denials,
the evidence chain, and capsule isolation. In the interactive Logbook, select a story and then any
role to inspect its artifact or waiting contract.

The default context in `.lab/config.yaml` covers common Python, JavaScript/TypeScript, Rust, Go,
Java, documentation, test, app, library, and package layouts. Edit `context.include_globs` for a
different repository shape and keep `security.deny_globs` conservative. Binary files, build output,
dependency trees, archives, secrets, environments, and Git internals stay outside role prompts;
`context.max_bytes` caps each assembled view.

The ordinary human path needs no workflow command memorization: press `n` in the Logbook, describe
the work, submit it, and press `a` once inside the resulting story. The Product Steward scopes the
durable request, consecutive text roles run automatically, and repository changes become a visible
handoff to the surrounding harness. See [Harness Proxy Protocol](harness-proxy.md).

### Docker setup

```bash
docker compose build
docker compose run --rm lab init
docker compose run --rm lab logbook
```

The repository is mounted at `/workspace`, so stories and evidence remain on the host. The image does
not bundle Codex credentials or another model runtime; use deterministic `--fake` runs in the container
or connect a deliberate harness adapter. On Linux, set `LAB_UID` and `LAB_GID` in your shell if your
Compose installation needs an explicit host-user mapping.

## Start and run a story

```bash
uv run lab request --file brief.md
# or create a manually scoped/lightweight story:
uv run lab new-story --title "Observable outcome" --depth full
uv run lab run scientist US-004 --harness
uv run lab run architect US-004 --harness
uv run lab run heretic US-004 --harness
```

Use `light` for a small change that does not need competing proposals. Use `full` when uncertainty
or design choice warrants the complete experiment. Each role call is fresh and text-only. The
controller supplies allowlisted context, validates the output, writes the artifact, records metadata,
appends a ledger event, and updates deterministic state. `--fake` is for workflow testing.

The CLI refuses roles at illegal stages. Follow the workflow rather than editing `story.yaml`.

## Complete the experimental middle

After both blind proposals, record the supporting artifacts explicitly:

```bash
uv run lab draft critique US-004
# edit the printed path, then:
uv run lab record critique US-004 --from .lab/stories/US-004/drafts/critique.md
uv run lab draft experiment US-004
uv run lab record experiment US-004 --from .lab/stories/US-004/drafts/experiment.md
uv run lab approve experiment US-004
uv run lab record evidence US-004 --from results.json
uv run lab draft decision US-004
uv run lab record decision US-004 --from .lab/stories/US-004/drafts/decision.md
uv run lab approve implementation US-004
```

The imported critique, experiment, and decision must follow their templates. Evidence may be any
nonempty UTF-8 file up to 2 MB. Existing destinations are never silently overwritten. `lab status`
always prints the next valid command.

## Human gates

```bash
uv run lab approve experiment US-004
uv run lab approve implementation US-004
uv run lab approve done US-004
```

Approval is an explicit action, never a phrase inferred from chat. Submitting a LIGHT request is the
explicit authority for that bounded implementation. FULL work still requires a separate
evidence-backed implementation decision. A done approval never substitutes for trial evidence.

## Review and remediation

```bash
uv run lab run redteam US-004 --harness
uv run lab request-changes US-004 --reason "The documented keyboard path does not work"
uv run lab reopen US-004 --to implementation --reason "Reproduce and repair finding RT-1"
uv run lab trial US-004 --harness
```

`request-changes` is the human rejection route for a completed assessment. It requires a reason,
preserves the superseded implementation/review/trial under `evidence/`, records human feedback,
and queues the Builder. Generic `reopen` remains the controller/operator repair tool for a Red Team
or trial finding. The Logbook connects preserved findings and human feedback to the response.

## Archive

```bash
uv run lab index-evidence US-004
uv run lab archive US-004 --harness
```

The deterministic index gives the Archivist artifact paths, hashes, story state, matching ledger
events, and chain status. The Archivist writes a sourced history; it cannot create missing evidence.

## Quality gate

```bash
uv run ruff check .
uv run pytest tests/test_lab_*.py
uv run lab doctor
uv run lab logbook US-004 --snapshot
```

## Recovery rules

- If `doctor` reports a broken chain, preserve the file and investigate; never rewrite history.
- If a role produces malformed output, correct its prompt/template or rerun it fresh.
- If review finds a defect, use `reopen` so the report is preserved rather than silently overwritten.
- If a role is WAITING, inspect it in the Logbook, then check the story stage with `lab status`.
- If work is DELAYED, read its live diagnostic and resolve the provider or proxy blocker; do not
  mistake delay for a completed transition.
