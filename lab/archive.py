"""Deterministic evidence indexes for the Archivist and human reviewers."""

import json
from datetime import UTC, datetime
from pathlib import Path

from .artifacts import load_story, story_dir
from .ledger import read_records, verify_ledger
from .util import sha256_file

GENERATED_NAMES = {"evidence-index.json", "EVIDENCE.md"}


def build_evidence_index(repo_root: Path, story_id: str) -> dict[str, object]:
    story = load_story(repo_root, story_id)
    directory = story_dir(repo_root, story_id)
    artifacts = []
    for path in sorted(directory.rglob("*")):
        if not path.is_file() or path.name in GENERATED_NAMES:
            continue
        artifacts.append(
            {
                "path": path.relative_to(repo_root).as_posix(),
                "sha256": sha256_file(path),
                "bytes": path.stat().st_size,
            }
        )
    events = [
        record
        for record in read_records(repo_root / ".lab/ledger.jsonl")
        if record.get("story_id") == story_id
    ]
    return {
        "schema_version": 1,
        "generated_at": datetime.now(UTC).isoformat(),
        "story": story.model_dump(mode="json"),
        "ledger_integrity": {
            "verified": not verify_ledger(repo_root / ".lab/ledger.jsonl"),
            "event_count": len(events),
        },
        "artifacts": artifacts,
        "events": events,
    }


def write_evidence_index(repo_root: Path, story_id: str) -> tuple[Path, Path]:
    index = build_evidence_index(repo_root, story_id)
    evidence = story_dir(repo_root, story_id) / "evidence"
    evidence.mkdir(parents=True, exist_ok=True)
    json_path = evidence / "evidence-index.json"
    markdown_path = evidence / "EVIDENCE.md"
    json_path.write_text(json.dumps(index, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    lines = [
        f"# Evidence Index: {story_id}",
        "",
        "> Generated deterministically. Narrative claims must cite paths from this index.",
        "",
        "Ledger integrity: "
        f"**{'verified' if index['ledger_integrity']['verified'] else 'FAILED'}**",
        "",
        "## Artifacts",
        "",
    ]
    for artifact in index["artifacts"]:
        lines.append(f"- `{artifact['path']}` — `{artifact['sha256']}` ({artifact['bytes']} bytes)")
    lines.extend(("", "## Recorded events", ""))
    for event in index["events"]:
        action = event.get("event") or event.get("status") or "event"
        role = event.get("role", "controller")
        timestamp = event.get("recorded_at", event.get("completed_at", "unknown"))
        lines.append(f"- {timestamp}: {role} / {action}")
    markdown_path.write_text("\n".join(lines).rstrip() + "\n", encoding="utf-8")
    return markdown_path, json_path
