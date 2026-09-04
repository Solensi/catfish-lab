"""A readable observation console derived from Lab evidence."""

import os
import re
import select
import sys
import textwrap
import threading
import time
from collections.abc import Callable, Iterator
from contextlib import contextmanager
from dataclasses import dataclass
from pathlib import Path

from .artifacts import load_story
from .controller import run_role
from .harnesses import (
    active_profile,
    adapter_for_active,
    profile_availability,
)
from .ledger import read_records, verify_ledger
from .util import sha256_file
from .workflow import (
    next_actions,
    record_delay,
    request_next_action,
)

ROLE_LABELS = {
    "product": ("THE PRODUCT STEWARD", "STORY"),
    "scientist": ("THE SCIENTIST", "HYPOTHESIS"),
    "architect": ("THE ARCHITECT", "PROPOSAL A"),
    "heretic": ("THE BLIND HERETIC", "PROPOSAL B"),
    "builder": ("THE BUILDER", "IMPLEMENTATION"),
    "redteam": ("THE RED TEAM", "REVIEW"),
    "judge": ("THE JUDGE", "TRIAL"),
    "archivist": ("THE ARCHIVIST", "ARCHIVE"),
    "controller": ("CONTROLLER", "EVENT"),
    "human": ("HUMAN", "APPROVAL"),
}

PREFERRED_SECTIONS = {
    "product": ("Statement", "User value"),
    "scientist": ("Hypothesis", "Observation", "Question"),
    "architect": ("Summary", "Core idea"),
    "heretic": ("Summary", "Core idea", "Claim under challenge"),
    "builder": ("Approved scope", "Files changed", "Tests"),
    "redteam": ("Confirmed defects", "Suspected defects", "Design concerns"),
    "judge": ("Overall Verdict", "Acceptance Criterion 1", "Missing Evidence"),
    "archivist": ("Portfolio takeaway", "What happened", "What surprised us"),
}

ROLE_PIPELINE = (
    ("product", "story.md", "Frames value and acceptance criteria"),
    ("scientist", "hypothesis.md", "Turns uncertainty into a testable question"),
    ("architect", "candidates/A.md", "Proposes the maintainable path"),
    ("heretic", "candidates/B.md", "Challenges the obvious path"),
    ("builder", "implementation.md", "Implements the approved direction"),
    ("redteam", "redteam.md", "Hunts reproducible violations"),
    ("judge", "trial.md", "Tests the claim that work is complete"),
    ("archivist", "archive.md", "Preserves the evidence-backed history"),
)

ROLE_TITLES = {
    "product": "Product Steward",
    "scientist": "Scientist",
    "architect": "Architect",
    "heretic": "blind Heretic",
    "builder": "Builder",
    "redteam": "Red Team",
    "judge": "Judge",
    "archivist": "Archivist",
}

ANSI = {
    "reset": "\x1b[0m",
    "bold": "\x1b[1m",
    "dim": "\x1b[2m",
    "cyan": "\x1b[36m",
    "green": "\x1b[32m",
    "yellow": "\x1b[33m",
    "red": "\x1b[31m",
    "magenta": "\x1b[35m",
    "white": "\x1b[37m",
}

BRAND_MARK = "≋<°)))><"
BRAND_PROMISE = "Make the claim. Show the trace."


def _style(value: str, *names: str, enabled: bool) -> str:
    if not enabled:
        return value
    return "".join(ANSI[name] for name in names) + value + ANSI["reset"]


def _poster_header(
    width: int,
    section: str,
    *,
    subtitle: str = BRAND_PROMISE,
    meta: str | None = None,
    styled: bool = False,
) -> list[str]:
    """Render one quiet, recognizable identity line and put content first."""
    width = max(52, width)
    lines = [
        _style(f"{BRAND_MARK}  Catfish Lab / {section}", "bold", "cyan", enabled=styled),
        subtitle,
    ]
    if meta:
        lines.append(_style(meta, "yellow", enabled=styled))
    lines.append("─" * width)
    return lines


