# Candidate Proposal

## Summary

**Observation:** The repository already separates the Lab controller, context resolver, ledger, Logbook, model adapters, product runtime, and tests.

**Recommendation:** Preserve those boundaries and add one deterministic US-003 conformance layer that tests installation, supported Python versions, snapshot truthfulness, artifact seals, role visibility, and ledger tamper detection through public CLI behavior. Keep the Logbook a read-only projection over story artifacts, run records, and the ledger; do not introduce a database, web service, or second history store.

## Core idea

Define a small conformance suite around three existing authoritative boundaries:

1. Packaging authority: `pyproject.toml` and `uv.lock`.
2. Evidence authority: role artifacts, run records, and `.lab/ledger.jsonl`.
3. Presentation boundary: `lab logbook --snapshot`.

The suite should create disposable repositories and invoke the installed `lab` command as an operator would. Snapshot rendering should receive an explicit rendering configuration for width, color, locale-independent ordering, and live versus snapshot mode. Evidence citations should be produced only from current artifacts whose SHA-256 matches a recorded seal.

## Assumptions

**Observation:** Default project dependencies exclude Flet; it appears only in the `legacy-game` optional dependency.

**Observation:** `pyproject.toml` currently declares `requires-python = ">=3.11"` and Ruff targets Python 3.11.

**Observation:** The ledger verifier checks sequence numbers, previous hashes, and record hashes, while `lab doctor` reports verifier failures.

**Observation:** The Logbook always renders Product through Archivist and labels absent artifacts `WAITING`.

**Inference:** The current module boundaries are sufficient; the remaining risk is incomplete end-to-end verification rather than a need for architectural replacement.

**Uncertainty:** The supplied evidence does not identify a finite highest supported Python version or demonstrate Windows and hosted GitHub Actions behavior.

## Architecture / behavior

Add a focused conformance-test module and CI matrix without changing the underlying evidence model.

- Packaging tests build and install the wheel in a clean environment, inspect installed distributions, and assert that Flet is absent from the default dependency closure.
- The Python matrix is generated from one explicit repository setting, such as a documented list in `pyproject.toml` or CI configuration. It must include 3.11 and every intentionally supported version through the selected development interpreter. Avoid interpreting the open-ended `>=3.11` declaration as proof that every future Python release is supported.
- Snapshot rendering remains in `lab/logbook.py`, but its deterministic inputs are explicit: fixed width, no ANSI styling, no clock reads, sorted stories, and ledger order for events.
- Add a structured snapshot model internally, containing story state, eight role states, report text, artifact path, current digest, recorded digest, and integrity status. Plain-text and interactive views consume that same model.
- A role report is quotable only when the artifact exists and its current SHA-256 equals the recorded `output_sha256`. Missing, changed, or unsealed artifacts receive diagnostic text and are never narrated as historical conclusions.
- Evidence-citation verification walks every evidence-bearing snapshot item and asserts that its repository-relative path exists and its digest matches.
- Ledger tamper tests operate on a disposable repository copy, change a valid field while preserving valid JSON, and assert that `lab doctor` exits nonzero with a hash-chain diagnostic.
- CI runs the same documented commands used locally: installation verification, tests, Ruff, snapshot conformance, and `lab doctor`. Platform-specific terminal tests may be added for Windows without changing core rendering semantics.

The dependency direction remains:

```text
artifacts + run records + ledger
              ↓
       structured Logbook model
          ↙             ↘
stable snapshot      interactive terminal
```

## Expected advantages

**Recommendation:** Reuse the existing deterministic core instead of adding another persistence or narration subsystem.

This keeps history authoritative in one place, makes snapshot and interactive modes agree, and allows most acceptance criteria to be tested without a model, network, or terminal emulator. Subprocess-level tests demonstrate the installed CLI rather than only internal helper behavior. A single declared Python matrix prevents documentation and CI support claims from drifting independently.

## Failure modes

- An unbounded Python declaration may still imply support for an interpreter never exercised by CI.
- Dependency caches may conceal undeclared dependencies unless installation tests use fresh environments.
- Snapshot tests may become brittle if they assert entire cosmetic output instead of semantic fields plus a small stable golden fixture.
- A tamper test that creates invalid JSON would test parsing rather than SHA-256 chain verification.
- Interactive terminal behavior can differ on Windows even when snapshot tests pass.
- A current artifact may legitimately differ after reopening; the view must show that change rather than quote it as sealed historical evidence.
- Hosted CI configuration remains a claim until an actual GitHub Actions run is observed.

## Cost / complexity

**Inference:** This is a moderate testing and small-refactoring change. The structured Logbook model adds one internal seam but removes duplicated reasoning between presentation modes. No new runtime service or mandatory dependency is required.

The main maintenance cost is updating the explicit Python matrix as supported versions change. That cost is preferable to an unverifiable open-ended compatibility claim.

## Testability

Before inspecting results, define success as all of the following:

- A clean default installation succeeds on the lowest and highest configured Python versions.
- The installed default environment contains no Flet distribution.
- `pytest`, `ruff check .`, and `lab doctor` exit successfully on an intact checkout.
- Two snapshot invocations over unchanged files are byte-for-byte identical.
- Product through Archivist appear exactly once as `READY` or `WAITING`.
- Every quoted role report cites an existing artifact with a matching SHA-256.
- A changed, missing, or legacy-unsealed artifact is not quoted as its historical conclusion.
- Changing one byte within a valid new-chain ledger event makes `lab doctor` exit nonzero and report ledger integrity failure.
- Interactive navigation actions remain covered by deterministic state/key-transition tests; platform terminal smoke tests are reported separately.
- Actual hosted CI and Windows outcomes are labeled unobserved until runs exist.

## What would falsify this proposal?

The proposal is falsified if the conformance suite requires a second source of truth, if snapshot and interactive views cannot share one evidence model without excessive coupling, if a clean supported interpreter cannot install and pass the gates, if Flet appears in the default environment, if repeated snapshots differ with unchanged inputs, if any displayed conclusion lacks a matching artifact seal, or if valid-JSON ledger tampering is not detected by `lab doctor`.
