"""Safe story artifact and state persistence."""

from datetime import UTC, datetime
from pathlib import Path

import yaml

from .config import STORY_README
from .contracts import ArtifactState, StoryState
from .ledger import append_record


def story_dir(repo_root: Path, story_id: str) -> Path:
    if not story_id.startswith("US-") or not story_id[3:].isdigit():
        raise ValueError(f"invalid story id: {story_id}")
    return repo_root / ".lab" / "stories" / story_id


def load_story(repo_root: Path, story_id: str) -> StoryState:
    path = story_dir(repo_root, story_id) / "story.yaml"
    return StoryState.model_validate(yaml.safe_load(path.read_text(encoding="utf-8")), strict=False)


def save_story(repo_root: Path, story: StoryState) -> None:
    directory = story_dir(repo_root, story.id)
    directory.mkdir(parents=True, exist_ok=True)
    payload = story.model_dump(mode="json")
    (directory / "story.yaml").write_text(
        yaml.safe_dump(payload, sort_keys=False), encoding="utf-8"
    )


def next_story_id(repo_root: Path) -> str:
    root = repo_root / ".lab" / "stories"
    used = [int(path.name[3:]) for path in root.glob("US-[0-9]*") if path.name[3:].isdigit()]
    return f"US-{max(used, default=0) + 1:03d}"


def create_story(
    repo_root: Path,
    title: str,
    *,
    lab_depth: str = "light",
    request: str | None = None,
) -> StoryState:
    timestamp = datetime.now(UTC)
    story = StoryState(
        id=next_story_id(repo_root),
        title=title,
        lab_depth=lab_depth,
        created_at=timestamp,
        updated_at=timestamp,
        artifacts=ArtifactState(story=request is None),
    )
    directory = story_dir(repo_root, story.id)
    (directory / "candidates").mkdir(parents=True)
    (directory / "critiques").mkdir()
    (directory / "evidence").mkdir()
    save_story(repo_root, story)
    if request is None:
        template = (repo_root / ".lab/templates/story.md").read_text(encoding="utf-8")
        (directory / "story.md").write_text(template, encoding="utf-8")
    if request:
        (directory / "request.md").write_text(
            "# Original Request\n\n"
            "> This is the user's durable input. Roles may scope it, but must not silently "
            "rewrite it.\n\n"
            "## Prompt\n\n"
            f"{request.strip()}\n",
            encoding="utf-8",
        )
    (directory / "README.md").write_text(STORY_README.format(story_id=story.id), encoding="utf-8")
    append_record(
        repo_root / ".lab/ledger.jsonl",
        {
            "event": "story_created",
            "role": "human",
            "story_id": story.id,
            "title": story.title,
            "lab_depth": story.lab_depth,
            "status": "success",
        },
    )
    return story
