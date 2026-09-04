# Contributing to Catfish Lab

Start by opening the Logbook and creating a story. This keeps the proposed change visible before
it becomes code.

```bash
uv sync
uv run lab init
uv run lab doctor
uv run lab logbook
```

Use a second terminal for the work. Keep changes scoped to the story, keep secrets out of Lab
artifacts, and record approvals through the CLI. A claim is not evidence: include the command,
result, and relevant artifact path for deterministic checks.

Before opening a pull request:

```bash
uv run ruff check .
uv run pytest tests/test_lab_*.py
uv run lab doctor
uv run lab index-evidence US-NNN
```

Pull requests should name the story ID, summarize observed evidence, identify remaining uncertainty,
and state which human gates have actually been recorded. Never mark an approval on another person's
behalf.

Use the issue forms for reproducible defects or bounded proposals. Security concerns follow
[`SECURITY.md`](SECURITY.md), not the public issue tracker.
