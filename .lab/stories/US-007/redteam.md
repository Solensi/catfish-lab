# Red Team Report

## Confirmed defects

None reproduced in the final staged release path.

## Suspected defects

None in the locally exercised release path. Provider authentication and non-Linux hosts remain
unobserved rather than presumed successful.

## Missing tests

- Human visual review in the exact terminal and display used for the presentation.
- Live provider checks for Claude Code, OpenCode, and Ollama; their deterministic subprocess
  contracts are covered, but credentials and models are deliberately not bundled.
- Windows and macOS host checks.
- The GitHub Actions result cannot exist until the repository has been pushed.

## Design concerns

- The container correctly reports `Codex CLI · DELAYED` because the host executable is not mounted.
  Presentation narration should explain that Docker contains the Lab, not the operator's
  authenticated harness.
- Local pre-Lab history is ignored rather than deleted. This preserves the operator's files while
  ensuring they cannot enter the initial public commit accidentally.
- The final completion gate remains a human decision. Publication must not be treated as permission
  for the system to approve itself.

## Areas tested without finding a defect

- Buildx 0.36.1 resolved the digest-pinned Python 3.13 and uv 0.12.9 images.
- The Docker build executed `uv sync --locked --extra docs --no-editable`; container doctor and
  Logbook snapshot checks passed.
- Ruff passed; all 71 tests passed; `lab doctor` passed; MkDocs built in strict mode.
- The context-policy regression explicitly includes `archive/**/*.md` in an arbitrary project and
  proves it is no longer blocked by a Catfish-specific global deny.
- Source and wheel packages built successfully. The sdist contains the launch guide, Dockerfile, and
  OpenCode agent; the wheel contains the controller, TUI, and stylesheet; neither contains the
  ignored prototype tree or live `.lab` state.
- `git diff --cached --check` passed before the product-boundary changes; it must be rerun on the
  final staged index immediately before commit.
