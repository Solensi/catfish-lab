# Catfish Lab State Directory

Schema version: 1

This directory is the Lab's durable workspace, not its Python implementation.

- `constitution.md` contains rules supplied to every isolated role.
- `config.yaml` defines context denials, human gates, and artifact conventions.
- `harnesses.yaml` selects Codex, Claude Code, OpenCode, or local Ollama for future role runs.
- `HARNESS.md` is the portable custom instruction for a tool-capable coding agent.
- `roles/` contains the isolated contract for each role.
- `templates/` defines required artifact structure.
- `stories/US-NNN/` contains story state, role artifacts, and preserved evidence.
- `runs/` contains local run metadata and is ignored by Git except for `.gitkeep`.
- `ledger.jsonl` is the append-only interaction ledger. New entries form a SHA-256 chain.
- `schema/` contains interchange schemas for harnesses and validation tools.

Do not hand-edit approvals or ledger history. Use `lab approve` for gates and `lab reopen` for
remediation. Story Markdown is intended for humans; `story.yaml` is authoritative workflow state.

See `docs/lab/operator-guide.md` for operation and `docs/lab/evidence.md` for the trust model.
