from pathlib import Path

import pytest

from lab.artifacts import create_story, load_story, save_story
from lab.config import TEMPLATES, initialize
from lab.controller import reject_assessment, reopen_story, run_role
from lab.ledger import read_records
from lab.model import FakeModelAdapter
from lab.stages import Stage
from lab.workflow import next_actions


def prepare_repo(tmp_path: Path):
    initialize(tmp_path)
    return create_story(tmp_path, "Controller test")


def test_builder_requires_human_implementation_gate(tmp_path: Path) -> None:
    story = prepare_repo(tmp_path)
    with pytest.raises(ValueError, match="human implementation approval"):
        run_role(
            tmp_path,
            role="builder",
            story_id=story.id,
            adapter=FakeModelAdapter([TEMPLATES["implementation"]]),
        )


def test_light_builder_advances_state_and_records_artifact(tmp_path: Path) -> None:
    story = prepare_repo(tmp_path)
    approved = story.model_copy(
        update={"human": story.human.model_copy(update={"implementation_approved": True})}
    )
    save_story(tmp_path, approved)
    run_role(
        tmp_path,
        role="builder",
        story_id=story.id,
        adapter=FakeModelAdapter([TEMPLATES["implementation"]]),
    )
    updated = load_story(tmp_path, story.id)
    assert updated.stage.value == "implementation"
    assert updated.artifacts.implementation


def test_full_builder_does_not_fall_back_to_proposals(tmp_path: Path) -> None:
    story = prepare_repo(tmp_path)
    ready = story.model_copy(
        update={
            "lab_depth": "full",
            "stage": Stage.DECISION,
            "human": story.human.model_copy(update={"implementation_approved": True}),
            "artifacts": story.artifacts.model_copy(
                update={"candidate_a": True, "candidate_b": True, "decision": True}
            ),
        }
    )
    save_story(tmp_path, ready)

    run_role(
        tmp_path,
        role="builder",
        story_id=story.id,
        adapter=FakeModelAdapter([TEMPLATES["implementation"]]),
    )

    assert load_story(tmp_path, story.id).stage is Stage.IMPLEMENTATION


def test_reopen_preserves_review_and_records_backward_transition(tmp_path: Path) -> None:
    story = prepare_repo(tmp_path)
    directory = tmp_path / ".lab" / "stories" / story.id
    review = "# Red Team Report\n\nConfirmed defect.\n"
    (directory / "redteam.md").write_text(review)
    save_story(
        tmp_path,
        story.model_copy(
            update={
                "stage": Stage.REDTEAM,
                "artifacts": story.artifacts.model_copy(
                    update={"implementation": True, "redteam": True}
                ),
            }
        ),
    )

    preserved = reopen_story(
        tmp_path,
        story_id=story.id,
        target=Stage.IMPLEMENTATION,
        reason="confirmed defect requires remediation",
    )

    assert preserved is not None
    assert preserved.read_text() == review
    updated = load_story(tmp_path, story.id)
    assert updated.stage is Stage.IMPLEMENTATION
    assert not updated.artifacts.redteam
    assert '"status": "reopened"' in (tmp_path / ".lab" / "ledger.jsonl").read_text()


def test_reopen_rejects_forward_transition(tmp_path: Path) -> None:
    story = prepare_repo(tmp_path)
    with pytest.raises(ValueError, match="illegal backward transition"):
        reopen_story(
            tmp_path,
            story_id=story.id,
            target=Stage.REDTEAM,
            reason="not a backward transition",
        )


def test_rejected_assessment_preserves_work_and_returns_feedback_to_builder(
    tmp_path: Path,
) -> None:
    story = prepare_repo(tmp_path)
    directory = tmp_path / ".lab" / "stories" / story.id
    for name, heading in (
        ("implementation.md", "# Implementation"),
        ("redteam.md", "# Red Team Report"),
        ("trial.md", "# Completion Trial\n\n## Overall Verdict\n\nREADY"),
    ):
        (directory / name).write_text(f"{heading}\n\nPrevious result.\n")
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

    rejection = reject_assessment(
        tmp_path,
        story_id=story.id,
        reason="The keyboard path still traps me in the story rail.",
    )

    updated = load_story(tmp_path, story.id)
    assert updated.stage is Stage.IMPLEMENTATION
    assert not updated.artifacts.implementation
    assert not updated.artifacts.redteam
    assert not updated.artifacts.trial
    assert next_actions(tmp_path, story.id) == [f"lab run builder {story.id} --harness"]
    assert "keyboard path" in rejection.feedback.read_text()
    assert len(rejection.preserved) == 3
    assert not (directory / "trial.md").exists()
    event = read_records(tmp_path / ".lab/ledger.jsonl")[-1]
    assert event["event"] == "assessment_rejected"
    assert event["artifact"] == rejection.feedback.relative_to(tmp_path).as_posix()
