"""Durable harness selection and concrete text-only model adapters."""

import json
import os
import shutil
import subprocess
import tempfile
import urllib.error
import urllib.request
from dataclasses import dataclass
from pathlib import Path

import yaml

from .ledger import append_record
from .model import (
    CodexTextAdapter,
    LabModelAdapter,
    LabModelError,
    LabModelRequest,
    LabModelResponse,
)

HARNESS_CONFIG = """version: 1
active: codex
profiles:
  codex:
    label: Codex CLI
    kind: codex
    executable: codex
    model:
  claude:
    label: Claude Code
    kind: claude
    executable: claude
    model:
  opencode:
    label: OpenCode
    kind: opencode
    executable: opencode
    model:
  ollama:
    label: Ollama · local
    kind: ollama
    endpoint: http://localhost:11434/api/generate
    model: gemma3
"""


@dataclass(frozen=True)
class HarnessProfile:
    name: str
    label: str
    kind: str
    model: str | None
    executable: str | None = None
    endpoint: str | None = None


def config_path(repo_root: Path) -> Path:
    return repo_root / ".lab/harnesses.yaml"


def load_harnesses(repo_root: Path) -> tuple[str, list[HarnessProfile]]:
    path = config_path(repo_root)
    if not path.is_file():
        raise ValueError("missing .lab/harnesses.yaml; run `lab init`")
    payload = yaml.safe_load(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict) or payload.get("version") != 1:
        raise ValueError(".lab/harnesses.yaml must contain version: 1")
    raw_profiles = payload.get("profiles")
    if not isinstance(raw_profiles, dict) or not raw_profiles:
        raise ValueError(".lab/harnesses.yaml requires at least one profile")
    profiles: list[HarnessProfile] = []
    for name, raw in raw_profiles.items():
        if not isinstance(name, str) or not isinstance(raw, dict):
            raise ValueError("invalid harness profile")
        kind = raw.get("kind")
        if kind not in {"codex", "claude", "opencode", "ollama"}:
            raise ValueError(f"unsupported harness kind for {name}: {kind}")
        profiles.append(
            HarnessProfile(
                name=name,
                label=str(raw.get("label") or name),
                kind=kind,
                model=str(raw["model"]) if raw.get("model") else None,
                executable=str(raw["executable"]) if raw.get("executable") else None,
                endpoint=str(raw["endpoint"]) if raw.get("endpoint") else None,
            )
        )
    active = payload.get("active")
    if active not in {profile.name for profile in profiles}:
        raise ValueError(f"active harness does not name a configured profile: {active}")
    return str(active), profiles


def active_profile(repo_root: Path) -> HarnessProfile:
    active, profiles = load_harnesses(repo_root)
    return next(profile for profile in profiles if profile.name == active)


def profile_availability(profile: HarnessProfile) -> tuple[bool, str]:
    if profile.kind in {"codex", "claude", "opencode"}:
        executable = profile.executable or profile.kind
        location = shutil.which(executable)
        return (True, location) if location else (False, f"{executable} not found in PATH")
    if not profile.model:
        return False, "no local model configured"
    if not profile.endpoint:
        return False, "no Ollama endpoint configured"
    tags = profile.endpoint.rsplit("/api/", 1)[0] + "/api/tags"
    try:
        with urllib.request.urlopen(tags, timeout=0.15):
            pass
    except (OSError, urllib.error.URLError):
        return False, f"Ollama is not responding at {profile.endpoint}"
    return True, f"connected to {profile.endpoint}"


def select_harness(repo_root: Path, name: str) -> HarnessProfile:
    active, profiles = load_harnesses(repo_root)
    selected = next((profile for profile in profiles if profile.name == name), None)
    if selected is None:
        raise ValueError(f"unknown harness: {name}")
    if name != active:
        path = config_path(repo_root)
        payload = yaml.safe_load(path.read_text(encoding="utf-8"))
        payload["active"] = name
        path.write_text(yaml.safe_dump(payload, sort_keys=False), encoding="utf-8")
        available, detail = profile_availability(selected)
        append_record(
            repo_root / ".lab/ledger.jsonl",
            {
                "event": "harness_selected",
                "role": "human",
                "harness": name,
                "available": available,
                "detail": detail,
                "status": "success" if available else "delayed",
            },
        )
    return selected


