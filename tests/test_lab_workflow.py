from pathlib import Path

import pytest
from typer.testing import CliRunner

from lab.artifacts import create_story, load_story, save_story
from lab.cli import app
from lab.config import initialize
from lab.ledger import read_records
from lab.stages import Stage
from lab.workflow import (
    approve_story,
    create_request,
    draft_artifact,
    inbox_payload,
    next_actions,
    record_artifact,
    request_next_action,
    set_story_depth,
)


def prepare_proposals(tmp_path: Path):
    initialize(tmp_path)
    story = create_story(tmp_path, "Complete the middle workflow", lab_depth="full")
    story = story.model_copy(
        update={
            "stage": Stage.PROPOSALS,
            "artifacts": story.artifacts.model_copy(
                update={"hypothesis": True, "candidate_a": True, "candidate_b": True}
            ),
        }
    )
    save_story(tmp_path, story)
    return story


def write_artifact(tmp_path: Path, name: str, text: str) -> Path:
    path = tmp_path / name
    path.write_text(text)
    return path


def test_recorded_artifacts_complete_missing_middle_workflow(tmp_path: Path, monkeypatch) -> None:
    story = prepare_proposals(tmp_path)
    critique = write_artifact(tmp_path, "critique.md", "# Critique\n\nMeasured concern.\n")
    experiment = write_artifact(tmp_path, "experiment.md", "# Experiment\n\n## Success criteria\n")
    results = write_artifact(tmp_path, "results.json", '{"passed": true}\n')
    decision = write_artifact(tmp_path, "decision.md", "# Decision\n\nChoose the evidence.\n")

    record_artifact(tmp_path, story.id, "critique", critique)
    record_artifact(tmp_path, story.id, "experiment", experiment)
    monkeypatch.chdir(tmp_path)
    approval = CliRunner().invoke(app, ["approve", "experiment", story.id, "--yes"])
    assert approval.exit_code == 0
    record_artifact(tmp_path, story.id, "evidence", results)
    record_artifact(tmp_path, story.id, "decision", decision)

    updated = load_story(tmp_path, story.id)
    assert updated.stage is Stage.DECISION
    assert updated.artifacts.critiques
    assert updated.artifacts.experiment
    assert updated.artifacts.evidence
    assert updated.artifacts.decision
    assert next_actions(tmp_path, story.id) == [f"lab approve implementation {story.id}"]


def test_record_refuses_wrong_stage_and_overwrite(tmp_path: Path) -> None:
    story = prepare_proposals(tmp_path)
    critique = write_artifact(tmp_path, "critique.md", "# Critique\n\nMeasured concern.\n")
    record_artifact(tmp_path, story.id, "critique", critique)

    with pytest.raises(ValueError, match="only be recorded at proposals"):
        record_artifact(tmp_path, story.id, "critique", critique)


def test_story_workspace_explains_missing_role_artifacts(tmp_path: Path) -> None:
    initialize(tmp_path)
    story = create_story(tmp_path, "Readable workspace")

    overview = tmp_path / ".lab" / "stories" / story.id / "README.md"
    assert "blind Heretic" in overview.read_text()
    assert "missing role artifact" in overview.read_text()


def test_draft_creates_editable_template_without_advancing_story(tmp_path: Path) -> None:
    story = prepare_proposals(tmp_path)

    draft = draft_artifact(tmp_path, story.id, "critique")

    assert draft.read_text().startswith("# Critique")
    assert load_story(tmp_path, story.id).stage is Stage.PROPOSALS
    assert next_actions(tmp_path, story.id) == [
        f"lab record critique {story.id} --from .lab/stories/{story.id}/drafts/critique.md"
    ]


def test_request_is_durable_private_from_ledger_and_visible_to_harness(tmp_path: Path) -> None:
    initialize(tmp_path)

    story_id = create_request(
        tmp_path,
        "Repair the parser, document the behavior, and prove it on Windows.",
        title=None,
        depth="full",
    )
    action = request_next_action(tmp_path, story_id)
    request_next_action(tmp_path, story_id)

    request_text = (tmp_path / ".lab/stories" / story_id / "request.md").read_text()
    records = read_records(tmp_path / ".lab/ledger.jsonl")
    item = inbox_payload(tmp_path)["stories"][0]
    assert "Repair the parser" in request_text
    assert all("prompt" not in record for record in records)
    assert action == f"lab run product {story_id} --harness"
    assert item["requested_action"] == action
    assert item["request_artifact"].endswith("request.md")
    assert sum(record.get("event") == "action_requested" for record in records) == 1