def _section_text(text: str, role: str) -> str | None:
    """Extract the first substantive, role-relevant statement from Markdown."""
    sections: dict[str, list[str]] = {}
    current = ""
    for raw in text.splitlines():
        heading = re.match(r"^#{2,}\s+(.+?)\s*$", raw)
        if heading:
            current = heading.group(1)
            sections.setdefault(current, [])
        elif current:
            sections[current].append(raw)
    for wanted in PREFERRED_SECTIONS.get(role, ()):
        lines = sections.get(wanted, [])
        substantive: list[str] = []
        for line in lines:
            cleaned = re.sub(r"^[-*]\s+", "", line.strip())
            cleaned = re.sub(r"^\*\*(Observation|Inference|Recommendation):\*\*\s*", "", cleaned)
            if not cleaned or cleaned in {"None", "N/A", "UNTESTED", "NOT_READY"}:
                if substantive:
                    break
                continue
            substantive.append(cleaned)
            if line.lstrip().startswith(("- ", "* ")):
                break
        if substantive:
            return textwrap.shorten(" ".join(substantive), width=300, placeholder=" …")
    return None


def _artifact_observation(repo_root: Path, record: dict[str, object]) -> tuple[str, str, str]:
    relative = str(record.get("output_artifact", ""))
    if not relative:
        return "No output artifact was recorded.", "ledger event only", "NO ARTIFACT"
    path = repo_root / relative
    if not path.is_file():
        return "The recorded artifact is no longer present.", relative, "MISSING"
    current_hash = sha256_file(path)
    recorded_hash = record.get("output_sha256")
    if not recorded_hash:
        statement = (
            "This legacy role run completed, but its original artifact content was not sealed. "
            "The current file is not quoted as historical evidence."
        )
        return statement, relative, f"LEGACY / UNSEALED · current {current_hash[:19]}"
    if recorded_hash != current_hash:
        statement = (
            "This artifact changed after the recorded run. Its current content is not quoted as "
            "the role's historical report."
        )
        return statement, relative, f"CHANGED SINCE RUN · current {current_hash[:19]}"
    role = str(record.get("role", "controller"))
    statement = _section_text(path.read_text(encoding="utf-8"), role)
    if statement is None:
        statement = "The role produced an artifact, but no substantive report could be extracted."
    seal = f"MATCH · {current_hash[:19]}"
    return statement, relative, seal


