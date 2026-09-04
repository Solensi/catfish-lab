from pathlib import Path

from lab.model import DISABLED_CODEX_FEATURES, build_codex_text_command


def test_codex_text_command_is_fresh_ephemeral_and_tool_disabled(tmp_path: Path) -> None:
    command = build_codex_text_command(
        executable="codex",
        output=tmp_path / "output.md",
        working_directory=tmp_path,
        model_id="test-model",
    )
    assert "--ephemeral" in command
    assert "--ignore-user-config" in command
    assert "read-only" in command
    assert 'web_search="disabled"' in command
    assert 'shell_environment_policy.inherit="none"' in command
    for feature in DISABLED_CODEX_FEATURES:
        index = command.index(feature)
        assert command[index - 1] == "--disable"
    assert command[-3:] == ["--model", "test-model", "-"]
