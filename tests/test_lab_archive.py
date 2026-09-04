import json
from pathlib import Path

from lab.archive import write_evidence_index
from lab.artifacts import create_story
from lab.config import initialize


def test_evidence_index_hashes_artifacts_and_includes_events(tmp_path: Path) -> None:
    initialize(tmp_path)
    story = create_story(tmp_path, "Evidence first")

    markdown_path, json_path = write_evidence_index(tmp_path, story.id)
    index = json.loads(json_path.read_text())

    assert index["ledger_integrity"]["verified"] is True
    assert index["events"][0]["event"] == "story_created"
    assert any(item["path"].endswith("story.md") for item in index["artifacts"])
    assert "Narrative claims must cite paths" in markdown_path.read_text()