def test_inbox_excludes_idle_history_unless_requested(tmp_path: Path) -> None:
    initialize(tmp_path)
    idle = create_story(tmp_path, "Old context")
    queued = create_story(tmp_path, "Current work")
    request_next_action(tmp_path, queued.id)

    assert [item["id"] for item in inbox_payload(tmp_path)["stories"]] == [queued.id]
    assert [item["id"] for item in inbox_payload(tmp_path, include_idle=True)["stories"]] == [
        idle.id,
        queued.id,
    ]


def test_approval_records_state_and_evidence_event(tmp_path: Path) -> None:
    story = prepare_proposals(tmp_path)
    experiment = write_artifact(tmp_path, "experiment.md", "# Experiment\n")
    critique = write_artifact(tmp_path, "critique.md", "# Critique\n")
    record_artifact(tmp_path, story.id, "critique", critique)
    record_artifact(tmp_path, story.id, "experiment", experiment)

    approve_story(tmp_path, story.id, "experiment")

    assert load_story(tmp_path, story.id).human.experiment_approved
    assert read_records(tmp_path / ".lab/ledger.jsonl")[-1]["event"] == "approval_recorded"


def test_request_changes_cli_requires_reason_and_queues_builder(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    initialize(tmp_path)
    story = create_story(tmp_path, "Reject an incomplete assessment")
    directory = tmp_path / ".lab/stories" / story.id
    for name, heading in (
        ("implementation.md", "# Implementation"),
        ("redteam.md", "# Red Team Report"),
        ("trial.md", "# Completion Trial\n\n## Overall Verdict\n\nREADY"),
    ):
        (directory / name).write_text(f"{heading}\n")
    save_story(
        tmp_path,
        story.model_copy(
            update={
                "stage": Stage.TRIAL,
                "human": story.human.model_copy(update={"implementation_approved": True}),
                "artifacts": story.artifacts.model_copy(
                    update={"implementation": True, "redteam": True, "trial": True}
                ),
            }
        ),
    )
    monkeypatch.chdir(tmp_path)

    missing = CliRunner().invoke(app, ["request-changes", story.id])
    result = CliRunner().invoke(
        app,
        ["request-changes", story.id, "--reason", "The proof does not cover the actual device."],
    )

    assert missing.exit_code != 0
    assert result.exit_code == 0
    assert "Queued remediation" in result.stdout
    assert inbox_payload(tmp_path)["stories"][0]["feedback"]["reason"].startswith("The proof")


def test_request_cli_and_product_handoff(tmp_path: Path, monkeypatch) -> None:
    initialize(tmp_path)
    monkeypatch.chdir(tmp_path)

    admitted = CliRunner().invoke(
        app, ["request", "--prompt", "Explain and repair an intermittent startup failure"]
    )
    assert admitted.exit_code == 0
    story_id = admitted.stdout.strip()
    assert next_actions(tmp_path, story_id) == [f"lab run product {story_id} --harness"]

    product = CliRunner().invoke(app, ["run", "product", story_id, "--fake"])
    request_next_action(tmp_path, story_id)
    inbox = CliRunner().invoke(app, ["inbox", "--json"])
    assert product.exit_code == 0
    assert inbox.exit_code == 0
    assert f"lab run builder {story_id} --harness" in inbox.stdout
    assert load_story(tmp_path, story_id).human.implementation_approved


def test_request_is_not_counted_as_product_artifact(tmp_path: Path) -> None:
    initialize(tmp_path)

    story_id = create_request(tmp_path, "Make this understandable", title=None, depth="light")

    assert not load_story(tmp_path, story_id).artifacts.story
    assert not (tmp_path / ".lab/stories" / story_id / "story.md").exists()


def test_light_story_skips_research_after_product_framing(tmp_path: Path) -> None:
    initialize(tmp_path)
    story = create_story(tmp_path, "A small deliverable", lab_depth="full")

    set_story_depth(tmp_path, story.id, "light")

    assert next_actions(tmp_path, story.id) == [f"lab approve implementation {story.id}"]
    assert read_records(tmp_path / ".lab/ledger.jsonl")[-1]["event"] == "depth_changed"
