# ≋<°)))>< Catfish Lab

**A quality-control room for AI-assisted work.**

Tell the Logbook what you want built, repaired, investigated, or maintained. Catfish preserves the
request, gives each responsibility a clean context, hands real edits to your coding harness, attacks
the result, and leaves a source-linked record a human can inspect later.

> **Make the claim. Show the trace.**

Use Catfish when the work must remain understandable after the chat window disappears. For a throwaway
script, use your coding agent directly.

## Start after cloning

Choose one route. Neither needs an API key to open the Logbook or run the tutorial.

### Docker

```bash
docker compose build
docker compose run --rm lab logbook
```

### Python 3.11+ and uv

```bash
uv sync
uv run lab init
uv run lab doctor
uv run lab logbook
```

On first launch, Catfish offers an optional disposable tutorial. It waits at an orientation before
the synthetic run begins; pause it with Space and read with `j`/`k`. In the real Logbook, press `n`,
describe the outcome, then press `a` to advance. Press `l` for source-linked live analysis and `h`
to choose Codex, Claude Code, OpenCode, or local Ollama. Press `e` to browse every case document and
its exact path. Press Tab or → to enter the main case text, scroll with `j`/`k`, and press ← to
return to stories. At a final assessment, `r` sends the work back only after you provide a reason.
Outside the TUI, run `uv run lab files US-NNN` to locate the same documents.

## What happens to a request

```text
YOU ASK → THE STEWARD SCOPES → THE BUILDER HANDOFF
                              → THE RED TEAM ATTACKS
                              → THE JUDGE TESTS
                              → YOU ACCEPT
                              → THE ARCHIVIST REMEMBERS
```

That short **LIGHT** route is the default. **FULL** adds the Scientist, Architect, blind Heretic,
critique, experiment, and evidence-backed decision when uncertainty deserves the laboratory rather
than ceremony. The names are theatrical; the artifacts and approval gates are not.

## Attach Catfish to another project

Install this checkout as a tool, then initialize from the other project's root:

```bash
uv tool install --editable /path/to/catfish-lab
cd /path/to/your-project
lab init
lab doctor
lab logbook
```

`lab init` creates only missing `.lab/` files and does not require a Python project or a Catfish-
specific filename. Give your coding agent `.lab/HARNESS.md` as a custom instruction. Commit the
durable `.lab` contracts and story artifacts; transient run records remain ignored.

## Your harness is the pair of hands

The Logbook is the human interface. `lab inbox --json` is the narrow machine interface for Codex,
Claude, or another tool-capable coding agent. Root [AGENTS.md](AGENTS.md) is the compact instruction
that teaches a compatible harness to read the request, perform the queued repository action, report
delays, preserve tests, and stop at human gates.

Text-only roles may use different providers, but provider choice never changes the evidence contract.
A prose-only Builder is never allowed to pretend it edited the repository.

OpenCode users can use both layers: select `opencode` for isolated text-only Lab roles, or launch the
bundled tool-capable Catfish agent with `opencode --agent catfish .`. See
[Harness selection](docs/lab/harnesses.md#opencode-setup) for the one-time authentication and model
setup.

## Keep exploring

- [Five-minute guide](docs/lab/quickstart.md)
- [Live presentation route](docs/presentation.md)
- [Improvement chart](docs/design/improvement-chart.md)
- [Why Catfish exists](docs/lab/why.md)
- [Roles and workflow](docs/lab/roles-and-workflow.md)
- [Harness proxy protocol](docs/lab/harness-proxy.md)
- [GitHub launch checklist](docs/repository-launch.md)
- [Security policy](SECURITY.md)
- [Contributing](CONTRIBUTING.md)

Serve the searchable handbook locally with `uv sync --extra docs && uv run lab docs`, then open
<http://127.0.0.1:8000>. Build it locally with `uv run lab docs --build`.

Catfish Lab is MIT-licensed and currently pre-1.0. This repository contains the Lab only; unrelated
prototype history is deliberately excluded from clones, packages, role context, and container images.
