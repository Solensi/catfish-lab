from pathlib import Path

import pytest
import yaml

from lab.config import initialize
from lab.context import ContextError, ContextPolicy, resolve_context
from lab.roles import contract_for


def test_forbidden_beats_allowed(tmp_path: Path) -> None:
    (tmp_path / "safe.txt").write_text("safe")
    (tmp_path / ".env").write_text("TOKEN=secret")
    paths = resolve_context(tmp_path, ContextPolicy(("**/*",), (".env",)))
    assert [path.name for path in paths] == ["safe.txt"]


def test_context_order_is_deterministic(tmp_path: Path) -> None:
    (tmp_path / "z.txt").write_text("z")
    (tmp_path / "a.txt").write_text("a")
    paths = resolve_context(tmp_path, ContextPolicy(("*.txt",), ()))
    assert [path.name for path in paths] == ["a.txt", "z.txt"]


def test_path_escape_and_symlink_are_rejected(tmp_path: Path) -> None:
    with pytest.raises(ContextError):
        resolve_context(tmp_path, ContextPolicy(("../*",), ()))
    target = tmp_path.parent / "outside.txt"
    target.write_text("outside")
    (tmp_path / "escape").symlink_to(target)
    with pytest.raises(ContextError):
        resolve_context(tmp_path, ContextPolicy(("escape",), ()))


def test_independent_candidates_are_mutually_forbidden() -> None:
    architect = contract_for("architect", "US-014").policy.forbidden_globs
    heretic = contract_for("heretic", "US-014").policy.forbidden_globs
    assert ".lab/stories/US-014/candidates/B.md" in architect
    assert ".lab/stories/US-014/candidates/A.md" in heretic


def test_technical_roles_can_inspect_lab_implementation() -> None:
    for role in ("scientist", "architect", "heretic", "builder", "redteam", "judge"):
        allowed = contract_for(role, "US-014").policy.allowed_globs
        assert "lab/**/*" in allowed
        assert not any(pattern.startswith("archive/") for pattern in allowed)


def test_project_context_supports_other_languages_and_configured_denials(tmp_path: Path) -> None:
    initialize(tmp_path)
    source = tmp_path / "src"
    source.mkdir()
    archived_source = tmp_path / "archive"
    archived_source.mkdir()
    (source / "main.ts").write_text("export const answer = 42;\n")
    (source / "private.ts").write_text("export const hidden = true;\n")
    (source / "logo.bin").write_bytes(b"\x00\xff\x00")
    (archived_source / "migration.md").write_text("# Still relevant project source\n")
    config_path = tmp_path / ".lab/config.yaml"
    config = yaml.safe_load(config_path.read_text())
    config["context"]["include_globs"].append("archive/**/*.md")
    config["security"]["deny_globs"].append("src/private.ts")
    config_path.write_text(yaml.safe_dump(config, sort_keys=False))

    policy = contract_for("builder", "US-014", tmp_path).policy
    selected = [path.relative_to(tmp_path).as_posix() for path in resolve_context(tmp_path, policy)]

    assert "src/main.ts" in selected
    assert "archive/migration.md" in selected
    assert "src/private.ts" not in selected
    assert "src/logo.bin" not in selected


def test_builder_context_includes_human_assessment_feedback(tmp_path: Path) -> None:
    initialize(tmp_path)
    feedback = tmp_path / ".lab/stories/US-014/evidence/human-feedback-example.md"
    feedback.parent.mkdir(parents=True)
    feedback.write_text("# Human Assessment Feedback\n\nMake the reading pane scrollable.\n")

    selected = [
        path.relative_to(tmp_path).as_posix()
        for path in resolve_context(tmp_path, contract_for("builder", "US-014", tmp_path).policy)
    ]

    assert ".lab/stories/US-014/evidence/human-feedback-example.md" in selected
