"""Human-readable workflow guidance and non-model artifact transitions."""

import json
import textwrap
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path

from .artifacts import create_story, load_story, save_story, story_dir
from .config import TEMPLATES
from .harnesses import active_profile
from .ledger import append_record, read_records
from .stages import HumanGates, Stage, validate_transition
from .util import sha256_file


@dataclass(frozen=True)
class RecordedArtifact:
    kind: str
    current: Stage
    target: Stage
    relative_path: str
    heading: str | None
    flag: str


RECORDED_ARTIFACTS = {
    "critique": RecordedArtifact(
        "critique",
        Stage.PROPOSALS,
        Stage.CRITIQUE,
        "critiques/review.md",
        "# Critique",
        "critiques",
    ),
    "experiment": RecordedArtifact(
        "experiment",
        Stage.CRITIQUE,
        Stage.EXPERIMENT_READY,
        "experiment.md",
        "# Experiment",
        "experiment",
    ),
    "evidence": RecordedArtifact(
        "evidence", Stage.EVIDENCE, Stage.EVIDENCE, "evidence/{name}", None, "evidence"
    ),
    "decision": RecordedArtifact(
        "decision", Stage.EVIDENCE, Stage.DECISION, "decision.md", "# Decision", "decision"
    ),
}


def draft_artifact(repo_root: Path, story_id: str, kind: str) -> Path:
    """Create an editable supporting-artifact draft without claiming workflow progress."""
    if kind not in {"critique", "experiment", "decision"}:
        raise ValueError("kind must be critique, experiment, or decision")
    story = load_story(repo_root, story_id)
    destination = story_dir(repo_root, story_id) / "drafts" / f"{kind}.md"
    if destination.exists():
        raise ValueError(f"draft already exists: {destination.relative_to(repo_root)}")
    destination.parent.mkdir(parents=True, exist_ok=True)
    content = TEMPLATES[kind].replace("US-___", story.id)
    destination.write_text(content, encoding="utf-8")
    return destination


def approve_story(repo_root: Path, story_id: str, kind: str) -> None:
    """Apply an already-authorized human gate and its deterministic transition."""
    if kind not in {"experiment", "implementation", "done"}:
        raise ValueError("kind must be experiment, implementation, or done")
    story = load_story(repo_root, story_id)
    if kind == "experiment":
        if story.stage is not Stage.EXPERIMENT_READY or not story.artifacts.experiment:
            raise ValueError("a recorded experiment at experiment_ready is required")
        next_stage = Stage.EVIDENCE
    elif kind == "implementation":
        full_ready = story.stage is Stage.DECISION and story.artifacts.decision
        light_ready = story.lab_depth == "light" and story.stage is Stage.STORY
        if not (full_ready or light_ready):
            raise ValueError("a full story requires a recorded decision before approval")
        next_stage = story.stage
    else:
        trial = story_dir(repo_root, story_id) / "trial.md"
        if story.stage is not Stage.TRIAL or not trial.is_file():
            raise ValueError("a completion trial is required before done approval")
        verdict = trial.read_text(encoding="utf-8").partition("## Overall Verdict")[2]
        if "READY" not in verdict or "NOT_READY" in verdict:
            raise ValueError("the completion trial does not contain a READY verdict")
        next_stage = Stage.DONE
    human = story.human.model_copy(update={f"{kind}_approved": True})
    now = datetime.now(UTC)
    save_story(
        repo_root,
        story.model_copy(update={"human": human, "stage": next_stage, "updated_at": now}),
    )
    append_record(
        repo_root / ".lab/ledger.jsonl",
        {
            "event": "approval_recorded",
            "role": "human",
            "story_id": story_id,
            "gate": kind,
            "status": "success",
        },
    )


def create_request(repo_root: Path, prompt: str, *, title: str | None, depth: str) -> str:
    """Turn arbitrary input into a durable request without logging a dedicated prompt field."""
    prompt = prompt.strip()
    if not prompt:
        raise ValueError("request prompt cannot be empty")
    if len(prompt.encode()) > 200_000:
        raise ValueError("request prompt exceeds 200 KB")
    if depth not in {"light", "full"}:
        raise ValueError("depth must be light or full")
    derived = textwrap.shorten(" ".join(prompt.split()), width=72, placeholder=" …")
    story = create_story(repo_root, title or derived, lab_depth=depth, request=prompt)
    if depth == "light":
        _authorize_light_request(repo_root, story.id)
    return story.id


def _authorize_light_request(repo_root: Path, story_id: str) -> None:
    """Treat submission of a bounded light request as its implementation authority."""
    story = load_story(repo_root, story_id)
    if story.human.implementation_approved:
        return
    human = story.human.model_copy(update={"implementation_approved": True})
    save_story(
        repo_root,
        story.model_copy(update={"human": human, "updated_at": datetime.now(UTC)}),
    )
    append_record(
        repo_root / ".lab/ledger.jsonl",
        {
            "event": "approval_recorded",
            "role": "human",
            "story_id": story_id,
            "gate": "implementation",
            "basis": "light_request_submission",
            "status": "success",
        },
    )


