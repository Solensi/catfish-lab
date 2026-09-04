# Harness Proxy Protocol

The Logbook is the human interface; the CLI is the narrow machine interface used by the surrounding
coding harness. Model-only role actions can run directly from the TUI. Repository-tool operations,
external results, and deliberately proxied work remain discoverable without making a person
translate them into orchestration commands.

## The loop

```text
human types request in Logbook
             │
             ▼
request.md + story_created ledger event
             │
       human presses a
             ▼
action_requested ledger event ──► selected model harness runs directly when possible
             │
             ▼
external harness reads `lab inbox --json` when repository tools are required
             │
             ▼
role artifact + sealed run + narrated Logbook update
```

Start every harness turn with:

```bash
uv run lab init
uv run lab inbox --json
```

The JSON envelope has `schema_version` and explicitly queued `stories`; an empty list means the
harness has no authority to act. Each queued story exposes its ID, title, stage, depth, original
request path, current valid actions, pending requested action, gates, and artifact flags.
After a final assessment is sent back, `feedback` also provides the human's reason and durable
artifact path. That feedback is authoritative remediation context, not optional commentary.
The complete prompt is deliberately not copied into JSON or a ledger prompt field; only its short
display title is exposed. Read `request_artifact` from disk for authoritative wording.

`requested_action` is pending only while its `action_requested` event is the latest event for that
story. Completing the command writes a newer role, artifact, or approval event and naturally clears
the request. Repeated presses of `a` do not duplicate an identical pending event.

Use `lab inbox --all` only for human diagnostics. It includes idle history and is deliberately not
the default agent context. An initialized external project can point any harness at the standalone
`.lab/HARNESS.md` contract; Catfish's own repository uses the equivalent root `AGENTS.md`.

For non-interactive admission, use one of:

```bash
uv run lab request --prompt "Investigate why cold starts fail and make setup reliable"
uv run lab request --file brief.md --title "Portable cold starts"
printf '%s' "Audit the evidence trail" | uv run lab request
```

The command prints only the allocated story ID. `--file` is the preferred path for multiline or
non-ASCII briefs. Requests default to the LIGHT workflow; pass `--depth full` when uncertainty
deserves hypotheses, blind proposals, and an experiment.

## Human authority

The proxy must not execute approval commands just because they appear under `next_actions`. In the
interactive Logbook, `a` opens a dedicated yes/no gate and records the approval directly. A harness
may invoke `lab approve` only when the human explicitly authorizes it through its own trusted UI.
Likewise, only a human may reject a final assessment; the proxy must address its `feedback` before
claiming implementation again.

## Failure behavior

If a requested command fails, report the failure without manufacturing a completion event. Native
model invocation failures are recorded automatically. Other proxies must run `lab delay STORY
--reason "concise diagnostic"`; the pending request then remains visible and the Logbook marks the
story `DELAYED`. Diagnose with `lab status STORY`, inspect the cited artifact, and preserve useful
failure output as evidence when the workflow calls for it.
