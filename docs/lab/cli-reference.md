# CLI Reference

Run commands from the repository root. Both `lab` and `catfish-lab` console scripts point to the
same Typer application. `python -m lab` is equivalent.

| Command | Purpose | Durable effect |
|---|---|---|
| `lab init` | Create missing Lab structure | Adds missing files; never overwrites customization |
| `lab request [--prompt TEXT\|--file FILE] [--title TEXT] [--depth light\|full]` | Admit arbitrary work | Preserves the brief; LIGHT records bounded implementation authority |
| `lab new-story --title TEXT [--depth light\|full]` | Allocate the next story | Creates story files and a ledger event |
| `lab request-action STORY` | Queue its next action for the harness | Appends one deduplicated pending event |
| `lab inbox [--json] [--all]` | Expose explicitly queued work; optionally include idle history | None |
| `lab status [STORY]` | Show stages and human gates | None |
| `lab files STORY` | List READY and WAITING case documents with exact paths | None |
| `lab depth STORY light\|full` | Change early routing depth | Updates state and appends an event |
| `lab harness [NAME]` | List or select Codex, Claude, OpenCode, or Ollama | Selection appends a ledger event |
| `lab run ROLE STORY [--harness\|--fake\|--codex\|--from FILE] [--model ID]` | Invoke or import one isolated role | Writes artifact, run record, ledger event, and state |
| `lab delay STORY --reason TEXT` | Relay a proxy blocker to the user | Appends a DELAYED event |
| `lab approve KIND STORY [--yes]` | Record a human gate | Updates story state and appends a ledger event |
| `lab request-changes STORY --reason TEXT` | Reject a final assessment with actionable feedback | Preserves superseded work and queues Builder remediation |
| `lab draft KIND STORY` | Create an editable supporting template | Writes under the story's `drafts/` directory only |
| `lab record KIND STORY --from FILE` | Import completed workflow material | Stores, hashes, records, and advances it |
| `lab reopen STORY --to STAGE --reason TEXT` | Return rejected work for remediation | Preserves review, resets flags, and records the reason |
| `lab trial STORY [--harness\|--fake\|--codex]` | Run the completion Judge | Writes `trial.md` and advances to trial |
| `lab archive STORY [--harness\|--fake\|--codex]` | Run the Archivist | Indexes evidence and writes `archive.md` |
| `lab index-evidence STORY` | Regenerate citation maps | Writes Markdown and JSON evidence indexes |
| `lab logbook [STORY] [--live\|--snapshot]` | Submit, advance, and explore work | Interactive requests, action events, or approvals |
| `lab tutorial [--snapshot] [--speed SECONDS]` | Teach the workflow with a guided story | None; tutorial data is temporary |
| `lab docs [--build] [--host HOST] [--port PORT]` | Serve or build the handbook | `--build` writes the static `site/` directory |
| `lab doctor` | Audit deterministic invariants | None; exits nonzero on failure |

`ROLE` is one of `product`, `scientist`, `architect`, `heretic`, `builder`, `redteam`, `judge`, or
`archivist`. Prefer the dedicated `trial` and `archive` aliases for those final roles.

`lab request` reads a prompt from its option, a UTF-8 file, interactive input, or redirected stdin.
It defaults to light depth and prints the allocated ID. `lab inbox --json` is the stable integration
surface; see [Harness Proxy Protocol](harness-proxy.md).

Approval `KIND` is `experiment`, `implementation`, or `done`. LIGHT request admission records the
implementation approval directly; manually created LIGHT stories still need the command. Without `--yes`, an interactive
confirmation is required. Automation may use `--yes` only when it is executing a human's explicit
decision; a harness must never approve on its own authority.

`lab request-changes` applies only at the final trial gate and refuses an empty reason. It writes a
human-authored feedback artifact, preserves the old implementation, Red Team report, and trial,
and exposes a fresh Builder handoff through the inbox.

Record `KIND` is `critique`, `experiment`, `evidence`, or `decision`. These artifacts are not assigned
to one of the eight standing roles, so a human or deliberately configured harness prepares them. The
command refuses the wrong stage, empty or oversized input, missing headings, reserved evidence-index
names, and accidental overwrite. After the blind proposals, the ordinary sequence is:

```bash
lab draft critique US-004
# edit .lab/stories/US-004/drafts/critique.md
lab record critique US-004 --from .lab/stories/US-004/drafts/critique.md
lab draft experiment US-004
lab record experiment US-004 --from .lab/stories/US-004/drafts/experiment.md
lab approve experiment US-004
lab record evidence US-004 --from results.json
lab draft decision US-004
lab record decision US-004 --from .lab/stories/US-004/drafts/decision.md
lab approve implementation US-004
```

## Exit behavior

Invalid stages, missing human gates, bad story identifiers, malformed model output, context-policy
violations, adapter failures, and doctor findings produce a nonzero exit. Scripts should check the
exit code and preserve diagnostics rather than automatically retrying with weakened checks.

## Tutorial behavior

On the first interactive `lab logbook` launch, an invitation offers the tutorial. Space toggles
“Don’t show this invitation again,” persisted in the ignored
`.lab/tutorial-prompt-dismissed` marker. Running `lab tutorial` never changes that preference. The
tour uses deterministic fake role responses but the real controller, stage rules, approval logic,
artifact hashing, ledger, evidence indexer, and Logbook. Its story data never enters the repository's
actual `.lab/`. Redirected output emits the completed snapshot; `--speed` controls seconds between
events.