def set_story_depth(repo_root: Path, story_id: str, depth: str) -> None:
    """Change routing depth while a story has not advanced beyond product framing."""
    if depth not in {"light", "full"}:
        raise ValueError("depth must be light or full")
    story = load_story(repo_root, story_id)
    if story.stage is not Stage.STORY or any(
        (
            story.artifacts.hypothesis,
            story.artifacts.candidate_a,
            story.artifacts.candidate_b,
            story.artifacts.implementation,
        )
    ):
        raise ValueError("depth can only change before research or implementation begins")
    if story.lab_depth == depth:
        return
    human = story.human
    if depth == "light" and (story_dir(repo_root, story_id) / "request.md").is_file():
        human = human.model_copy(update={"implementation_approved": True})
    elif depth == "full":
        human = human.model_copy(update={"implementation_approved": False})
    save_story(
        repo_root,
        story.model_copy(
            update={"lab_depth": depth, "human": human, "updated_at": datetime.now(UTC)}
        ),
    )
    append_record(
        repo_root / ".lab/ledger.jsonl",
        {
            "event": "depth_changed",
            "role": "human",
            "story_id": story_id,
            "depth": depth,
            "implementation_authorized": human.implementation_approved,
            "status": "success",
        },
    )


def request_next_action(repo_root: Path, story_id: str) -> str:
    """Place the next deterministic action in the ledger for an external harness proxy."""
    actions = next_actions(repo_root, story_id)
    if not actions:
        raise ValueError(f"{story_id} has no pending action")
    action = actions[0]
    records = [
        record
        for record in read_records(repo_root / ".lab/ledger.jsonl")
        if record.get("story_id") == story_id
    ]
    if (
        records
        and records[-1].get("event") == "action_requested"
        and records[-1].get("action") == action
    ):
        return action
    append_record(
        repo_root / ".lab/ledger.jsonl",
        {
            "event": "action_requested",
            "role": "human",
            "story_id": story_id,
            "action": action,
            "status": "pending",
        },
    )
    return action


def record_delay(
    repo_root: Path, story_id: str, reason: str, *, harness: str | None = None
) -> None:
    """Expose a blocked or failed proxy action without pretending progress occurred."""
    load_story(repo_root, story_id)
    reason = " ".join(reason.split())
    if not reason:
        raise ValueError("a delay reason is required")
    append_record(
        repo_root / ".lab/ledger.jsonl",
        {
            "event": "work_delayed",
            "role": "controller",
            "story_id": story_id,
            "harness": harness,
            "reason": textwrap.shorten(reason, width=500, placeholder=" …"),
            "status": "delayed",
        },
    )


def inbox_payload(repo_root: Path, *, include_idle: bool = False) -> dict[str, object]:
    """Return explicitly queued work, with an opt-in diagnostic view of idle stories."""
    ledger = read_records(repo_root / ".lab/ledger.jsonl")
    stories = []
    for directory in sorted((repo_root / ".lab/stories").glob("US-*")):
        story = load_story(repo_root, directory.name)
        request = directory / "request.md"
        story_records = [record for record in ledger if record.get("story_id") == story.id]
        latest = story_records[-1] if story_records else None
        pending = None
        if latest and latest.get("event") in {"action_requested", "work_delayed"}:
            pending = next(
                (
                    record
                    for record in reversed(story_records)
                    if record.get("event") == "action_requested"
                ),
                None,
            )
        delay = latest if latest and latest.get("event") == "work_delayed" else None
        feedback = next(
            (
                record
                for record in reversed(story_records)
                if record.get("event") == "assessment_rejected"
            ),
            None,
        )
        if not include_idle and pending is None:
            continue
        stories.append(
            {
                "id": story.id,
                "title": story.title,
                "stage": story.stage.value,
                "depth": story.lab_depth,
                "request_artifact": (
                    request.relative_to(repo_root).as_posix() if request.is_file() else None
                ),
                "next_actions": next_actions(repo_root, story.id),
                "requested_action": pending.get("action") if pending else None,
                "requested_event_id": pending.get("event_id") if pending else None,
                "delay": (
                    {
                        "reason": delay.get("reason"),
                        "harness": delay.get("harness"),
                        "event_id": delay.get("event_id"),
                    }
                    if delay
                    else None
                ),
                "feedback": (
                    {
                        "reason": feedback.get("reason"),
                        "artifact": feedback.get("artifact"),
                        "event_id": feedback.get("event_id"),
                    }
                    if feedback
                    else None
                ),
                "human_gates": story.human.model_dump(),
                "artifacts": story.artifacts.model_dump(),
            }
        )
    harness = active_profile(repo_root)
    return {
        "schema_version": 1,
        "active_harness": {
            "name": harness.name,
            "label": harness.label,
            "kind": harness.kind,
            "model": harness.model,
        },
        "stories": stories,
    }


def inbox_json(repo_root: Path, *, include_idle: bool = False) -> str:
    return json.dumps(inbox_payload(repo_root, include_idle=include_idle), indent=2, sort_keys=True)


