"""Deterministic role orchestration; reasoning remains inside the adapter."""

import json
import secrets
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path

from .archive import write_evidence_index
from .artifacts import load_story, save_story, story_dir
from .capsule import CapabilityManifest, Isolation, context_digest
from .context import resolve_context
from .ledger import append_record
from .model import LabModelAdapter, LabModelRequest
from .roles import contract_for
from .stages import Stage
from .util import sha256_bytes, sha256_file


class OutputContractError(ValueError):
    pass


@dataclass(frozen=True)
class AssessmentRejection:
    """Durable human feedback plus the artifacts superseded by that decision."""

    feedback: Path
    preserved: tuple[Path, ...]


def reject_assessment(repo_root: Path, *, story_id: str, reason: str) -> AssessmentRejection:
    """Send a completion assessment back to the Builder with explicit human feedback."""

    story = load_story(repo_root, story_id)
    reason = reason.strip()
    if story.stage is not Stage.TRIAL or not story.artifacts.trial:
        raise ValueError("only a completed trial assessment can be sent back")
    if not reason:
        raise ValueError("a rejection reason is required")
    if len(reason.encode()) > 20_000:
        raise ValueError("a rejection reason cannot exceed 20 KB")

    timestamp = datetime.now(UTC)
    stamp = timestamp.strftime("%Y%m%dT%H%M%S%fZ")
    directory = story_dir(repo_root, story_id)
    evidence = directory / "evidence"
    evidence.mkdir(parents=True, exist_ok=True)
    preserved: list[Path] = []
    preserved_records: list[dict[str, str]] = []
    for name in ("implementation.md", "redteam.md", "trial.md"):
        source = directory / name
        if not source.is_file():
            continue
        destination = evidence / f"superseded-{source.stem}-{stamp}.md"
        source.replace(destination)
        preserved.append(destination)
        preserved_records.append(
            {
                "path": destination.relative_to(repo_root).as_posix(),
                "sha256": sha256_file(destination),
            }
        )

    feedback = evidence / f"human-feedback-{stamp}.md"
    feedback.write_text(
        "# Human Assessment Feedback\n\n"
        f"Story: {story_id}\n\n"
        "Outcome: changes requested\n\n"
        "## Why the assessment was not accepted\n\n"
        f"{reason}\n\n"
        "## Required response\n\n"
        "The Builder must address this feedback before the Red Team and Judge run again.\n",
        encoding="utf-8",
    )
    artifacts = story.artifacts.model_copy(
        update={"implementation": False, "redteam": False, "trial": False, "archive": False}
    )
    human = story.human.model_copy(update={"done_approved": False})
    save_story(
        repo_root,
        story.model_copy(
            update={
                "stage": Stage.IMPLEMENTATION,
                "artifacts": artifacts,
                "human": human,
                "updated_at": timestamp,
            }
        ),
    )
    append_record(
        repo_root / ".lab/ledger.jsonl",
        {
            "timestamp": timestamp.isoformat(),
            "event": "assessment_rejected",
            "story_id": story_id,
            "role": "human",
            "stage": "trial->implementation",
            "reason": reason,
            "artifact": feedback.relative_to(repo_root).as_posix(),
            "artifact_sha256": sha256_file(feedback),
            "preserved_artifacts": preserved_records,
            "status": "rejected",
        },
    )
    return AssessmentRejection(feedback=feedback, preserved=tuple(preserved))


