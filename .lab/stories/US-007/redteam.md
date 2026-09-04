# Red Team Report

## Confirmed defects

None remain reproduced in the final release path.

## Suspected defects

None in the locally and publicly exercised release path. Provider authentication and non-Linux
hosts remain unobserved rather than presumed successful.

## Missing tests

- Human visual review in the exact terminal and display used for the presentation.
- Live provider checks for Claude Code, OpenCode, and Ollama; their deterministic subprocess
  contracts are covered, but credentials and models are deliberately not bundled.
- Windows and macOS host checks.

## Design concerns

- The container correctly reports `Codex CLI · DELAYED` because the host executable is not mounted.
  Presentation narration should explain that Docker contains the Lab, not the operator's
  authenticated harness.
- Local pre-Lab history is ignored rather than deleted. This preserves the operator's files while
  ensuring they cannot enter the public repository accidentally.
- The final completion gate remains a human decision. Publication must not be treated as permission
  for the system to approve itself.

## Areas tested without finding a defect

- Public commit `8a4422e` reached `Solensi/catfish-lab`; GitHub run `33874097926` passed Docker and
  both Python matrix jobs.
- The Node 20 deprecation annotations from that run are addressed with maintainer-current checkout
  v7 and setup-uv v10.0.1 commits, each pinned to its resolved SHA.
- The modal-transition regression and existing case-files interaction passed five consecutive
  targeted runs. Ruff, all 72 tests, `lab doctor`, and strict MkDocs then passed together.
- Buildx 0.36.1, the digest-pinned images, `uv sync --locked`, container doctor, container Logbook,
  source distribution, and wheel checks passed during the release audit.
- The staged public product excludes unrelated prototype history, credentials, generated caches,
  and transient run records. A host project may explicitly include its own `archive/` source.
