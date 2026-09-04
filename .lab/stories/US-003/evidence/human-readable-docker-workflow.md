# Human-readable Structure, Docker, and Workflow Repair

## User observation

The repository assumed too much prior knowledge, absent artifacts might indicate an incomplete
workflow, setup was not containerized, and the Logbook needed a real-time situation view without
losing its distinctive role narration.

## Implemented behavior

- `START_HERE.md`, `docs/README.md`, the root repository map, and per-story READMEs provide layered
  entry points for newcomers.
- The legacy game package and specification are visibly marked as archived without deleting history.
- `Dockerfile`, `compose.yaml`, and `.dockerignore` provide a host-mounted Lab CLI environment.
- The cast is written as the Product Steward, the Scientist, the Architect, the blind Heretic, the
  Builder, the Red Team, the Judge, and the Archivist.
- Pressing `l` opens a feed that polls and repaints as evidence-bearing ledger interactions arrive.
- The supporting critique, experiment, raw evidence, and decision artifacts are visible separately
  from role output.
- `lab draft` creates editable supporting templates without advancing state.
- `lab record` validates, imports, hashes, records, and advances completed supporting artifacts.
- Experiment, implementation, and done approvals now enforce their required stage artifacts; done
  also requires a READY completion-trial verdict.
- `lab status` reports the next valid command.

## Why missing role artifacts remain visible

The code now distinguishes absence from failure. A role artifact is READY only after that role has
actually completed. Before then, the Logbook shows WAITING and lets the operator open the role
contract. It never manufactures prose merely to make the pipeline look populated.

US-003 legitimately has READY artifacts for the Product Steward, Scientist, Architect, and blind
Heretic. Builder and later review roles remain WAITING because no implementation decision has been
approved. The formerly unreachable middle workflow now has explicit commands.

## Observed verification

- An actual pseudo-terminal opened the new real-time feed, displayed matching sealed Architect and
  blind Heretic reports, processed a burst `lq`, and restored the terminal.
- The full suite passed 60 tests before the final state-display refinement.
- Ruff reported no violations.
- `lab status US-003` reported `lab draft critique US-003` as the next action.
- Compose YAML and Dockerfile build inputs were parsed and structurally checked.

## Unobserved evidence

Docker is not installed in the current environment, so an actual image build and container session
remain unobserved. The configuration must run in Docker-capable CI or on the future GitHub host before
that claim can be promoted to observed evidence.