def reopen_story(repo_root: Path, *, story_id: str, target: Stage, reason: str) -> Path | None:
    """Move a story back for remediation while preserving the superseded review."""
    story = load_story(repo_root, story_id)
    permitted = {
        Stage.REDTEAM: {Stage.IMPLEMENTATION},
        Stage.TRIAL: {Stage.IMPLEMENTATION, Stage.REDTEAM},
    }
    if target not in permitted.get(story.stage, set()):
        raise ValueError(f"illegal backward transition: {story.stage.value} -> {target.value}")
    if not reason.strip():
        raise ValueError("a reopening reason is required")

    preserved: Path | None = None
    source_names = {Stage.REDTEAM: "redteam.md", Stage.TRIAL: "trial.md"}
    source = story_dir(repo_root, story_id) / source_names[story.stage]
    timestamp = datetime.now(UTC)
    if source.exists():
        preserved = (
            story_dir(repo_root, story_id)
            / "evidence"
            / (f"{story.stage.value}-{timestamp.strftime('%Y%m%dT%H%M%S%fZ')}.md")
        )
        preserved.parent.mkdir(parents=True, exist_ok=True)
        preserved.write_bytes(source.read_bytes())

    reset = {"redteam": False, "trial": False, "archive": False}
    if target is Stage.REDTEAM:
        reset["redteam"] = True
    save_story(
        repo_root,
        story.model_copy(
            update={
                "stage": target,
                "updated_at": timestamp,
                "artifacts": story.artifacts.model_copy(update=reset),
            }
        ),
    )
    append_record(
        repo_root / ".lab/ledger.jsonl",
        {
            "timestamp": timestamp.isoformat(),
            "story_id": story_id,
            "role": "controller",
            "stage": f"{story.stage.value}->{target.value}",
            "artifact": preserved.relative_to(repo_root).as_posix() if preserved else None,
            "artifact_sha256": sha256_file(preserved) if preserved else None,
            "status": "reopened",
            "reason": reason.strip(),
        },
    )
    return preserved


def _validate_output(role: str, text: str, template: str) -> None:
    if not text.strip():
        raise OutputContractError("model output is empty")
    if len(text.encode()) > 200_000:
        raise OutputContractError("model output exceeds 200 KB")
    required = [line for line in template.splitlines() if line.startswith("# ")]
    if required and required[0] not in text:
        raise OutputContractError(f"required heading missing: {required[0]}")
    if role == "builder" and ("No patch produced" in text or "## Files changed\n\nNone" in text):
        raise OutputContractError("Builder output contains no implementation change")


