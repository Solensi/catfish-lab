# Harness Selection

Press `h` in the interactive Logbook to open the harness chooser. Use focus navigation and Enter, or
click a provider, to choose which harness future isolated role runs use. Readiness is shown before
selection; the result appears in the realtime situation line.

Four profiles are created by `lab init`:

| Profile | Transport | Default behavior |
|---|---|---|
| Codex CLI | Fresh `codex exec` process | Tool-disabled, read-only, ephemeral invocation |
| Claude Code | Fresh `claude -p` process | Text output, plan permission mode, one turn |
| OpenCode | Fresh `opencode --pure run` process | Attached brief, all tool permissions denied |
| Ollama · local | `POST /api/generate` | Local non-streaming generation with `gemma3` |

The Claude invocation follows Anthropic's documented print-mode flags. OpenCode uses its documented
non-interactive `run`, pure mode, file attachment, model selection, and permission controls. Ollama
uses its documented non-streaming generate endpoint. See the
[Claude CLI reference](https://docs.anthropic.com/en/docs/claude-code/cli-usage),
[OpenCode CLI reference](https://dev.opencode.ai/docs/cli/),
[OpenCode permissions](https://opencode.ai/docs/permissions/), and
[Ollama generate API](https://docs.ollama.com/api/generate).

Edit `.lab/harnesses.yaml` to change executable paths, model IDs, or the Ollama endpoint. Secrets do
not belong in this file. CLI equivalents are:

```bash
lab harness                 # list profiles and availability
lab harness claude          # select a profile
lab run scientist US-004    # active profile is the default
lab run scientist US-004 --harness
lab run scientist US-004 --codex  # deliberate one-run override
lab run scientist US-004 --from response.md  # import the outer harness response
```

Selecting an unavailable profile is allowed so configuration can happen in any order. Its status is
shown as `DELAYED`. If an invocation fails or violates its output contract, the CLI records a
`work_delayed` event with the diagnostic before returning nonzero. External proxies must report their
own blockers with `lab delay STORY --reason TEXT`.

The Ollama availability check requests `/api/tags` with a short timeout. In Docker, change the
endpoint to an address reachable from the container, commonly `host.docker.internal`, according to
your Docker host configuration.

## OpenCode setup

Install OpenCode using the [official cross-platform instructions](https://opencode.ai/docs/#install).
For example, choose one supported package route, then connect the provider you intend to use:

```bash
npm install -g opencode-ai
# or on macOS/Linux: brew install anomalyco/tap/opencode

opencode auth login
opencode models
lab harness opencode
lab logbook
```

The profile works without a fixed model when OpenCode already has a default. To pin one, put the
`provider/model` identifier printed by `opencode models` in `.lab/harnesses.yaml` under
`profiles.opencode.model`. You can also choose OpenCode inside the Logbook with `h`.

There are two deliberately different OpenCode paths:

- **Inside the Logbook:** OpenCode supplies one isolated, text-only role. Catfish invokes it in an
  empty temporary directory, sets pure mode, disables default plugins and auto-update for that run,
  and denies every tool. It can write only through Catfish's validated artifact boundary.
- **Around the Lab:** OpenCode is the tool-capable coding harness. This repository ships
  `.opencode/agents/catfish.md`; start it with `opencode --agent catfish .`. The agent reads
  `.lab/HARNESS.md`, consumes explicitly queued work, may edit the repository, and stops at human
  gates.

Authentication and provider credentials remain in OpenCode's own configuration. Never copy them
into `.lab/harnesses.yaml` or evidence artifacts.