def observation(repo_root: Path, record: dict[str, object]) -> tuple[str, str, str, str]:
    story_id = str(record.get("story_id", "LAB"))
    role, kind = ROLE_LABELS.get(
        str(record.get("role", "controller")),
        (str(record.get("role", "UNKNOWN")).upper(), "EVENT"),
    )
    event = record.get("event")
    if event == "story_created":
        statement = f"Registered {story_id}: {record.get('title', 'Untitled')}"
        return (
            role,
            "STORY CREATED",
            statement,
            f"ledger sequence {record.get('sequence', 'legacy')}",
        )
    if event == "approval_recorded":
        statement = (
            f"Submitting the LIGHT request authorized its bounded implementation for {story_id}."
            if record.get("basis") == "light_request_submission"
            else f"Recorded explicit {record.get('gate')} approval for {story_id}."
        )
        return role, kind, statement, f"ledger sequence {record.get('sequence', 'legacy')}"
    if event == "harness_selected":
        available = "ready" if record.get("available") else "not currently available"
        statement = f"Selected {record.get('harness')} as the active harness; {available}."
        return role, "HARNESS CHANGED", statement, str(record.get("detail", "ledger event"))
    if event == "work_delayed":
        harness = record.get("harness") or "active harness"
        statement = f"{story_id} is delayed on {harness}: {record.get('reason')}"
        return role, "DELAYED", statement, f"ledger sequence {record.get('sequence', 'legacy')}"
    if event == "assessment_rejected":
        reason = record.get("reason", "reason not recorded")
        relative = str(record.get("artifact") or "")
        path = repo_root / relative if relative else None
        digest = sha256_file(path) if path and path.is_file() else "missing"
        seal = "MATCH" if digest == record.get("artifact_sha256") else "MISMATCH"
        statement = f"The human sent {story_id} back to the Builder: {reason}"
        return role, "CHANGES REQUESTED", statement, f"{relative}  ·  {seal} · {digest[:19]}"
    if event == "depth_changed":
        statement = f"Routed {story_id} through the {record.get('depth')} workflow."
        sequence = f"ledger sequence {record.get('sequence', 'legacy')}"
        return role, "ROUTE CHANGED", statement, sequence
    if event == "action_requested":
        statement = f"Asked the harness to continue {story_id}: {record.get('action')}"
        sequence = f"ledger sequence {record.get('sequence', 'legacy')}"
        return role, "HARNESS REQUEST", statement, sequence
    if event == "artifact_recorded":
        relative = str(record.get("artifact", ""))
        path = repo_root / relative
        digest = sha256_file(path) if path.is_file() else "missing"
        seal = "MATCH" if digest == record.get("artifact_sha256") else "MISMATCH"
        statement = f"Recorded the completed {record.get('artifact_kind')} artifact for {story_id}."
        return role, "ARTIFACT RECORDED", statement, f"{relative}  ·  {seal} · {digest[:19]}"
    if record.get("status") == "reopened":
        target = str(record.get("stage", "unknown")).split("->")[-1]
        reason = record.get("reason", "reason not recorded")
        relative = str(record.get("artifact") or "")
        preserved = repo_root / relative if relative else None
        finding = None
        if preserved and preserved.is_file():
            finding = _section_text(preserved.read_text(encoding="utf-8"), "redteam")
        statement = (
            f"Red Team: {finding}\nController: returned {story_id} to {target}: {reason}"
            if finding
            else f"Returned {story_id} to {target}: {reason}"
        )
        if preserved and preserved.is_file():
            digest = sha256_file(preserved)
            recorded = record.get("artifact_sha256")
            seal = "MATCH" if recorded == digest else "LEGACY / UNSEALED"
            evidence = f"{relative}  ·  {seal} · {digest[:19]}"
        else:
            evidence = "ledger event; no superseded artifact existed"
        return role, "REOPENED", statement, evidence
    if record.get("status") == "success" and record.get("output_artifact"):
        statement, evidence, seal = _artifact_observation(repo_root, record)
        return role, kind, statement, f"{evidence}  ·  {seal}"
    statement = f"Recorded {event or record.get('status', 'an event')} for {story_id}."
    return role, kind, statement, f"ledger sequence {record.get('sequence', 'legacy')}"


def _wrapped(label: str, value: str, width: int, *, indent: int = 4) -> list[str]:
    label_width = 10 if label else 0
    available = max(24, width - indent - label_width)
    output: list[str] = []
    for paragraph in value.splitlines() or [""]:
        wrapped = textwrap.wrap(paragraph, width=available) or [""]
        if not output:
            prefix = f"{label:<10}" if label else ""
            output.append(f"{' ' * indent}{prefix}{wrapped[0]}")
        else:
            output.append(f"{' ' * (indent + label_width)}{wrapped[0]}")
        output.extend(f"{' ' * (indent + label_width)}{line}" for line in wrapped[1:])
    return output


def _masthead(width: int, harness: str, *, styled: bool) -> list[str]:
    return _poster_header(
        width,
        "Logbook",
        meta=f"Harness: {harness}",
        styled=styled,
    )


def _evidence_bearing(records: list[dict[str, object]]) -> list[dict[str, object]]:
    """Hide historical run summaries whose original content cannot be established."""
    return [
        record
        for record in records
        if not (record.get("output_artifact") and not record.get("output_sha256"))
    ]


def _action_label(action: str) -> str:
    """Translate the harness protocol into one human instruction."""
    parts = action.split()
    if parts[:3] == ["lab", "run", "product"]:
        return "Press a to let the Product Steward scope this request."
    if parts[:3] == ["lab", "run", "builder"]:
        return "Waiting for the coding harness to implement the scoped work."
    if parts[:3] == ["lab", "run", "redteam"]:
        return "Press a to begin independent review."
    if parts[:2] == ["lab", "trial"]:
        return "The Red Team has reported. Press a to test the completion claim."
    if parts[:2] == ["lab", "archive"]:
        return "Press a to let the Archivist preserve the accepted result."
    if parts[:2] == ["lab", "approve"]:
        return f"Press a to review the {parts[2]} decision."
    if parts[:2] == ["lab", "draft"] or parts[:2] == ["lab", "record"]:
        return "Waiting for the coding harness to prepare the next evidence artifact."
    return "The coding harness has the next step."


