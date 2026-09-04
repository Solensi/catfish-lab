# Architecture

Catfish Lab separates deterministic orchestration, isolated model invocation, durable artifacts,
and human authority.

```text
Human in Logbook                 coding harness
      │ request + explicit gates       │ `lab inbox --json`
      └──────────────┬──────────────────┘
                     │ CLI protocol
      ▼
Lab Controller ── allowlisted context ──► fresh Model Adapter
      │                                      │ text only
      │ validates response                   ▼
      ├── story artifact ◄────────────── role response
      ├── run record
      ├── integrity-linked ledger event
      └── deterministic state update
                  │
                  ▼
          Logbook / Archivist
```

## Code map

- `lab/cli.py`: user and harness commands.
- `lab/controller.py`: stages, gates, contracts, validation, run records, and state updates.
- `lab/context.py`: role allowlists and deny rules.
- `lab/capsule.py`: isolated context materialization and digest.
- `lab/roles.py`: role-to-artifact, template, and context mapping.
- `lab/model.py`: vendor-neutral protocol and fake/Codex adapters.
- `lab/harnesses.py`: persistent provider profiles plus Claude, OpenCode, and Ollama adapters.
- `lab/artifacts.py`: validated story state persistence.
- `lab/ledger.py`: serialized writers and event hash chain.
- `lab/archive.py`: story evidence indexes.
- `lab/logbook.py`: evidence interpretation and automation-safe snapshots.
- `lab/tui.py` + `lab/logbook.tcss`: interactive requests, gates, live analysis, and role drill-down.
- `lab/tutorial.py`: disposable first-run instruction using the production workflow.
- `lab/doctor.py`: deterministic installation audit.

## State versus evidence

`story.yaml` says where the workflow is. Role Markdown says what a role reported. Run JSON says how
an invocation was constructed. The ledger says which interactions were recorded and in what order.
None substitutes for another.

## Isolation

Role policies allowlist files and deny environment, credential-like, secret-like, and Git paths.
Codex runs use a fresh temporary directory, empty inherited environment, read-only sandbox, disabled
network and tools. Claude runs one tool-disallowed print turn from an empty directory. OpenCode runs
in pure mode from an empty directory with every tool permission denied. Ollama receives only the
assembled request over its configured endpoint. A response is data until validated and stored.

## Product boundary

The public repository, package, container image, handbook, and CI contain only Catfish Lab. Earlier
unrelated prototype material is kept outside Git, so a first-time contributor never has to decide
which Catfish is current. An attached project may still use its own `archive/` directory: that name
is not globally denied by the context engine.
