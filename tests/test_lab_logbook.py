import time
from pathlib import Path

from typer.testing import CliRunner

from lab.artifacts import create_story, save_story
from lab.cli import app
from lab.config import TEMPLATES, initialize
from lab.ledger import append_record, read_records
from lab.logbook import (
    _InteractiveState,
    _start_model_action,
    observation,
    render,
)
from lab.model import FakeModelAdapter
from lab.stages import Stage
from lab.util import sha256_file
from lab.workflow import create_request, record_delay


def test_logbook_narrates_story_creation_from_evidence(tmp_path: Path) -> None:
    initialize(tmp_path)
    story = create_story(tmp_path, "Make the Lab observable")

    page = render(tmp_path)

    assert "Catfish Lab / Logbook" in page
    assert "≋<°)))><" in page
    assert "Make the claim. Show the trace." in page
    assert "Evidence  VERIFIED" in page
    assert story.id in page
    assert "Registered" in page
    assert "Cited artifacts" in page


def test_logbook_reports_role_finding_with_citation_and_matching_seal(tmp_path: Path) -> None:
    initialize(tmp_path)
    story = create_story(tmp_path, "Inspect a design")
    artifact = tmp_path / ".lab" / "stories" / story.id / "redteam.md"
    artifact.write_text(
        "# Red Team Report\n\n## Confirmed defects\n\n"
        "- **Observation:** Repeated submission escapes the error boundary.\n"
    )
    append_record(
        tmp_path / ".lab/ledger.jsonl",
        {
            "story_id": story.id,
            "role": "redteam",
            "status": "success",
            "output_artifact": artifact.relative_to(tmp_path).as_posix(),
            "output_sha256": sha256_file(artifact),
        },
    )

    page = render(tmp_path, story.id)

    assert "RED TEAM  ·  REVIEW" in page
    assert "Repeated submission escapes the error boundary." in page
    assert f"SOURCE    {artifact.relative_to(tmp_path).as_posix()}" in page
    assert "MATCH · sha256:" in page


def test_logbook_cli_accepts_story_as_positional(tmp_path: Path, monkeypatch) -> None:
    initialize(tmp_path)
    story = create_story(tmp_path, "One chapter")
    monkeypatch.chdir(tmp_path)

    result = CliRunner().invoke(app, ["logbook", story.id, "--snapshot"])

    assert result.exit_code == 0
    assert "One chapter" in result.stdout


def test_story_view_lists_every_role_and_waiting_contract(tmp_path: Path) -> None:
    initialize(tmp_path)
    story = create_story(tmp_path, "See the whole team", lab_depth="full")

    page = render(tmp_path, story.id)
    for role in (
        "Product Steward",
        "Scientist",
        "Architect",
        "blind Heretic",
        "Builder",
        "Red Team",
        "Judge",
        "Archivist",
    ):
        assert role in page
    assert "Evidence     Waiting" in page
    role_contract = (tmp_path / ".lab/roles/scientist.md").read_text()
    assert "Turn uncertainty into a testable question" in role_contract


def test_status_cli_accepts_story_as_positional(tmp_path: Path, monkeypatch) -> None:
    initialize(tmp_path)
    story = create_story(tmp_path, "Status target")
    monkeypatch.chdir(tmp_path)

    result = CliRunner().invoke(app, ["status", story.id])

    assert result.exit_code == 0
    assert "stage: story" in result.stdout


def test_logbook_relays_delayed_work_and_marks_story(tmp_path: Path) -> None:
    initialize(tmp_path)
    story = create_story(tmp_path, "Local model may be offline")
    record_delay(tmp_path, story.id, "connection refused", harness="ollama")

    page = render(tmp_path, story.id)
    report = observation(tmp_path, read_records(tmp_path / ".lab/ledger.jsonl")[-1])

    assert "Delayed · Story" in page
    assert "is delayed on ollama: connection refused" in report[2]