def _pipeline(repo_root: Path, story_id: str, width: int, *, compact: bool = False) -> list[str]:
    directory = repo_root / ".lab" / "stories" / story_id
    story = load_story(repo_root, story_id)
    lines = ["", "Roles"]
    skipped_names: list[str] = []
    for number, (role, artifact, purpose) in enumerate(ROLE_PIPELINE, 1):
        path = directory / artifact
        skipped = story.lab_depth == "light" and role in {"scientist", "architect", "heretic"}
        if skipped:
            skipped_names.append(ROLE_TITLES[role])
            continue
        ready = path.is_file() and (role != "product" or story.artifacts.story)
        status = "SKIPPED" if skipped and not ready else ("READY" if ready else "WAITING")
        if ready:
            source = path.relative_to(repo_root).as_posix()
        elif role == "product" and (directory / "request.md").is_file():
            source = (directory / "request.md").relative_to(repo_root).as_posix()
        elif skipped:
            source = "not required by light route"
        else:
            source = artifact
        summary = (
            f"[{number}] {ROLE_TITLES[role]:<18} {status.title():<7} · {purpose}"
            if compact
            else f"[{number}] {ROLE_TITLES[role]:<18} {status.title():<7} {purpose}"
        )
        lines.extend(_wrapped("", summary, width, indent=2))
        if not compact:
            lines.extend(_wrapped("", f"↳ {source}", width, indent=6))
    if skipped_names:
        lines.extend(
            _wrapped(
                "FULL ONLY",
                f"[2–4] {' · '.join(skipped_names)} — skipped on the Light route",
                width,
            )
        )
    directory = repo_root / ".lab" / "stories" / story_id

    def middle_status(ready: bool) -> str:
        return "READY" if ready else ("SKIPPED" if story.lab_depth == "light" else "WAITING")

    supporting = (
        (
            "REQUEST",
            "READY" if (directory / "request.md").is_file() else "MANUAL",
            "request.md" if (directory / "request.md").is_file() else "created without prompt",
        ),
        ("CRITIQUE", middle_status(story.artifacts.critiques), "critiques/review.md"),
        ("EXPERIMENT", middle_status(story.artifacts.experiment), "experiment.md"),
        ("EVIDENCE", middle_status(story.artifacts.evidence), "evidence/"),
        ("DECISION", middle_status(story.artifacts.decision), "decision.md"),
    )
    if story.lab_depth == "full":
        lines.extend(("", "Research notes"))
        for name, status, path in supporting:
            lines.append(f"    {name.title():<12} {status.title():<7} {path}")
    actions = next_actions(repo_root, story_id)
    if actions:
        lines.extend(("", "Next"))
        for action in actions:
            lines.extend(_wrapped("", _action_label(action), width))
            if not compact:
                lines.extend(_wrapped("COMMAND", action, width))
    return lines


