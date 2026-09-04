# Interactive Logbook

The Logbook is the Lab's human console. It admits plain-language work, exposes every role and
artifact, records explicit human gates, and asks the surrounding harness to perform deterministic
actions. It never pretends a queued request is completed work.

Its visual identity is deliberately small: one Catfish mark, a story rail, one readable case, and a
status line. Status and the next human action take precedence over decoration. Machine paths stay in
role detail and evidence reports instead of competing with the main workflow.

```bash
uv run lab logbook                 # interactive overview
uv run lab logbook US-004          # open one story
uv run lab logbook --snapshot      # plain output for CI/harnesses
uv run lab tutorial                # run the guided First Cast whenever you like
```

## Navigation

| View | Keys |
|---|---|
| Story rail | `↑`/`↓` or `j`/`k` selects a story and keeps it selected during live updates |
| Current case | Tab or `→` enters the text; `j`/`k` or arrows scroll; `←` returns to stories |
| Case actions | `a` advances work or opens an evidence-first human gate; `1`–`8` opens every role |
| Any view | `n` adds work; `e` browses case files; `h` switches harness; `l` opens live analysis |
| Evidence review | `j`/`k` or arrows scroll; Esc returns to the gate |
| Human gate | `e` reviews; `y` accepts; final `r` requires a reason and sends work back; Esc changes nothing |
| Dialog | Tab changes focus; Enter activates the focused control |

The Logbook is keyboard-first. Clicking remains supported for terminals that provide a mouse, but
every primary workflow is reachable without it.

## Case files

Press `e` from a selected story to open **Case files**. This browser lists every expected role and
workflow document as READY or WAITING, shows its exact repository path, and opens READY documents
with Enter. Navigate with `j`/`k` or arrows; Esc returns. Clicking remains available.

The durable directory is `.lab/stories/US-NNN/`. It contains the original request, role Markdown,
supporting experiment material, recorded evidence, preserved superseded trials, and the generated
evidence index. From an ordinary shell, `lab files US-NNN` prints the same discoverable index.

## Submit and advance work

Press `n`, enter any product, bug, research, documentation, refactoring, or maintenance request, and
press Enter. The Lab preserves the original words in `request.md`; the ledger stores only the short
display title, not a separate full prompt. The form defaults to LIGHT; select “Use the full
experimental route” (Tab then Space, or mouse) for the hypothesis, blind-proposal, and experiment
path. Use `lab request --file BRIEF.md` for a multiline brief.

Press `a` once inside a story. Consecutive text-only roles run asynchronously through the active
provider until the Lab reaches a real boundary. Repository changes become a visible **HANDOFF** to
the surrounding coding harness and appear in `lab inbox --json`; they are never simulated by a prose
patch. A human gate names the decision and initially focuses **Review evidence**. Press `e` to visit
the relevant source artifacts in one scrollable reading view, then `y` to accept and advance. Esc
returns without changing workflow state. Tab, Enter, and mouse remain equivalent alternatives.
Submitting a LIGHT request already records its bounded implementation authority, so the common path
does not ask the same question twice.

At the final completion assessment, **Send back [r]** asks what failed to earn acceptance. A blank
reason is refused. Catfish stores the response as `evidence/human-feedback-*.md`, preserves the
superseded implementation, Red Team report, and trial beside it, resets those completion claims,
and queues a new Builder handoff. The coding harness receives both the reason and its artifact path
through `lab inbox --json`.

The masthead always names the active harness. Press `h` for the Harness Bay, where readiness is
visible before selection. Provider failures and proxy blockers appear as red `DELAYED` notices and
mark the affected story until a later successful event clears the condition. The status line derives
the latest delay from the durable ledger, so restarting the Logbook cannot hide token exhaustion or
another provider diagnostic.

Interactive mode uses Textual widgets for focus, scrolling, keyboard, and mouse behavior, restoring
the terminal on exit. Redirected output automatically becomes one plain snapshot.

## Live analysis

Press `l` from the Logbook. Live Analysis polls the ledger and cited artifacts once per second and
repaints only when the evidence changes. It shows the latest evidence-bearing findings, their story,
and source integrity. Analysis opened with a selected story stays scoped to that story.
Press Esc to return.

## Story and role views

The story header shows stage, required-artifact progress, and explicit approvals. LIGHT uses five
required artifacts; FULL uses twelve. The pipeline always lists all
eight roles. READY means the expected file exists; WAITING exposes missing work rather than hiding
the role. Selecting READY opens the artifact. Selecting WAITING opens the role contract so an
operator can inspect its mission, context, rules, output, and failure conditions.

## Evidence cards

- `REPORTED` is the finding extracted from the most relevant Markdown section for that role.
- `SOURCE` is the repository-relative path plus integrity status.
- `MATCH` means current bytes equal the digest recorded with the run.
- `CHANGED SINCE RUN` means the artifact changed afterward.
- `LEGACY / UNSEALED` means older history lacks a contemporaneous content hash.

Reopening cards connect the preserved review finding to the controller's remediation response.
Summaries aid navigation; inspect the full artifact and reproduce tests before deciding.

## First-launch tutorial

The first interactive launch offers—not forces—the five-part **First Cast** against a temporary
synthetic repository. Enter accepts the invitation, `s` skips, and Space toggles the visible
**DON'T SHOW AGAIN** preference. Accepting opens a calm orientation inside the real
TUI; no ledger events begin until `b` starts the cast. The run unfolds at a readable pace. Space
pauses or resumes it, `j`/`k` scrolls, Esc exposes the roles, and `l` returns to Live Analysis.
`lab tutorial` remains available regardless of the saved preference. A banner prevents synthetic
success from being mistaken for project evidence; quitting removes the temporary workspace and
enters the real Logbook.
