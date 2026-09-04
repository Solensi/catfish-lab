from pathlib import Path

from lab.artifacts import create_story
from lab.config import initialize


def test_init_is_idempotent_and_preserves_custom_role(tmp_path: Path) -> None:
    initialize(tmp_path)
    role = tmp_path / ".lab/roles/product.md"
    role.write_text("custom")
    initialize(tmp_path)
    assert role.read_text() == "custom"


def test_story_ids_are_collision_safe(tmp_path: Path) -> None:
    initialize(tmp_path)
    first = create_story(tmp_path, "First")
    second = create_story(tmp_path, "Second")
    assert (first.id, second.id) == ("US-001", "US-002")