def render(
    repo_root: Path,
    story_id: str | None = None,
    *,
    width: int = 88,
    styled: bool = False,
    selected_story_id: str | None = None,
    compact_pipeline: bool = True,
    include_reports: bool = True,
) -> str:
    ledger = repo_root / ".lab/ledger.jsonl"
    all_records = read_records(ledger)
    records = all_records
    if story_id:
        records = [record for record in records if record.get("story_id") == story_id]
        story_paths = [repo_root / ".lab/stories" / story_id]
    else:
        story_paths = sorted((repo_root / ".lab/stories").glob("US-*"))
    width = max(52, min(width, 110))
    rule = "┄" * width
    failures = verify_ledger(ledger)
    try:
        selected_harness = active_profile(repo_root)
        available, _ = profile_availability(selected_harness)
        harness = f"{selected_harness.label} · {'READY' if available else 'DELAYED'}"
    except ValueError:
        harness = "NOT CONFIGURED"
    lines = _masthead(width, harness, styled=styled)
    if (repo_root / ".lab/TUTORIAL").is_file():
        lines.append(
            _style(
                "FIRST CAST  ·  synthetic case  ·  no project evidence",
                "bold",
                "yellow",
                enabled=styled,
            )
        )
    lines.extend(
        (
            "Evidence  "
            + _style(
                "BROKEN" if failures else "VERIFIED",
                "red" if failures else "green",
                "bold",
                enabled=styled,
            )
            + f"   ·   {len(records)} recorded interaction(s)",
            "",
            _style("Stories", "bold", "magenta", enabled=styled),
        )
    )
    if not story_paths:
        lines.append("  The board is clear. Press n in live mode to open a case.")
    for story_number, path in enumerate(story_paths, 1):
        try:
            story = load_story(repo_root, path.name)
        except Exception as error:
            lines.append(f"  {path.name}  UNREADABLE  {error}")
            continue
        gates = story.human.model_dump()
        if story.lab_depth == "light":
            gates = {key: gates[key] for key in ("implementation_approved", "done_approved")}
        required_artifacts = (
            ("story", "implementation", "redteam", "trial", "archive")
            if story.lab_depth == "light"
            else tuple(story.artifacts.model_dump())
        )
        artifact_state = story.artifacts.model_dump()
        artifacts = sum(artifact_state[name] for name in required_artifacts)
        story_records = [record for record in all_records if record.get("story_id") == story.id]
        delayed = bool(story_records and story_records[-1].get("event") == "work_delayed")
        marker = "› " if path.name == selected_story_id else "  "
        prefix = f"[{story_number}] " if not story_id else ""
        badge = f"Delayed · {story.stage.value}" if delayed else story.stage.value
        lines.append(
            _style(
                f"{marker}{prefix}{story.id}  ·  {badge.title()}  ·  {story.title}",
                "bold",
                "red" if delayed else "white",
                enabled=styled,
            )
        )
        gate_marks = "  ".join(
            f"{name.removesuffix('_approved')} {'✓' if value else '○'}"
            for name, value in gates.items()
        )
        total = len(required_artifacts)
        progress = "◆" * artifacts + "·" * (total - artifacts)
        progress_label = f"{progress}  {artifacts}/{total} required artifacts"
        lines.extend(_wrapped(story.lab_depth.upper(), progress_label, width))
        lines.extend(_wrapped("APPROVALS", gate_marks, width))
    if story_id:
        lines.extend(_pipeline(repo_root, story_id, width, compact=compact_pipeline))
    if include_reports:
        evidence_records = _evidence_bearing(records)
        noun = "entry" if len(evidence_records) == 1 else "entries"
        section = f"Recent reports  ·  {len(evidence_records)} evidence-bearing {noun}"
        lines.extend(("", _style(section, "bold", enabled=styled)))
        visible = evidence_records[-8:]
        for index, record in enumerate(visible, max(1, len(records) - len(visible) + 1)):
            stamp = str(
                record.get("recorded_at", record.get("completed_at", record.get("timestamp", "")))
            )
            stamp = stamp[11:19] if len(stamp) >= 19 else "--:--:--"
            role, kind, statement, evidence = observation(repo_root, record)
            story = record.get("story_id", "LAB")
            header = f"  LOG-{index:03d}  {stamp}  {role}  ·  {kind}  ·  {story}"
            lines.extend(("", _style(header, "bold", "cyan", enabled=styled)))
            lines.extend(_wrapped("REPORTED", statement, width))
            lines.extend(_wrapped("SOURCE", evidence, width))
        if not records:
            lines.append("  No interactions recorded.")
    if failures:
        lines.extend(("", _style("INTEGRITY WARNINGS", "bold", "red", enabled=styled)))
        lines.extend(f"  ! {failure}" for failure in failures)
    lines.extend(
        (
            "",
            rule,
            "Claims speak; evidence gets the last word.",
            "Narration is derived. Cited artifacts and the JSONL ledger are authoritative.",
        )
    )
    return "\n".join(lines)


@dataclass
class _InteractiveState:
    story_id: str | None = None
    message: str = ""
    busy: bool = False


