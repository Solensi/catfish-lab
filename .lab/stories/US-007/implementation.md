# Implementation

## Approved scope

Prepare Catfish Lab for a public repository and a live presentation without publishing it: make the
Logbook calmer and reliable, make installed use honest across project types, remove archived-game
assumptions from active behavior, improve documentation/community health, and preserve every human
gate.

## Files changed

- `lab/tui.py`, `lab/logbook.tcss`, and `lab/logbook.py`: one component Logbook, source-linked live
  analysis, focused dialogs, provider switching, visible delays, synchronous rendering, and removal
  of the obsolete key-routing frontend.
- `lab/cli.py`, `lab/config.py`, `lab/context.py`, `lab/roles.py`, `lab/workflow.py`, `lab/doctor.py`,
  and `.lab/`: arbitrary-project initialization, portable harness instruction, queued-only inbox,
  configurable cross-language context, enforced denials, binary filtering, and consistent versioning.
- `README.md`, `docs/`, `CONTRIBUTING.md`, `SECURITY.md`, `SUPPORT.md`, `CODE_OF_CONDUCT.md`, and
  `.github/`: a coherent front door, presentation route, improvement chart, local handbook identity,
  and contribution templates.
- `pyproject.toml`, `uv.lock`, `Dockerfile`, `.dockerignore`, `.gitignore`, and CI: Lab-only packaging,
  a smaller dependency graph, lock-enforced container installs, clean source/wheel contents, and
  local/CI quality gates.
- Public-repository boundary: unrelated game-prototype history remains available locally but is
  ignored by Git, so clones contain one product instead of a 2.1 MB demo face and thousands of lines
  of unrelated design material.
- `tests/`: TUI lifecycle, realtime delay, portable initialization, queued inbox, cross-language
  context, deny-policy, and binary-filter coverage.

## Keyboard remediation

The presentation trial exposed three interaction regressions. Numeric role bindings had been added
after Textual compiled the application class, so `1`–`8` were inert. The one-second refresh loop reset
the story cursor to the newest case because highlighting a row did not update the active story. The
footer also called advancement “Continue” and live analysis “Reports,” obscuring both actions.

Role bindings now exist when the application class is created. Arrow keys and `j`/`k` update the
active story as soon as the cursor moves, and refreshes preserve that choice. Mouse input remains
available but is no longer the clearest route. User-facing copy consistently says **Advance** and
**Live analysis**. Regression coverage opens all eight roles, preserves a keyboard selection through
refresh, and proves the digits remain typeable inside the request form.

## Evidence-gate and tutorial remediation

The next presentation review found that the final gate was technically clickable but not a coherent
keyboard workflow. Advance now opens a dedicated human-decision screen. `e` visits the actual
gate-relevant source artifacts, `j`/`k` and arrows scroll them, Esc returns without mutation, and `y`
accepts the claim and advances. The evidence button receives initial focus, so Enter and Tab remain
clear alternatives; mouse support is secondary.

The First Cast no longer begins moving as soon as its invitation closes. A native orientation states
what is synthetic, what the visitor will see, and every relevant control. Nothing is produced until
`b` begins the cast. The default pace is slower and Space can pause or resume it while `j`/`k` reads.

Finally, the status line now reconstructs the latest DELAYED diagnostic from the durable ledger.
Token exhaustion and other provider failures therefore survive navigation and restart. Unexpected
adapter exceptions are also caught at the worker boundary and recorded as delay events rather than
disappearing with a dead thread.

## Case-file discovery

Role documents were stored correctly but hidden inside `.lab/` and discoverable mainly through
numeric shortcuts. `lab/casefiles.py` now provides one ordered index of expected role documents,
supporting workflow artifacts, generated evidence maps, and arbitrary recorded or preserved
evidence. The Logbook exposes that index with the global `e` key: `j`/`k` selects, Enter opens, and
every row and reading view shows the exact repository path. WAITING files remain visible instead of
disappearing. The public `lab files STORY` command provides the same index without launching a TUI.

## Presentation skin and OpenCode route

The pre-Logbook tutorial question now has the same identity as the application it introduces. It is
a bounded **FIRST CAST** poster with Catfish's teal/amber palette, a plain-language synthetic-run
disclosure, an explicit orientation step, and keyboard choices. The preference is shown as
`DON'T SHOW AGAIN OFF` or `ON ✓`, avoiding a terminal-dependent checkbox glyph. It remains fully
readable without ANSI color.

