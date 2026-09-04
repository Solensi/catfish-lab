# Interactive Role Visibility and Documentation

## User observation

Roles other than those with recent ledger events were invisible, most system behavior lacked
approachable documentation, and the Logbook offered no path from summary into deeper material.

## Implemented behavior

- Story views always list Product, Scientist, Architect, Heretic, Builder, Red Team, Judge, and
  Archivist with READY/WAITING state, purpose, and expected artifact.
- Interactive overview supports `j`/`k`, Enter, and numeric quick selection.
- Story view supports numeric role selection.
- Role detail pages through the complete artifact when READY or the role contract when WAITING.
- Help, back, refresh, and quit controls are available without modifying Lab state.
- POSIX input is unbuffered and Windows uses its native console key reader.
- Compact interactive pages fit ordinary terminals; detailed evidence reports remain available in
  snapshots.
- Six linked documents cover operation, roles/workflow, architecture, evidence, Logbook behavior,
  adapters, and CLI semantics.

## Observed verification

- An actual pseudo-terminal session opened US-003, selected the waiting Scientist, displayed both
  pages of its contract, returned to the story, processed a burst of keys, and restored the terminal.
- The full suite passed 54 tests after interactive navigation and documentation were added.
- Ruff reported no violations.

## Evidence boundary

WAITING exposes absence; it does not synthesize a role opinion. A role appears as READY only when its
artifact exists. Running roles remains a separate, stage-gated CLI action.

## Isolated role exercise

After the visibility work, three genuine Codex-backed roles ran through the Lab controller:

- Scientist produced `hypothesis.md` and advanced the story to HYPOTHESIS.
- Architect produced `candidates/A.md` while Candidate B was forbidden.
- Heretic produced `candidates/B.md` while Candidate A was forbidden.

The first proposal pair revealed that technical roles could inspect legacy application code but not
`lab/**/*.py`. The context contract was corrected to include Lab code, Lab tests, operator docs, and
package metadata while retaining mutual proposal denial. Architect and Heretic were rerun as fresh
blind roles. The Logbook now preserves the earlier event seals as changed and quotes only the latest
matching artifacts.

Architect recommends a conventional shared projection and conformance suite. Heretic recommends
immutable content-addressed role outputs behind the mutable working paths. No direction was selected:
US-003 remains at PROPOSALS with every human gate false.
