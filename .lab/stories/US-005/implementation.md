# Implementation

## Approved scope

Reduce the common Catfish Lab path without removing the full workflow, named roles, evidence model,
harness choice, or human authority. Add a polished, locally served handbook.

## Files changed

- Workflow and contracts: `lab/contracts.py`, `lab/artifacts.py`, `lab/controller.py`,
  `lab/workflow.py`, `lab/logbook.py`, and `lab/cli.py`.
- Packaging and portability: `pyproject.toml`, `uv.lock`, `Dockerfile`, `compose.yaml`, `.gitignore`,
  and `.github/workflows/ci.yml`.
- Human and harness guidance: `README.md`, `AGENTS.md`, `CAPABILITIES.md`, `mkdocs.yml`, and `docs/`.
- Behavioral coverage: `tests/test_lab_workflow.py` and `tests/test_lab_logbook.py`.
- Removed the redundant root `START_HERE.md`; the root README and handbook quickstart now own
  onboarding without a three-document loop.

## Patch

The LIGHT route now treats request submission as bounded implementation authority, reports progress
against five required artifacts, and distinguishes an actual tool-capable Builder handoff from a
text-only role response. One Logbook continuation runs consecutive isolated roles until a handoff or
gate. Request work no longer creates a blank `story.md` that looks like Product evidence.

The public surface now leads with value and fit, hides low-level workflow controls from default CLI
help without removing them, and serves a searchable Material for MkDocs handbook through `lab docs`
or the Compose `docs` service.

## Tests

- `uv run ruff check .` — passed.
- `uv run pytest -q tests/test_lab_*.py` — 53 passed.
- `uv run lab doctor` — passed.
- `uv run lab docs --build` — strict build passed.
- `compose.yaml` was parsed and its two service/port structure asserted successfully.
- Docker launch was not exercised because Docker is not installed on this host; the limitation is a
  recorded DELAYED event in the Logbook.
- Browser visual inspection was deferred at the user's direction because no browser backend was
  available; the user will inspect the served site locally.

## Remaining uncertainty

Real-world feedback may justify further reduction or a richer TUI framework. The current design
keeps render logic testable and avoids introducing a framework before that evidence exists.
