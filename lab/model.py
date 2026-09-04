"""Vendor-neutral, text-only model boundary for isolated Lab roles."""

import subprocess
import tempfile
from dataclasses import dataclass
from pathlib import Path
from typing import Protocol


@dataclass(frozen=True)
class LabModelRequest:
    system: str
    prompt: str
    temperature: float | None = None


@dataclass(frozen=True)
class LabModelResponse:
    text: str
    model_id: str
    provider: str


class LabModelAdapter(Protocol):
    def complete(self, request: LabModelRequest) -> LabModelResponse: ...


class FakeModelAdapter:
    def __init__(self, responses: list[str]):
        self._responses = iter(responses)

    def complete(self, request: LabModelRequest) -> LabModelResponse:
        return LabModelResponse(text=next(self._responses), model_id="fake", provider="fake")


class ProvidedTextAdapter:
    """Treat text supplied by an external harness as one auditable role response."""

    def __init__(self, text: str, *, provider: str = "external-harness") -> None:
        self._text = text
        self._provider = provider

    def complete(self, request: LabModelRequest) -> LabModelResponse:
        return LabModelResponse(
            text=self._text,
            model_id="externally-provided",
            provider=self._provider,
        )


class LabModelError(RuntimeError):
    pass


DISABLED_CODEX_FEATURES = (
    "shell_tool",
    "unified_exec",
    "apply_patch_freeform",
    "apps",
    "plugins",
    "multi_agent",
    "browser_use",
    "computer_use",
    "image_generation",
    "in_app_browser",
    "js_repl",
    "tool_search",
    "connectors",
)


def build_codex_text_command(
    *, executable: str, output: Path, working_directory: Path, model_id: str | None
) -> list[str]:
    command = [
        executable,
        "exec",
        "--ephemeral",
        "--ignore-user-config",
        "--ignore-rules",
        "--strict-config",
        "--skip-git-repo-check",
        "--sandbox",
        "read-only",
        "-c",
        'web_search="disabled"',
        "-c",
        'shell_environment_policy.inherit="none"',
        "-C",
        str(working_directory),
        "--color",
        "never",
        "-o",
        str(output),
    ]
    for feature in DISABLED_CODEX_FEATURES:
        command.extend(("--disable", feature))
    if model_id:
        command.extend(("--model", model_id))
    command.append("-")
    return command


class CodexTextAdapter:
    """Fresh, ephemeral Codex invocation with local and network tools disabled."""

    def __init__(
        self,
        *,
        model_id: str | None = None,
        executable: str = "codex",
        timeout_seconds: int = 300,
    ) -> None:
        self._model_id = model_id
        self._executable = executable
        self._timeout_seconds = timeout_seconds

    def complete(self, request: LabModelRequest) -> LabModelResponse:
        prompt = f"SYSTEM\n{request.system}\n\nTASK\n{request.prompt}"
        with tempfile.TemporaryDirectory(prefix="catfish-lab-model-") as directory:
            root = Path(directory)
            output = root / "last-message.md"
            command = build_codex_text_command(
                executable=self._executable,
                output=output,
                working_directory=root,
                model_id=self._model_id,
            )
            try:
                completed = subprocess.run(
                    command,
                    input=prompt,
                    text=True,
                    capture_output=True,
                    timeout=self._timeout_seconds,
                    check=False,
                )
            except (OSError, subprocess.TimeoutExpired) as error:
                raise LabModelError(f"Codex invocation failed: {error}") from error
            if completed.returncode != 0:
                diagnostic = completed.stderr.strip().splitlines()[-1:]
                raise LabModelError(
                    f"Codex exited {completed.returncode}: "
                    f"{diagnostic[0] if diagnostic else 'no diagnostic'}"
                )
            if not output.exists():
                raise LabModelError("Codex did not write its final response")
            text = output.read_text(encoding="utf-8")
        return LabModelResponse(
            text=text,
            model_id=self._model_id or "codex-default",
            provider="openai-codex-cli",
        )
