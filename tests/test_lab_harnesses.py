from pathlib import Path
from types import SimpleNamespace

from typer.testing import CliRunner

from lab import cli
from lab.artifacts import create_story
from lab.config import initialize
from lab.harnesses import (
    ClaudeTextAdapter,
    OpenCodeTextAdapter,
    active_profile,
    load_harnesses,
    select_harness,
)
from lab.ledger import read_records
from lab.model import LabModelError, LabModelRequest
from lab.workflow import inbox_payload, request_next_action


def prepare(tmp_path: Path) -> None:
    initialize(tmp_path)


def test_harness_profiles_are_initialized_and_selectable(tmp_path: Path) -> None:
    prepare(tmp_path)

    active, profiles = load_harnesses(tmp_path)
    selected = select_harness(tmp_path, "claude")

    assert active == "codex"
    assert [profile.name for profile in profiles] == ["codex", "claude", "opencode", "ollama"]
    assert selected.name == "claude"
    assert active_profile(tmp_path).name == "claude"
    event = read_records(tmp_path / ".lab/ledger.jsonl")[-1]
    assert event["event"] == "harness_selected"
    assert "available" in event


def test_selecting_current_harness_does_not_duplicate_ledger_event(tmp_path: Path) -> None:
    prepare(tmp_path)

    select_harness(tmp_path, "codex")

    assert read_records(tmp_path / ".lab/ledger.jsonl") == []


def test_model_failure_becomes_visible_delay_and_keeps_request_pending(
    tmp_path: Path, monkeypatch
) -> None:
    class FailingAdapter:
        def complete(self, request):
            raise LabModelError("provider is warming up")

    prepare(tmp_path)
    story = create_story(tmp_path, "Watch failures", lab_depth="full")
    request_next_action(tmp_path, story.id)
    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(cli, "adapter_for_active", lambda root, model_id: FailingAdapter())

    result = CliRunner().invoke(cli.app, ["run", "scientist", story.id, "--harness"])

    item = inbox_payload(tmp_path)["stories"][0]
    assert result.exit_code != 0
    assert "Work delayed" in result.output
    assert item["requested_action"] == f"lab run scientist {story.id} --harness"
    assert item["delay"]["reason"] == "provider is warming up"


def test_claude_adapter_uses_one_tool_disallowed_print_turn(monkeypatch) -> None:
    captured: dict[str, object] = {}

    def fake_run(command, **kwargs):
        captured["command"] = command
        captured["kwargs"] = kwargs
        return SimpleNamespace(returncode=0, stdout="# Hypothesis\n", stderr="")

    monkeypatch.setattr("lab.harnesses.subprocess.run", fake_run)
    response = ClaudeTextAdapter(model_id="sonnet").complete(
        LabModelRequest(system="isolated", prompt="write the artifact")
    )

    command = captured["command"]
    assert command[:3] == ["claude", "-p", "--output-format"]
    assert "--disallowedTools" in command
    assert "--max-turns" in command
    assert response.provider == "anthropic-claude-cli"


def test_opencode_adapter_uses_pure_tool_denied_file_attached_run(monkeypatch) -> None:
    captured: dict[str, object] = {}

    def fake_run(command, **kwargs):
        captured["command"] = command
        captured["kwargs"] = kwargs
        attachment = Path(command[command.index("--file") + 1])
        captured["prompt"] = attachment.read_text()
        return SimpleNamespace(returncode=0, stdout="# Hypothesis\n\nObservable.\n", stderr="")

    monkeypatch.setattr("lab.harnesses.subprocess.run", fake_run)
    response = OpenCodeTextAdapter(model_id="anthropic/claude-sonnet-4-5").complete(
        LabModelRequest(system="isolated", prompt="write the artifact")
    )

    command = captured["command"]
    environment = captured["kwargs"]["env"]
    assert command[:3] == ["opencode", "--pure", "run"]
    assert command[command.index("--model") + 1] == "anthropic/claude-sonnet-4-5"
    assert captured["kwargs"]["cwd"] == Path(command[command.index("--file") + 1]).parent
    assert environment["OPENCODE_PERMISSION"] == '"deny"'
    assert environment["OPENCODE_DISABLE_DEFAULT_PLUGINS"] == "true"
    assert "SYSTEM\nisolated" in captured["prompt"]
    assert response.provider == "opencode-cli"
