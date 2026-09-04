import pytest

from lab.stages import (
    HumanGates,
    Stage,
    StageTransitionError,
    validate_distinct_reviewers,
    validate_transition,
)


def test_human_experiment_gate() -> None:
    with pytest.raises(StageTransitionError):
        validate_transition(Stage.EXPERIMENT_READY, Stage.EVIDENCE, HumanGates())


def test_human_done_gate_and_contradiction_gate() -> None:
    with pytest.raises(StageTransitionError):
        validate_transition(Stage.TRIAL, Stage.APPROVED, HumanGates())
    with pytest.raises(StageTransitionError):
        validate_transition(
            Stage.TRIAL,
            Stage.APPROVED,
            HumanGates(done_approved=True),
            contradicted_criteria=True,
        )


def test_builder_cannot_self_judge() -> None:
    with pytest.raises(StageTransitionError):
        validate_distinct_reviewers("run-1", "run-1")