Textual's inherited light surfaces were also overridden for Input, Checkbox, Button, focus, cursor,
selection, and Footer states. That removes the isolated pale boxes while preserving keyboard focus
and color-independent borders.

OpenCode is now a fourth selectable text-role profile. Its adapter starts `opencode --pure run` in
an empty temporary directory, attaches the complete role brief, disables default plugins and
auto-update for the invocation, and globally denies tools. This is deliberately distinct from the
tool-capable outer proxy: the source distribution includes `.opencode/agents/catfish.md`, which can
drive queued repository work while respecting `.lab/HARNESS.md` and human gates. The handbook
documents authentication, model discovery, model pinning, both operating modes, and the rule that
credentials never enter Lab configuration or evidence.

## Reasoned rejection and split-pane reading

The final assessment is no longer a false binary between acceptance and silent retreat. **Send
back [r]** opens a focused reason field and refuses an empty response. The controller seals that
reason in `evidence/human-feedback-*.md`, moves the superseded implementation, Red Team report, and
trial into timestamped evidence, resets their artifact claims, and queues a new Builder handoff.
The inbox exposes both the reason and its source path, the Builder context allowlists the feedback,
and Live Analysis attributes it to the human.

The main case text is now a first-class keyboard pane rather than scenery beside the story cursor.
Tab or Right moves focus from the story rail into the case; `j`/`k` and arrows scroll the case without
changing stories; Left returns to the rail. A persistent pane label explains the route and a teal
focus border shows where navigation will act. The same ReviewScroll behavior remains available in
role, evidence, and analysis readers.

`docs/repository-launch.md` records the exact local Git, GitHub CLI, Docker, authentication, remote
creation, push, and post-push verification sequence. Its Arch setup includes the official Buildx
plugin after a live Compose build revealed the warning produced when that package is absent. Buildx
0.36.1 was then installed and verified. The initial environment audit found Git 2.55.0, no
functional repository metadata for Catfish, and no GitHub CLI or Docker executables; those became
explicit release prerequisites rather than silently skipped checks.

## Public product boundary

The final staged-release audit found that the locally preserved game prototype would dominate the
initial public commit even though it was excluded from packages and containers. `/archive/` is now
Git-ignored and removed from the release index without deleting the local files. Public-facing docs
describe a Lab-only clone rather than advertising absent history.

The audit also found a legacy product assumption in the generic context policy: `archive/**` was
always denied. That block is removed from both initialized configuration and role defaults. A
regression test configures `archive/**/*.md` in an arbitrary host project and proves that relevant
source can reach technical roles while security-specific denials still win.

## Patch

The tool-capable outer harness applied the changes directly to the repository. The working tree and
the path list above are the patch authority; this artifact does not pretend that a prose-only role
performed those edits.

## Tests

- `ruff check --no-cache .` — pass.
- `pytest -q` — 71 passed.
- `lab doctor` — pass.
- `mkdocs build --strict` — pass.
- `uv build --no-build-isolation --offline` — source distribution and wheel built from cached build
  dependencies; the wheel includes the OpenCode adapter and `logbook.tcss`, while the source
  distribution also includes `.opencode/agents/catfish.md` and excludes local history and live Lab
  state.
- Docker 29.7.2, Compose 5.5.0, and Buildx 0.36.1 — the release image built successfully from
  a digest-pinned `python:3.13-slim` base as `catfish-lab:local`. The Dockerfile copies a uv 0.12.9
  binary from its resolved image digest and runs `uv sync --locked`, so both build tools and Python
  dependencies are reproducible rather than tag- or resolver-dependent.
  `docker compose run --rm lab doctor` passed, and `docker compose run --rm lab logbook --snapshot`
  rendered the repository ledger and all seven stories from inside the container. The snapshot also
  surfaced the intentionally unavailable host Codex executable as `Harness: Codex CLI · DELAYED`,
  proving that provider delay remains visible while the containerized Logbook stays operational.

## Remaining uncertainty

The final TUI needs a human visual pass in the actual presentation terminal. macOS, Windows, Claude,
OpenCode authentication/provider execution, and Ollama are documented but not claimed as locally
exercised by this run. The OpenCode subprocess contract is covered with a controlled test.
