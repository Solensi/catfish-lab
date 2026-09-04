"""Story transitions and human-gate enforcement."""

from dataclasses import dataclass
from enum import StrEnum


class Stage(StrEnum):
    IDEA = "idea"
    STORY = "story"
    HYPOTHESIS = "hypothesis"
    PROPOSALS = "proposals"
    CRITIQUE = "critique"
    EXPERIMENT_READY = "experiment_ready"
    EVIDENCE = "evidence"
    DECISION = "decision"
    IMPLEMENTATION = "implementation"
    REDTEAM = "redteam"
    TRIAL = "trial"
    APPROVED = "approved"
    DONE = "done"


FORWARD_TRANSITIONS = {
    Stage.IDEA: Stage.STORY,
    Stage.STORY: Stage.HYPOTHESIS,
    Stage.HYPOTHESIS: Stage.PROPOSALS,
    Stage.PROPOSALS: Stage.CRITIQUE,
    Stage.CRITIQUE: Stage.EXPERIMENT_READY,
    Stage.EXPERIMENT_READY: Stage.EVIDENCE,
    Stage.EVIDENCE: Stage.DECISION,
    Stage.DECISION: Stage.IMPLEMENTATION,
    Stage.IMPLEMENTATION: Stage.REDTEAM,
    Stage.REDTEAM: Stage.TRIAL,
    Stage.TRIAL: Stage.APPROVED,
    Stage.APPROVED: Stage.DONE,
}


class StageTransitionError(ValueError):
    pass


def validate_distinct_reviewers(builder_run_id: str, judge_run_id: str) -> None:
    if builder_run_id == judge_run_id:
        raise StageTransitionError("a Builder run cannot serve as its own Judge")


@dataclass(frozen=True)
class HumanGates:
    experiment_approved: bool = False
    implementation_approved: bool = False
    done_approved: bool = False


def validate_transition(
    current: Stage,
    target: Stage,
    gates: HumanGates,
    *,
    contradicted_criteria: bool = False,
) -> None:
    if FORWARD_TRANSITIONS.get(current) is not target:
        raise StageTransitionError(f"illegal transition: {current.value} -> {target.value}")
    if current is Stage.EXPERIMENT_READY and not gates.experiment_approved:
        raise StageTransitionError("human experiment approval is required")
    if current is Stage.DECISION and not gates.implementation_approved:
        raise StageTransitionError("human implementation approval is required")
    if current is Stage.TRIAL:
        if not gates.done_approved:
            raise StageTransitionError("human done approval is required")
        if contradicted_criteria:
            raise StageTransitionError("contradicted acceptance criteria block approval")