class ClaudeTextAdapter:
    """Fresh Claude Code print-mode invocation in an empty directory."""

    def __init__(self, *, executable: str = "claude", model_id: str | None = None) -> None:
        self._executable = executable
        self._model_id = model_id

    def complete(self, request: LabModelRequest) -> LabModelResponse:
        command = [
            self._executable,
            "-p",
            "--output-format",
            "text",
            "--permission-mode",
            "plan",
            "--max-turns",
            "1",
            "--disallowedTools",
            "Bash,Edit,Write,Read,Glob,Grep,WebFetch,WebSearch,NotebookEdit,Task",
        ]
        if self._model_id:
            command.extend(("--model", self._model_id))
        prompt = f"SYSTEM\n{request.system}\n\nTASK\n{request.prompt}"
        try:
            with tempfile.TemporaryDirectory(prefix="catfish-lab-claude-") as directory:
                completed = subprocess.run(
                    command,
                    input=prompt,
                    text=True,
                    capture_output=True,
                    timeout=300,
                    check=False,
                    cwd=directory,
                )
        except (OSError, subprocess.TimeoutExpired) as error:
            raise LabModelError(f"Claude invocation failed: {error}") from error
        if completed.returncode != 0:
            detail = completed.stderr.strip().splitlines()[-1:] or ["no diagnostic"]
            raise LabModelError(f"Claude exited {completed.returncode}: {detail[0]}")
        return LabModelResponse(
            text=completed.stdout,
            model_id=self._model_id or "claude-default",
            provider="anthropic-claude-cli",
        )


class OllamaTextAdapter:
    """Text-only adapter for Ollama's local non-streaming generate endpoint."""

    def __init__(self, *, endpoint: str, model_id: str) -> None:
        self._endpoint = endpoint
        self._model_id = model_id

    def complete(self, request: LabModelRequest) -> LabModelResponse:
        body = json.dumps(
            {
                "model": self._model_id,
                "system": request.system,
                "prompt": request.prompt,
                "stream": False,
            }
        ).encode()
        call = urllib.request.Request(
            self._endpoint,
            data=body,
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        try:
            with urllib.request.urlopen(call, timeout=300) as response:
                payload = json.loads(response.read())
        except (OSError, urllib.error.URLError, json.JSONDecodeError) as error:
            raise LabModelError(f"Ollama invocation failed: {error}") from error
        text = payload.get("response") if isinstance(payload, dict) else None
        if not isinstance(text, str):
            raise LabModelError("Ollama response did not contain text")
        return LabModelResponse(text=text, model_id=self._model_id, provider="ollama-local")


class OpenCodeTextAdapter:
    """Fresh OpenCode run with an attached prompt and every model tool denied."""

    def __init__(
        self,
        *,
        executable: str = "opencode",
        model_id: str | None = None,
        timeout_seconds: int = 300,
    ) -> None:
        self._executable = executable
        self._model_id = model_id
        self._timeout_seconds = timeout_seconds

    def complete(self, request: LabModelRequest) -> LabModelResponse:
        prompt = f"SYSTEM\n{request.system}\n\nTASK\n{request.prompt}"
        try:
            with tempfile.TemporaryDirectory(prefix="catfish-lab-opencode-") as directory:
                root = Path(directory)
                attachment = root / "role-request.md"
                attachment.write_text(prompt, encoding="utf-8")
                command = [
                    self._executable,
                    "--pure",
                    "run",
                    "--format",
                    "default",
                    "--file",
                    str(attachment),
                ]
                if self._model_id:
                    command.extend(("--model", self._model_id))
                command.append("Return only the artifact requested in the attached role brief.")
                environment = os.environ.copy()
                environment.update(
                    {
                        "OPENCODE_PERMISSION": json.dumps("deny"),
                        "OPENCODE_DISABLE_AUTOUPDATE": "true",
                        "OPENCODE_DISABLE_DEFAULT_PLUGINS": "true",
                        "OPENCODE_DISABLE_LSP_DOWNLOAD": "true",
                        "OPENCODE_DISABLE_CLAUDE_CODE": "true",
                    }
                )
                completed = subprocess.run(
                    command,
                    text=True,
                    capture_output=True,
                    timeout=self._timeout_seconds,
                    check=False,
                    cwd=root,
                    env=environment,
                )
        except (OSError, subprocess.TimeoutExpired) as error:
            raise LabModelError(f"OpenCode invocation failed: {error}") from error
        if completed.returncode != 0:
            detail = completed.stderr.strip().splitlines()[-1:] or ["no diagnostic"]
            raise LabModelError(f"OpenCode exited {completed.returncode}: {detail[0]}")
        text = completed.stdout.strip()
        if not text:
            raise LabModelError("OpenCode returned no artifact text")
        return LabModelResponse(
            text=text,
            model_id=self._model_id or "opencode-default",
            provider="opencode-cli",
        )


def adapter_for_active(repo_root: Path, *, model_id: str | None = None) -> LabModelAdapter:
    profile = active_profile(repo_root)
    chosen_model = model_id or profile.model
    if profile.kind == "codex":
        return CodexTextAdapter(
            executable=profile.executable or "codex",
            model_id=chosen_model,
        )
    if profile.kind == "claude":
        return ClaudeTextAdapter(
            executable=profile.executable or "claude",
            model_id=chosen_model,
        )
    if profile.kind == "opencode":
        return OpenCodeTextAdapter(
            executable=profile.executable or "opencode",
            model_id=chosen_model,
        )
    if not profile.endpoint or not chosen_model:
        raise ValueError("Ollama requires endpoint and model in .lab/harnesses.yaml")
    return OllamaTextAdapter(endpoint=profile.endpoint, model_id=chosen_model)