def _role_completed(repo_root: Path, story_id: str, role: str) -> bool:
    return any(
        record.get("story_id") == story_id
        and record.get("role") == role
        and record.get("status") == "success"
        for record in read_records(repo_root / ".lab/ledger.jsonl")
    )


def record_artifact(repo_root: Path, story_id: str, kind: str, source: Path) -> Path:
    """Import a completed human/harness artifact and advance deterministic state."""
    try:
        contract = RECORDED_ARTIFACTS[kind]
    except KeyError as error:
        raise ValueError("kind must be critique, experiment, evidence, or decision") from error
    story = load_story(repo_root, story_id)
    if story.stage is not contract.current:
        raise ValueError(
            f"{kind} can only be recorded at {contract.current.value}; "
            f"{story_id} is at {story.stage.value}"
        )
    if kind == "decision" and not story.artifacts.evidence:
        raise ValueError("record evidence before the human decision")
    source = source.resolve()
    if not source.is_file():
        raise ValueError(f"artifact source is not a file: {source}")
    payload = source.read_bytes()
    if not payload or len(payload) > 2_000_000:
        raise ValueError("artifact must contain between 1 byte and 2 MB")
    text = payload.decode("utf-8")
    if contract.heading and contract.heading not in text:
        raise ValueError(f"artifact is missing required heading: {contract.heading}")
    name = source.name
    if name in {"EVIDENCE.md", "evidence-index.json"}:
        raise ValueError("that filename is reserved for generated evidence indexes")
    relative = contract.relative_path.format(name=name)
    destination = story_dir(repo_root, story_id) / relative
    if destination.exists():
        raise ValueError(f"artifact already exists: {destination.relative_to(repo_root)}")
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_bytes(payload)
    if contract.target is not contract.current:
        validate_transition(
            story.stage,
            contract.target,
            HumanGates(**story.human.model_dump()),
        )
    artifacts = story.artifacts.model_copy(update={contract.flag: True})
    save_story(
        repo_root,
        story.model_copy(
            update={
                "stage": contract.target,
                "artifacts": artifacts,
                "updated_at": datetime.now(UTC),
            }
        ),
    )
    relative_destination = destination.relative_to(repo_root).as_posix()
    append_record(
        repo_root / ".lab/ledger.jsonl",
        {
            "event": "artifact_recorded",
            "role": "human",
            "story_id": story_id,
            "artifact_kind": kind,
            "artifact": relative_destination,
            "artifact_sha256": sha256_file(destination),
            "status": "success",
        },
    )
    return destination


def next_actions(repo_root: Path, story_id: str) -> list[str]:
    story = load_story(repo_root, story_id)
    if story.stage is Stage.STORY:
        request = story_dir(repo_root, story_id) / "request.md"
        if request.is_file() and not _role_completed(repo_root, story_id, "product"):
            return [f"lab run product {story_id} --harness"]
        if story.lab_depth == "light":
            if not story.human.implementation_approved:
                return [f"lab approve implementation {story_id}"]
            return [f"lab run builder {story_id} --harness"]
        return [f"lab run scientist {story_id} --harness"]
    if story.stage is Stage.HYPOTHESIS:
        actions = []
        if not story.artifacts.candidate_a:
            actions.append(f"lab run architect {story_id} --harness")
        if not story.artifacts.candidate_b:
            actions.append(f"lab run heretic {story_id} --harness")
        return actions
    if story.stage is Stage.PROPOSALS:
        draft = story_dir(repo_root, story_id) / "drafts/critique.md"
        return [
            f"lab record critique {story_id} --from {draft.relative_to(repo_root)}"
            if draft.exists()
            else f"lab draft critique {story_id}"
        ]
    if story.stage is Stage.CRITIQUE:
        draft = story_dir(repo_root, story_id) / "drafts/experiment.md"
        return [
            f"lab record experiment {story_id} --from {draft.relative_to(repo_root)}"
            if draft.exists()
            else f"lab draft experiment {story_id}"
        ]
    if story.stage is Stage.EXPERIMENT_READY:
        return [f"lab approve experiment {story_id}"]
    if story.stage is Stage.EVIDENCE:
        if not story.artifacts.evidence:
            return [f"lab record evidence {story_id} --from RESULTS_FILE"]
        draft = story_dir(repo_root, story_id) / "drafts/decision.md"
        return [
            f"lab record decision {story_id} --from {draft.relative_to(repo_root)}"
            if draft.exists()
            else f"lab draft decision {story_id}"
        ]
    if story.stage is Stage.DECISION:
        if not story.human.implementation_approved:
            return [f"lab approve implementation {story_id}"]
        return [f"lab run builder {story_id} --harness"]
    if story.stage is Stage.IMPLEMENTATION:
        if not story.artifacts.implementation:
            return [f"lab run builder {story_id} --harness"]
        return [f"lab run redteam {story_id} --harness"]
    if story.stage is Stage.REDTEAM:
        return [f"lab trial {story_id} --harness"]
    if story.stage is Stage.TRIAL:
        return [f"lab approve done {story_id}"]
    if story.stage in {Stage.APPROVED, Stage.DONE}:
        return [] if story.artifacts.archive else [f"lab archive {story_id} --harness"]
    return []
