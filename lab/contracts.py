"""Validated Lab story and run contracts."""

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

from .stages import Stage


class LabContract(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)


class HumanState(LabContract):
    experiment_approved: bool = False
    implementation_approved: bool = False
    done_approved: bool = False


class ArtifactState(LabContract):
    story: bool = False
    hypothesis: bool = False
    candidate_a: bool = False
    candidate_b: bool = False
    critiques: bool = False
    experiment: bool = False
    evidence: bool = False
    decision: bool = False
    implementation: bool = False
    redteam: bool = False
    trial: bool = False
    archive: bool = False


class StoryState(LabContract):
    id: str = Field(pattern=r"^US-[0-9]{3,}$")
    title: str = Field(min_length=1, max_length=160)
    stage: Stage = Stage.STORY
    lab_depth: Literal["light", "full"] = "light"
    created_at: datetime
    updated_at: datetime
    human: HumanState = Field(default_factory=HumanState)
    artifacts: ArtifactState = Field(default_factory=ArtifactState)
