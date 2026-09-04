# Completion Trial

Story: US-007

## Acceptance Criterion 1 — the main case text is keyboard-readable

Verdict: PASS

Evidence: the Logbook labels the pane route; Tab or Right focuses `CaseScroll`, `j`/`k` and arrows
scroll it, and Left returns to `StoryList`. A headless test verifies positive scroll position and an
unchanged active story.

## Acceptance Criterion 2 — rejecting an assessment requires a reason

Verdict: PASS

Evidence: final Advance exposes **Send back [r]**, which opens a focused feedback prompt. Both the
controller and UI refuse empty feedback. The CLI equivalent requires `--reason`.

## Acceptance Criterion 3 — feedback reaches remediation rather than disappearing

Verdict: PASS

Evidence: rejection writes a hashed `evidence/human-feedback-*.md`, preserves superseded work,
resets its claims, and makes the next action `lab run builder STORY --harness`. `lab inbox --json`
exposes the feedback reason and artifact path, and the Builder can read that feedback document.

## Acceptance Criterion 4 — evidence narration remains attributable

Verdict: PASS

Evidence: Live Analysis attributes `assessment_rejected` to the human, quotes the reason, and checks
the feedback artifact's recorded SHA-256. Case files discovers feedback and superseded artifacts.

## Acceptance Criterion 5 — the public product is one comprehensible Lab

Verdict: PASS

Evidence: the staged repository excludes the unrelated game prototype and 2.1 MB demo image without
deleting the local history. README, architecture, contribution, harness, and improvement-chart copy
now describe one Lab-only clone. Catfish no longer globally denies a host project's own `archive/`
path, and a regression test proves an explicitly included archive document reaches technical roles.

## Acceptance Criterion 6 — setup and release checks are reproducible

Verdict: PASS

Evidence: the launch guide covers official Arch GitHub CLI, Docker, Compose, and Buildx packages;
native and container verification; local Git identity; authentication; push; and Actions. The
Dockerfile pins Python and uv image digests and enforces `uv.lock`. Ruff, 71 tests, doctor, strict
MkDocs, source/wheel builds, Buildx, container doctor, and container Logbook checks pass.

## Red Team Findings

No requested defect was reproduced. Live release testing exposed and resolved the missing Buildx
plugin, ignored lockfile, mutable image inputs, oversized unrelated initial history, and a residual
product-specific context denial. Remaining uncertainty is bounded to human visual review,
unavailable host/provider combinations, and GitHub Actions, which cannot run before push.

## Overall Verdict

READY

## Missing Evidence

- Human visual review on the presentation terminal.
- Authenticated push and the first GitHub Actions result.
- Live Windows, macOS, Claude, OpenCode provider, and Ollama checks.
