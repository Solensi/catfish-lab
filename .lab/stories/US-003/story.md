# User Story

## Statement

As a developer or coding harness on a newly cloned repository
I want Catfish Lab to install independently and expose a live evidence-backed terminal Logbook
So that I can understand, operate, and audit the experiment from any ordinary terminal.

## User value

The Lab becomes the product rather than an accessory to the game prototype. A newcomer can discover
the workflow quickly, while reviewers can trace narrative claims back to durable records.

## Acceptance criteria

- [x] Default installation does not require the legacy Flet game runtime.
- [x] Supported Python versions include 3.11 through the current development version.
- [x] `lab logbook` live-renders story state and narrated ledger events without a web service.
- [x] `lab logbook --snapshot` is stable in a non-interactive harness or CI.
- [x] Logbook entries summarize what each role reported and cite the supporting artifact.
- [x] Overwritten legacy artifact paths are not presented as historical role conclusions.
- [x] New role outputs and preserved reviews carry content hashes for integrity comparison.
- [x] Every story view shows Product through Archivist as READY or WAITING.
- [x] Interactive users can open stories, inspect any role, page through artifacts or contracts,
  refresh live state, view help, navigate back, and quit without losing terminal state.
- [x] Operator, workflow, architecture, evidence, Logbook, adapter, and CLI documentation is linked
  from the project README.
- [x] A newcomer has a root `START_HERE.md`, documentation map, repository map, and per-story guide.
- [x] Dockerfile and Compose entry points support doctor, status, and interactive Logbook commands.
- [x] The Logbook provides an automatically refreshing real-time situation feed.
- [x] Missing critique, experiment, evidence, and decision transitions have usable draft/record CLI
  commands, without attributing supporting artifacts to a role that did not produce them.
- [x] `lab status STORY` prints the next valid operator action.
- [x] `lab demo` animates a complete, disposable synthetic story through every role and supporting
  artifact using production controller, ledger, gate, archive, and Logbook code.
- [x] Demo output is prominently marked synthetic and cannot modify the real Lab ledger.
- [x] New ledger events form a verifiable SHA-256 chain without rewriting legacy history.
- [x] Story creation, human approvals, role runs, and reopenings are visible as ledger events.
- [x] The Archivist receives deterministic Markdown and JSON evidence indexes with artifact hashes.
- [x] `lab doctor` reports ledger tampering.
- [x] Clone, contribution, harness, license, and GitHub CI documentation exist.
- [x] Automated Lab tests and lint pass.

## Out of scope

- Publishing or creating the remote GitHub repository.
- Removing the historical game package.
- Choosing or integrating another model vendor.
- Replacing explicit human approval gates.

## Unknowns

- Behavior on Windows terminals has not been observed in this environment.
- The CI matrix is configured but cannot be observed until the repository is pushed to GitHub.

## AI experiment required?

yes — integrity migration, narration truthfulness, and cross-version packaging are measurable.

## Notes

This story was created during the implementation session at the user's invitation to use the Lab
on itself. It is an honest contemporaneous record, not a claim that the full staged workflow ran
before implementation.