def _model_role_from_action(action: str) -> str | None:
    parts = action.split()
    if len(parts) >= 4 and parts[:2] == ["lab", "run"]:
        role = parts[2]
        # Builder must use repository tools. Text-only role adapters cannot honestly
        # claim that their patch has been applied, so this is an outer-harness handoff.
        return None if role == "builder" else role
    if len(parts) >= 3 and parts[:2] == ["lab", "trial"]:
        return "judge"
    if len(parts) >= 3 and parts[:2] == ["lab", "archive"]:
        return "archivist"
    return None


def _start_model_action(
    repo_root: Path, state: _InteractiveState, story_id: str, action: str
) -> None:
    role = _model_role_from_action(action)
    if role is None:
        state.message = f"HANDOFF · waiting for the coding harness to perform: {action}"
        return
    harness = active_profile(repo_root)
    state.busy = True
    state.message = f"{ROLE_TITLES[role]} is working through {harness.label}…"

    def work() -> None:
        current_action = action
        current_role = role
        try:
            adapter = adapter_for_active(repo_root)
            while current_role is not None:
                state.message = f"{ROLE_TITLES[current_role]} is working through {harness.label}…"
                run_role(
                    repo_root,
                    role=current_role,
                    story_id=story_id,
                    adapter=adapter,
                )
                following = next_actions(repo_root, story_id)
                if not following:
                    state.message = (
                        f"{ROLE_TITLES[current_role]} reported. This chapter is at rest."
                    )
                    break
                current_action = request_next_action(repo_root, story_id)
                current_role = _model_role_from_action(current_action)
                if current_role is None:
                    if current_action.startswith("lab approve "):
                        state.message = (
                            "HUMAN GATE · the evidence is ready; press [a] to decide: "
                            f"{current_action}"
                        )
                    else:
                        state.message = (
                            "HANDOFF · the isolated roles are done; the coding harness now owns: "
                            f"{current_action}"
                        )
        except Exception as error:
            state.message = f"DELAYED · {error}"
            try:
                record_delay(
                    repo_root,
                    story_id,
                    str(error),
                    harness=harness.name,
                )
            except Exception as ledger_error:  # keep the original failure visible in memory
                state.message = f"DELAYED · {error} · ledger warning: {ledger_error}"
        else:
            if current_role is not None and not next_actions(repo_root, story_id):
                state.message = (
                    f"{ROLE_TITLES[current_role]} reported. The evidence is ready to inspect."
                )
        finally:
            state.busy = False

    threading.Thread(target=work, name=f"catfish-{story_id}-{role}", daemon=True).start()


@contextmanager
def _key_input() -> Iterator[None]:
    """Enable single-key input on POSIX; Windows uses msvcrt without setup."""
    if os.name == "nt":
        yield
        return
    import termios
    import tty

    descriptor = sys.stdin.fileno()
    previous = termios.tcgetattr(descriptor)
    try:
        tty.setcbreak(descriptor)
        yield
    finally:
        termios.tcsetattr(descriptor, termios.TCSADRAIN, previous)


def _read_key(timeout: float) -> str | None:
    if os.name == "nt":
        import msvcrt

        deadline = time.monotonic() + timeout
        while time.monotonic() < deadline:
            if msvcrt.kbhit():
                return msvcrt.getwch()
            time.sleep(0.03)
        return None
    readable, _, _ = select.select([sys.stdin], [], [], timeout)
    return os.read(sys.stdin.fileno(), 1).decode(errors="ignore") if readable else None


def watch(
    repo_root: Path,
    story_id: str | None = None,
    *,
    interval: float = 0.75,
    initial_view: str | None = None,
    tutorial_start: Callable[[], None] | None = None,
    tutorial_pause: Callable[[], bool] | None = None,
) -> None:
    """Open the Textual Logbook, or emit a plain snapshot when output is redirected."""
    del interval  # Retained for compatibility with tutorial and external callers.
    if not sys.stdout.isatty():
        sys.stdout.write(render(repo_root, story_id) + "\n")
        return
    from .tui import run_logbook

    run_logbook(
        repo_root,
        story_id,
        initial_view=initial_view,
        tutorial_start=tutorial_start,
        tutorial_pause=tutorial_pause,
    )
