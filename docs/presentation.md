# Six-minute presentation route

The presentation is a product story, not a tour of every command. Rehearse with the same terminal
size and harness you will use live.

## Before the room

```bash
uv sync --extra docs
uv run lab doctor
uv run lab tutorial --snapshot
```

Open one terminal in the repository. Keep `uv run lab logbook --snapshot` as the no-animation
fallback. Do not approve a completion gate merely to make the ending cleaner.

## 0:00 — the promise

Say: “AI can produce an answer quickly. Catfish keeps the path inspectable after the chat is gone.”
Open `uv run lab logbook`. Point to one story, one next action, and one status line. Do not explain
the state machine.

## 0:45 — make an ordinary request

Press `n` and enter a small, observable request. Leave the default LIGHT route selected. Explain that
the short route is for delivery; FULL exists when uncertainty warrants the Scientist, Architect, and
blind Heretic.

## 1:30 — show the honest handoff

Press `a`. The Product Steward makes scope durable, then Catfish stops at the Builder handoff because
a text-only role must not pretend to edit files. Show `lab inbox --json` only if the audience wants
the agent-facing protocol.

## 2:30 — show disagreement with receipts

Press `l`. Each report says who made the claim and cites its artifact. If using the tutorial, open the
Architect and blind Heretic with their numbered keys to show that memorable names represent separate
context contracts, not imaginary personalities.

## 3:30 — show resistance

Point to the Red Team and Judge. The Builder cannot review itself, missing artifacts remain visible,
provider failures become DELAYED, and a READY trial still cannot approve itself.

## 4:30 — show portability

Press `h` to show harness choice. Explain that Codex, Claude Code, OpenCode, and local Ollama can
supply text-only roles while the surrounding coding harness remains the tool-capable pair of hands.
Mention Docker and local Markdown docs; do not claim untested device support.

## 5:15 — close on memory

Open an Archivist artifact from a completed story or use the tutorial snapshot. End with: “The names
make the responsibilities memorable. The hashes, sources, and human gates make them accountable.”

## Failure-safe ending

If a provider is unavailable, treat the DELAYED report as a feature demonstration and switch to the
deterministic tutorial snapshot. If the TUI cannot render correctly on the venue terminal, run:

```bash
NO_COLOR=1 uv run lab logbook --snapshot
```

That fallback is less theatrical but makes the same evidence claims.
