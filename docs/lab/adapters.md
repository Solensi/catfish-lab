# Model Adapters

The controller uses one synchronous text protocol from `lab/model.py`:

```python
class LabModelAdapter(Protocol):
    def complete(self, request: LabModelRequest) -> LabModelResponse: ...
```

The request contains system text, assembled prompt, and optional temperature. The response contains
text, model ID, and provider label. Adapters do not select context, write artifacts, change stages,
or append the ledger; those responsibilities remain deterministic.

## Built-ins

`FakeModelAdapter` returns queued responses for tests. `CodexTextAdapter` starts a fresh ephemeral
Codex process in an empty temporary directory with tools, network, inherited environment, plugins,
connectors, and conversation persistence disabled. `ClaudeTextAdapter` uses one print-mode turn in
an empty directory with common tools explicitly disallowed. `OpenCodeTextAdapter` uses a pure,
non-interactive run in an empty directory, attaches the complete role brief as a file, and denies
every tool permission. `OllamaTextAdapter` sends the supplied system and task text to a configurable
local `/api/generate` endpoint with streaming disabled.

Users select these through `.lab/harnesses.yaml`, `lab harness NAME`, or the Logbook's `h` key. See
[Harness Selection](harnesses.md).

## Add another harness

Implement `complete`, return only text, and surface transport failures as exceptions:

```python
from lab.controller import run_role
from lab.model import LabModelRequest, LabModelResponse


class HarnessAdapter:
    def complete(self, request: LabModelRequest) -> LabModelResponse:
        text = my_harness_fresh_text_run(system=request.system, prompt=request.prompt)
        return LabModelResponse(text=text, model_id="configured-model", provider="my-harness")


run_role(root, role="scientist", story_id="US-004", adapter=HarnessAdapter())
```

The invocation must be fresh and must not add files, tools, environment values, or history beyond
the supplied request. If that boundary cannot be enforced, document the weaker isolation.
