import threading
import time
from pathlib import Path

from typer.testing import CliRunner

from lab import cli
from lab.artifacts import load_story
from lab.config import initialize
from lab.ledger import verify_ledger
from lab.stages import Stage
from lab.tui import AnalysisScreen
from lab.tutorial import (
    dismiss_tutorial_prompt,
    offer_tutorial,
    populate_tutorial,
    prepare_tutorial,
    render_tutorial_invitation,
    run_tutorial,
    tutorial_prompt_dismissed,
)


def test_tutorial_completes_every_role_and_artifact_in_disposable_repo(tmp_path: Path) -> None:
    story_id = prepare_tutorial(tmp_path)

    populate_tutorial(tmp_path, story_id)

    story = load_story(tmp_path, story_id)
    assert story.stage is Stage.DONE
    assert all(story.artifacts.model_dump().values())
    assert all(story.human.model_dump().values())
    assert verify_ledger(tmp_path / ".lab/ledger.jsonl") == []
    assert "First Cast · 5/5 · THE RECEIPTS" in AnalysisScreen(tmp_path, story_id)._content()


def test_tutorial_snapshot_is_guided_synthetic_and_shows_the_cast() -> None:
    page = run_tutorial(snapshot=True, speed=0)

    assert page is not None
    assert "FIRST CAST" in page
    assert "TOO-CONFIDENT MACHINE" in page
    assert "blind Heretic" in page
    assert "Judge" in page
    assert "Archivist" in page
    assert "Done" in page


def test_tutorial_prompt_preference_is_local_and_rerunnable(tmp_path: Path) -> None:
    assert not tutorial_prompt_dismissed(tmp_path)

    dismiss_tutorial_prompt(tmp_path)

    assert tutorial_prompt_dismissed(tmp_path)
    marker = tmp_path / ".lab/tutorial-prompt-dismissed"
    assert "lab tutorial" in marker.read_text()


def test_tutorial_pause_stops_the_next_evidence_event(tmp_path: Path) -> None:
    story_id = prepare_tutorial(tmp_path)
    stop = threading.Event()
    running = threading.Event()
    running.set()
    producer = threading.Thread(
        target=populate_tutorial,
        args=(tmp_path, story_id),
        kwargs={"delay": 0.2, "stop": stop, "running": running},
    )
    producer.start()
    time.sleep(0.05)
    running.clear()

    time.sleep(0.25)
    assert not (tmp_path / ".lab/stories" / story_id / "story.md").exists()

    stop.set()
    running.set()
    producer.join(timeout=1)
    assert not producer.is_alive()


def test_tutorial_invitation_has_toggleable_dont_show_again_checkbox(capsys) -> None:
    keys = iter([" ", "\n"])

    begin, dismiss = offer_tutorial(read_key=lambda timeout: next(keys))

    assert begin
    assert dismiss
    assert "DON'T SHOW AGAIN  ON  ✓" in capsys.readouterr().out
    assert "DON'T SHOW AGAIN  OFF" in render_tutorial_invitation(80, dont_show_again=False)
    styled = render_tutorial_invitation(80, dont_show_again=False, styled=True)
    assert "\x1b[" in styled
    assert "CATFISH LAB" in styled
    assert "┏" in styled and "┛" in styled


def test_first_interactive_logbook_boot_offers_tutorial_then_enters_logbook(
    tmp_path: Path, monkeypatch
) -> None:
    initialize(tmp_path)
    calls: list[str] = []
    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr("sys.stdout.isatty", lambda: True)
    monkeypatch.setattr(cli, "tutorial_prompt_dismissed", lambda root: False)
    monkeypatch.setattr(cli, "offer_tutorial", lambda: (True, True))
    monkeypatch.setattr(cli, "dismiss_tutorial_prompt", lambda root: calls.append("dismissed"))
    monkeypatch.setattr(
        cli,
        "run_tutorial",
        lambda *, snapshot, speed: calls.append(f"tutorial:{snapshot}:{speed}"),
    )
    monkeypatch.setattr(cli, "watch", lambda *args, **kwargs: calls.append("logbook"))

    cli.logbook(None, True)

    assert calls == ["dismissed", "tutorial:False:1.5", "logbook"]


def test_tutorial_command_replaces_demo_command(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.chdir(tmp_path)

    tutorial = CliRunner().invoke(cli.app, ["tutorial", "--snapshot"])
    retired_demo = CliRunner().invoke(cli.app, ["demo"])

    assert tutorial.exit_code == 0
    assert "FIRST CAST" in tutorial.stdout
    assert not (tmp_path / ".lab/tutorial-prompt-dismissed").exists()
    assert retired_demo.exit_code != 0