def run_role(
    repo_root: Path,
    *,
    role: str,
    story_id: str,
    adapter: LabModelAdapter,
) -> Path:
    story = load_story(repo_root, story_id)
    allowed_stages = {
        "product": {Stage.STORY},
        "scientist": {Stage.STORY},
        "architect": {Stage.HYPOTHESIS, Stage.PROPOSALS},
        "heretic": {Stage.HYPOTHESIS, Stage.PROPOSALS},
        "builder": {Stage.STORY, Stage.DECISION, Stage.IMPLEMENTATION},
        "redteam": {Stage.IMPLEMENTATION},
        "judge": {Stage.REDTEAM},
        "archivist": {Stage.TRIAL, Stage.APPROVED, Stage.DONE},
    }
    if story.stage not in allowed_stages[role]:
        raise ValueError(f"role {role} cannot run at stage {story.stage.value}")
    if role == "builder" and not story.human.implementation_approved:
        raise ValueError("human implementation approval is required before Builder")
    if (
        role == "builder"
        and story.lab_depth == "full"
        and story.stage not in {Stage.DECISION, Stage.IMPLEMENTATION}
    ):
        raise ValueError("a full-depth Builder requires the decision stage")
    if role == "builder" and story.stage is Stage.IMPLEMENTATION and story.artifacts.implementation:
        raise ValueError(
            "the current implementation must be sent back before Builder can revise it"
        )
    contract = contract_for(role, story_id, repo_root)
    if role == "archivist":
        write_evidence_index(repo_root, story_id)
    constitution = (repo_root / ".lab/constitution.md").read_text(encoding="utf-8")
    role_prompt = (repo_root / f".lab/roles/{role}.md").read_text(encoding="utf-8")
    template = (repo_root / f".lab/templates/{contract.template}").read_text(encoding="utf-8")
    paths = resolve_context(repo_root, contract.policy)
    context_files = [
        {"path": path.relative_to(repo_root).as_posix(), "sha256": sha256_file(path)}
        for path in paths
    ]
    visible = "\n\n".join(
        f"--- {path.relative_to(repo_root).as_posix()} ---\n{path.read_text(encoding='utf-8')}"
        for path in paths
    )
    capabilities = CapabilityManifest("none", False, False)
    prompt = (
        "You are one role inside Catfish Lab. You do not inherit conversational memory.\n\n"
        f"CONSTITUTION\n{constitution}\n\nROLE\n{role_prompt}\n\n"
        f"VISIBLE CONTEXT\n{visible}\n\nOUTPUT CONTRACT\n{template}\n\n"
        "Return only the requested artifact content."
    )
    started = datetime.now(UTC)
    response = adapter.complete(LabModelRequest(system="Catfish Lab isolated role", prompt=prompt))
    _validate_output(role, response.text, template)
    destination = story_dir(repo_root, story_id) / contract.artifact
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text(response.text.rstrip() + "\n", encoding="utf-8")
    completed = datetime.now(UTC)
    run_id = f"run_{started.strftime('%Y%m%dT%H%M%S')}_{secrets.token_hex(4)}"
    digest = context_digest(
        role_hash=sha256_bytes(role_prompt.encode()),
        constitution_hash=sha256_bytes(constitution.encode()),
        files=context_files,
        task_hash=sha256_bytes(story_id.encode()),
        capabilities=capabilities,
    )
    record = {
        "run_id": run_id,
        "role": role,
        "story_id": story_id,
        "started_at": started.isoformat(),
        "completed_at": completed.isoformat(),
        "provider": response.provider,
        "model_id": response.model_id,
        "temperature": None,
        "isolation": Isolation.TEXT_ONLY.value,
        "capabilities": capabilities.__dict__,
        "context_digest": digest,
        "context_files": context_files,
        "prompt_sha256": sha256_bytes(prompt.encode()),
        "output_artifact": destination.relative_to(repo_root).as_posix(),
        "output_sha256": sha256_file(destination),
        "status": "success",
    }
    run_path = repo_root / ".lab/runs" / f"{run_id}.json"
    run_path.write_text(json.dumps(record, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    append_record(
        repo_root / ".lab/ledger.jsonl",
        {
            key: record[key]
            for key in (
                "completed_at",
                "story_id",
                "run_id",
                "role",
                "model_id",
                "prompt_sha256",
                "output_artifact",
                "output_sha256",
                "status",
            )
        },
    )
    artifact_updates: dict[str, bool] = {}
    next_stage = story.stage
    if role == "product":
        artifact_updates["story"] = True
    elif role == "scientist":
        artifact_updates["hypothesis"] = True
        next_stage = Stage.HYPOTHESIS
    elif role == "architect":
        artifact_updates["candidate_a"] = True
    elif role == "heretic":
        artifact_updates["candidate_b"] = True
    elif role == "builder":
        artifact_updates["implementation"] = True
        next_stage = Stage.IMPLEMENTATION
    elif role == "redteam":
        artifact_updates["redteam"] = True
        next_stage = Stage.REDTEAM
    elif role == "judge":
        artifact_updates["trial"] = True
        next_stage = Stage.TRIAL
    elif role == "archivist":
        artifact_updates["archive"] = True
    artifacts = story.artifacts.model_copy(update=artifact_updates)
    if role in {"architect", "heretic"} and artifacts.candidate_a and artifacts.candidate_b:
        next_stage = Stage.PROPOSALS
    save_story(
        repo_root,
        story.model_copy(
            update={"artifacts": artifacts, "stage": next_stage, "updated_at": completed}
        ),
    )
    if role == "archivist":
        write_evidence_index(repo_root, story_id)
    return destination
