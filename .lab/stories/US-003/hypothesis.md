# Hypothesis

## Observation

US-003 requires an independently installable Catfish Lab, a terminal Logbook backed by durable artifacts, SHA-256 integrity checks, Python 3.11 through the current development version, and passing automated tests and lint. The story marks these acceptance criteria complete, but that status is a claim until reproduced by deterministic checks. Windows behavior and hosted GitHub CI remain unobserved.

## Question

Can a fresh checkout, without the legacy Flet runtime, reproducibly pass its quality gates across supported Python versions while producing truthful Logbook views and detecting tampering in the new ledger chain?

## Hypothesis

For every configured supported Python version, a clean installation will succeed without installing the legacy Flet runtime; automated tests and lint will pass; snapshot Logbook output will cite existing, hash-matching role artifacts without representing overwritten legacy paths as historical conclusions; and modifying any event in the new SHA-256 ledger chain will cause `lab doctor` to report tampering.

## Independent variable

- Python version under test.
- Ledger state: intact versus one deliberately modified new-chain event.
- Logbook mode: non-interactive snapshot versus interactive terminal.
- Artifact condition: current artifact, preserved review, overwritten legacy path, or content with a changed hash.

## Dependent variables

- Installation exit status and resolved dependency set.
- Presence or absence of the legacy Flet runtime in the default environment.
- Test and lint exit statuses.
- Stability of repeated `lab logbook --snapshot` output.
- Accuracy of displayed role states, summaries, citations, and content hashes.
- `lab doctor` exit status and tampering diagnostic.
- Availability of documented interactive navigation actions.

## Controls

- The same repository revision and lockfile.
- A fresh isolated environment for each Python version.
- Fixed terminal dimensions and locale for snapshot comparisons.
- The same story fixture and intact ledger baseline.
- No web service or network dependency during Logbook checks.
- Identical commands and test inputs across runs.
- A disposable copy of evidence for tampering tests so canonical history is not rewritten.

## Evidence that would change our mind

The hypothesis is falsified if any configured Python version cannot install or pass the quality gates; the default installation requires Flet; repeated snapshots differ without an underlying state change; a displayed summary lacks an existing supporting artifact or matching hash; an overwritten legacy path is presented as a historical role conclusion; any role from Product through Archivist is omitted or lacks READY/WAITING state; or a modified new-chain ledger event is not reported by `lab doctor`.

Successful Linux or macOS results would not resolve the stated uncertainty about Windows. A configured GitHub Actions matrix would not demonstrate hosted CI success until an actual run is observed.

## Smallest useful experiment

1. Select the lowest and highest configured supported Python versions.
2. In fresh isolated environments, perform the documented default installation and verify that Flet is absent.
3. Run the repository’s automated tests and lint checks.
4. Run `lab logbook --snapshot` twice against unchanged US-003 state and compare outputs byte-for-byte.
5. Mechanically verify that every displayed artifact citation exists and that its SHA-256 hash matches its content.
6. Check that Product through Archivist each appear as READY or WAITING and that overwritten legacy paths are not narrated as historical conclusions.
7. In a disposable repository copy, alter one byte in a new-chain ledger event and run `lab doctor`.
8. Declare success only if all installation, quality, snapshot, citation, role-state, and tamper-detection criteria pass.

## Confounders

- Dependency caches may conceal missing or undeclared requirements.
- The phrase “current development version” may change over time and must be resolved from repository configuration at test time.
- Terminal width, locale, color settings, timestamps, and filesystem ordering may affect snapshot output.
- A test fixture may not exercise all legacy overwrite patterns.
- Editing JSON may make it syntactically invalid, testing parsing rather than hash-chain verification.
- Platform-specific terminal behavior may differ from the observed environment.
- Restricted network access may prevent dependency resolution without indicating a packaging defect.
