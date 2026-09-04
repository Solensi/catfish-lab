# Disposable Logbook Demonstration

## Objective

Provide a single command that shows the entire Lab performing without requiring model credentials,
changing production code, or contaminating the repository's real evidence.

## Implemented behavior

- `lab demo` creates a temporary repository and opens directly in the real-time feed.
- Fifteen timed actions move one synthetic story from Product framing through Scientist hypothesis,
  mutually blind proposals, critique, experiment, evidence, decision, approvals, implementation,
  Red Team review, completion trial, done approval, and archive.
- All actions use the real controller, fake deterministic model adapter, stage enforcement, artifact
  recording, SHA-256 ledger, evidence index, and Logbook.
- `--speed` controls the animation interval.
- `--snapshot` completes immediately and prints a CI/recording-friendly view.
- A persistent synthetic-demo banner and story title prevent confusion with production evidence.
- The temporary directory and its ledger are removed on exit.

## Defect discovered by the demo

The first end-to-end run proved why later roles had no artifacts in full stories. After Builder set
the stage to IMPLEMENTATION, the controller unconditionally noticed that both proposal artifacts
existed and reset the stage to PROPOSALS. Red Team could therefore never run.

The proposal-completion rule is now limited to Architect and Heretic runs. A regression test proves
that a full-depth Builder advances to IMPLEMENTATION even when both candidates exist.

## Observed verification

- `lab demo --snapshot` completed with 16 integrity-linked interactions, all 12 artifact flags, all
  three approvals, every role READY, stage DONE, and a sealed Archivist report.
- The suite passed 64 tests after demo coverage was added.
- Ruff reported no violations.
- An accelerated pseudo-terminal run visibly progressed from story creation through the Product
  Steward, Scientist, Architect, blind Heretic, supporting artifacts and gates, Builder, Red Team,
  Judge, and Archivist. The feed repainted in real time and restored the terminal on `q`.

## Remaining uncertainty

Docker execution remains unobserved because Docker is not installed in this environment.
