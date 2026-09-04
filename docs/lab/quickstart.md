# Five-minute guide

## 1. Open the Logbook

=== "Docker"

    ```bash
    docker compose build
    docker compose run --rm lab logbook
    ```

=== "Python + uv"

    ```bash
    uv sync
    uv run lab init
    uv run lab doctor
    uv run lab logbook
    ```

The first interactive launch opens a styled invitation to a synthetic, disposable tutorial. Enter
accepts, `s` or Esc skips, and Space toggles the **DON'T SHOW AGAIN** preference. Nothing begins until
the separate orientation; press `b` there when ready. During the cast, Space pauses and `j`/`k`
scrolls. Quit with `q`; run `lab tutorial` whenever you want it, regardless of that preference.

## 2. Ask normally

Press `n`, type the outcome you want, and press Enter. LIGHT is selected because most maintenance
does not need a research pageant. For FULL, focus and select “Use the full experimental route” when
the central question is genuinely uncertain or costly.

Submitting a LIGHT request is the human authorization for that bounded implementation. Catfish does
not make you approve the same request twice.

## 3. Advance once

Open the story and press `a`. Catfish runs consecutive text-only specialists until it reaches one of
three honest boundaries:

- **HANDOFF** — the surrounding coding harness must inspect or change repository files.
- **HUMAN GATE** — an experiment, implementation decision, or final result needs authority.
- **DELAYED** — a provider or tool failed; the reason remains visible in the Logbook.

If a coding agent is operating this repository, the root `AGENTS.md` instruction tells it to consume
the handoff from `lab inbox --json` and record the result.

At a human gate, `e` visits the evidence selected for that decision. Review it with `j`/`k`, press
Esc to return, and use `y` only when the claim is acceptable. At the final assessment, `r` opens a
required feedback field and sends the case back to the Builder. Esc changes nothing.

## 4. Inspect only as deeply as useful

- `↑`/`↓` or `j`/`k` moves between stories without live updates stealing the selection.
- Tab or `→` enters the case text; `j`/`k` then scrolls it, and `←` returns to stories.
- `e` browses every expected or recorded case file and shows its exact path.
- `l` opens the source-linked live analysis.
- `1–8` opens any named role and its source artifact.
- `h` switches Codex, Claude Code, OpenCode, or local Ollama.
- `?` opens the concise key guide.

Run `lab files US-NNN` to locate documents, `lab status US-NNN` for a plain terminal summary, or
`lab logbook US-NNN --snapshot` for a stable report in automation.

## Locked-down hosts

If `uv` reports that its home cache is read-only, point it at any writable temporary directory for
the command, for example `UV_CACHE_DIR=/tmp/catfish-uv-cache uv run lab doctor` on POSIX. This changes
only dependency caching; Lab evidence still lives in the repository's `.lab/` directory.
