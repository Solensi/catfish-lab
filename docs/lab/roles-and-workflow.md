# Roles and Workflow

All roles may use the same model. Independence comes from fresh sessions, distinct instructions,
restricted context, different outputs, and incompatible incentives.

| Order | Role | Responsibility | Primary artifact |
|---:|---|---|---|
| 1 | Product | Frame value, scope, and observable acceptance criteria | `story.md` |
| 2 | Scientist | Convert uncertainty into a falsifiable hypothesis | `hypothesis.md` |
| 3 | Architect | Commit to a conventional, maintainable proposal | `candidates/A.md` |
| 4 | Heretic | Challenge assumptions with an independent alternative | `candidates/B.md` |
| 5 | Builder | Implement only the human-authorized direction | `implementation.md` |
| 6 | Red Team | Seek reproducible violations and missing tests | `redteam.md` |
| 7 | Judge | Test DONE criterion by criterion | `trial.md` |
| 8 | Archivist | Produce a cited experimental history | `archive.md` |

Architect cannot see Candidate B; Heretic cannot see Candidate A. Red Team receives implementation
and repository evidence, not Builder conversation. Judge is a fresh run and cannot be Builder.
Archivist receives finalized Markdown plus a deterministic evidence index.

## Where the documents live

Every case owns one durable directory: `.lab/stories/US-NNN/`. The paths in the table above are
relative to that directory, so the Red Team artifact for US-007 is
`.lab/stories/US-007/redteam.md`. Recorded experiment evidence lives under `evidence/`; superseded
reviews are preserved there rather than overwritten without trace.

Inside the Logbook, select the story and press `e` to browse all READY and WAITING case files with
their exact paths. Use `j`/`k` and Enter to open one. Outside the TUI, run `lab files US-NNN`.

Technical roles receive the active `lab/**/*.py` implementation, Lab tests, package metadata,
container/CI configuration, and handbook. Blind proposal paths remain denied even when the active
repository is visible. Catfish does not reserve a generic `archive/` path in projects it attaches to;
operators may include such a directory when it contains relevant project source.

## Full-depth sequence

```text
story → hypothesis → blind proposals → critique → experiment ready
      → evidence → human decision → implementation → red team
      → completion trial → human approval → done → archive
```

The eight roles produce the primary narrative artifacts. Critique, experiment definition, raw
evidence, and human decision are supporting workflow artifacts rather than invented ninth-role output.
Record completed material with `lab record KIND STORY --from FILE`; the controller hashes it, appends
an event, and advances only from the correct stage. Templates and state fields alone never prove a
stage ran.

## Light-depth sequence

A submitted light request records the user's bounded implementation authority and proceeds from
scope to the tool-capable Builder handoff without competing proposals or a duplicate approval.
Manually created stories still ask for implementation authority. Red Team, Judge, and final human
acceptance remain separate.

## READY and WAITING

The Logbook always displays all eight roles. READY means the expected artifact exists. WAITING means
it does not. READY does not imply correctness, approval, or completion; those claims require state,
review, trial evidence, and human gates.