def test_logbook_advance_runs_model_role_without_external_inbox_worker(
    tmp_path: Path, monkeypatch
) -> None:
    initialize(tmp_path)
    story = create_story(tmp_path, "Run from the TUI", lab_depth="full")
    state = _InteractiveState(story_id=story.id)
    monkeypatch.setattr(
        "lab.logbook.adapter_for_active",
        lambda root: FakeModelAdapter(
            [TEMPLATES["hypothesis"], TEMPLATES["proposal"], TEMPLATES["proposal"]]
        ),
    )

    _start_model_action(
        tmp_path,
        state,
        story.id,
        f"lab run scientist {story.id} --harness",
    )
    deadline = time.monotonic() + 1
    while state.busy and time.monotonic() < deadline:
        time.sleep(0.01)

    assert not state.busy
    assert (tmp_path / ".lab/stories" / story.id / "hypothesis.md").is_file()
    assert (tmp_path / ".lab/stories" / story.id / "candidates/A.md").is_file()
    assert (tmp_path / ".lab/stories" / story.id / "candidates/B.md").is_file()
    assert "HANDOFF" in state.message


def test_light_request_runs_product_then_stops_at_real_builder_handoff(
    tmp_path: Path, monkeypatch
) -> None:
    initialize(tmp_path)
    story_id = create_request(tmp_path, "Repair the setup", title=None, depth="light")
    state = _InteractiveState(story_id=story_id)
    monkeypatch.setattr(
        "lab.logbook.adapter_for_active",
        lambda root: FakeModelAdapter([TEMPLATES["story"]]),
    )

    _start_model_action(
        tmp_path,
        state,
        story_id,
        f"lab run product {story_id} --harness",
    )
    deadline = time.monotonic() + 1
    while state.busy and time.monotonic() < deadline:
        time.sleep(0.01)

    page = render(tmp_path, story_id)
    assert "HANDOFF" in state.message
    assert "1/5 required artifacts" in page
    assert not (tmp_path / ".lab/stories" / story_id / "implementation.md").exists()


def test_unexpected_provider_failure_becomes_persisted_delay(tmp_path: Path, monkeypatch) -> None:
    initialize(tmp_path)
    story = create_story(tmp_path, "Keep an exhausted provider visible")
    state = _InteractiveState(story_id=story.id)

    class ExhaustedAdapter:
        def complete(self, request):
            raise RuntimeError("token quota exhausted")

    monkeypatch.setattr("lab.logbook.adapter_for_active", lambda root: ExhaustedAdapter())
    _start_model_action(
        tmp_path,
        state,
        story.id,
        f"lab run product {story.id} --harness",
    )
    deadline = time.monotonic() + 1
    while state.busy and time.monotonic() < deadline:
        time.sleep(0.01)

    latest = read_records(tmp_path / ".lab/ledger.jsonl")[-1]
    assert state.message == "DELAYED · token quota exhausted"
    assert latest["event"] == "work_delayed"
    assert latest["reason"] == "token quota exhausted"


def test_logbook_hands_builder_to_tool_capable_harness(tmp_path: Path) -> None:
    initialize(tmp_path)
    story = create_story(tmp_path, "Do real work")
    state = _InteractiveState(story_id=story.id)

    _start_model_action(
        tmp_path,
        state,
        story.id,
        f"lab run builder {story.id} --harness",
    )

    assert not state.busy
    assert "HANDOFF" in state.message
    assert not (tmp_path / ".lab/stories" / story.id / "implementation.md").exists()


def test_automatic_review_stops_at_a_human_gate(tmp_path: Path, monkeypatch) -> None:
    initialize(tmp_path)
    story = create_story(tmp_path, "Review the actual result")
    save_story(
        tmp_path,
        story.model_copy(
            update={
                "stage": Stage.IMPLEMENTATION,
                "human": story.human.model_copy(update={"implementation_approved": True}),
                "artifacts": story.artifacts.model_copy(update={"implementation": True}),
            }
        ),
    )
    state = _InteractiveState(story_id=story.id)
    monkeypatch.setattr(
        "lab.logbook.adapter_for_active",
        lambda root: FakeModelAdapter([TEMPLATES["redteam"], TEMPLATES["trial"]]),
    )

    _start_model_action(
        tmp_path,
        state,
        story.id,
        f"lab run redteam {story.id} --harness",
    )
    deadline = time.monotonic() + 1
    while state.busy and time.monotonic() < deadline:
        time.sleep(0.01)

    assert state.message.startswith("HUMAN GATE")
    assert f"lab approve done {story.id}" in state.message
