from pathlib import Path

import pytest
from textual.widgets import Input, Label
from typer.testing import CliRunner

from lab.artifacts import create_story, load_story, save_story
from lab.cli import app, repo_root
from lab.config import initialize
from lab.stages import Stage
from lab.tui import (
    AdvanceScreen,
    AnalysisScreen,
    CaseFileItem,
    CaseFilesScreen,
    CaseScroll,
    CatfishLogbook,
    FeedbackScreen,
    ReadingScreen,
    RequestScreen,
    ReviewScroll,
    TutorialIntroScreen,
)
from lab.workflow import inbox_payload, record_delay


def test_init_attaches_lab_to_an_arbitrary_repository(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.chdir(tmp_path)

    result = CliRunner().invoke(app, ["init"])

    assert result.exit_code == 0
    assert (tmp_path / ".lab/config.yaml").is_file()
    assert (tmp_path / ".lab/HARNESS.md").is_file()
    assert "Harness handoff: .lab/HARNESS.md" in result.stdout
    nested = tmp_path / "frontend" / "src"
    nested.mkdir(parents=True)
    monkeypatch.chdir(nested)
    assert repo_root() == tmp_path


@pytest.mark.asyncio
async def test_logbook_opens_core_views_and_exits_cleanly(tmp_path: Path) -> None:
    initialize(tmp_path)
    story = create_story(tmp_path, "Make the setup legible")
    application = CatfishLogbook(tmp_path, story.id)

    async with application.run_test(size=(100, 32)) as pilot:
        assert application.active_story_id == story.id

        await pilot.press("n")
        assert isinstance(application.screen, RequestScreen)
        await pilot.press("escape")
        assert not isinstance(application.screen, RequestScreen)

        await pilot.press("l")
        assert isinstance(application.screen, AnalysisScreen)
        record_delay(tmp_path, story.id, "local provider did not answer", harness="ollama")
        application.screen.refresh_analysis()
        assert "local provider did not answer" in application.screen._rendered
        await pilot.press("escape")

        role_titles = (
            "Product Steward",
            "Scientist",
            "Architect",
            "blind Heretic",
            "Builder",
            "Red Team",
            "Judge",
            "Archivist",
        )
        for number, title in enumerate(role_titles, 1):
            await pilot.press(str(number))
            assert isinstance(application.screen, ReadingScreen)
            assert title in application.screen.reading_title
            await pilot.press("escape")

        await pilot.press("q")


@pytest.mark.asyncio
async def test_story_keyboard_navigation_survives_live_refresh(tmp_path: Path) -> None:
    initialize(tmp_path)
    first = create_story(tmp_path, "Make navigation stable")
    second = create_story(tmp_path, "Keep the newest case available")
    application = CatfishLogbook(tmp_path, second.id)

    async with application.run_test(size=(100, 32)) as pilot:
        assert application.active_story_id == second.id

        await pilot.press("up")
        assert application.active_story_id == first.id
        await application.refresh_lab()
        assert application.active_story_id == first.id

        create_story(tmp_path, "Arrive while another story is selected")
        await application.refresh_lab()
        assert application.active_story_id == first.id

        await pilot.press("j")
        assert application.active_story_id == second.id


@pytest.mark.asyncio
async def test_main_case_text_is_keyboard_scrollable_without_changing_story(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    initialize(tmp_path)
    story = create_story(tmp_path, "Read the case without reaching for a mouse")
    long_case = "# Case\n\n" + "\n\n".join(
        f"## Finding {number}\n\nA source-linked finding to read." for number in range(1, 50)
    )
    monkeypatch.setattr("lab.tui._story_markdown", lambda root, story_id: long_case)
    application = CatfishLogbook(tmp_path, story.id)

    async with application.run_test(size=(90, 24)) as pilot:
        await pilot.press("right")
        case = application.query_one(CaseScroll)
        assert case.has_focus

        await pilot.press("j", "j", "j")
        await pilot.pause()
        assert case.scroll_y > 0
        assert application.active_story_id == story.id

        await pilot.press("left")
        assert application.query_one("#story-list").has_focus

        await pilot.press("tab")
        assert case.has_focus


@pytest.mark.asyncio
async def test_role_numbers_remain_typeable_in_request_form(tmp_path: Path) -> None:
    initialize(tmp_path)
    application = CatfishLogbook(tmp_path)

    async with application.run_test(size=(100, 32)) as pilot:
        await pilot.press("n")
        assert isinstance(application.screen, RequestScreen)
        await pilot.press("1", "2", "3", "4", "5", "6", "7", "8")
        await pilot.press("e")
        prompt = application.screen.query_one("#request-input", Input)
        assert prompt.value == "12345678e"


@pytest.mark.asyncio
async def test_case_files_are_visible_and_openable_from_the_logbook(tmp_path: Path) -> None:
    initialize(tmp_path)
    story = create_story(
        tmp_path,
        "Make role documents discoverable",
        request="Show me where the Lab saved its work.",
    )
    application = CatfishLogbook(tmp_path, story.id)

    async with application.run_test(size=(110, 34)) as pilot:
        await pilot.press("e")
        assert isinstance(application.screen, CaseFilesScreen)
        first = application.screen.query(CaseFileItem).first()
        label = str(first.query_one(Label).content)
        assert "Original request" in label
        assert f".lab/stories/{story.id}/request.md" in label

        await pilot.press("enter")
        assert isinstance(application.screen, ReadingScreen)
        assert "Show me where the Lab saved its work." in application.screen.content
        await pilot.press("escape")
        assert isinstance(application.screen, CaseFilesScreen)


def test_files_command_lists_ready_and_waiting_case_documents(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    initialize(tmp_path)
    story = create_story(tmp_path, "List every role document", request="Find the files.")
    monkeypatch.chdir(tmp_path)

    result = CliRunner().invoke(app, ["files", story.id])

    assert result.exit_code == 0
    assert f".lab/stories/{story.id}/request.md" in result.stdout
    assert f".lab/stories/{story.id}/redteam.md" in result.stdout
    assert "READY" in result.stdout
    assert "WAITING" in result.stdout


@pytest.mark.asyncio
async def test_advance_reviews_scrolls_and_accepts_entirely_by_keyboard(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    initialize(tmp_path)
    story = create_story(tmp_path, "Accept only after reading the evidence")
    directory = tmp_path / ".lab/stories" / story.id
    (directory / "implementation.md").write_text("# Implementation\n\nImplemented.\n")
    (directory / "redteam.md").write_text("# Red Team Report\n\nChallenged.\n")
    trial = (
        "# Completion Trial\n\n"
        + "\n\n".join(f"## Finding {number}\n\nEvidence line {number}." for number in range(1, 60))
        + "\n\n## Overall Verdict\n\nREADY\n"
    )
    (directory / "trial.md").write_text(trial)
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
    monkeypatch.setattr("lab.tui._start_model_action", lambda *args, **kwargs: None)
    application = CatfishLogbook(tmp_path, story.id)

    async with application.run_test(size=(100, 32)) as pilot:
        await pilot.press("a")
        assert isinstance(application.screen, AdvanceScreen)

        await pilot.press("e")
        assert isinstance(application.screen, ReadingScreen)
        assert "Completion Trial" in application.screen.content
        review = application.screen.query_one(ReviewScroll)
        await pilot.press("j")
        await pilot.pause()
        assert review.scroll_y > 0

        await pilot.press("escape")
        assert isinstance(application.screen, AdvanceScreen)
        await pilot.press("y")
        await pilot.pause()
        assert load_story(tmp_path, story.id).human.done_approved


@pytest.mark.asyncio
async def test_final_assessment_can_be_sent_back_with_keyboard_feedback(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    initialize(tmp_path)
    story = create_story(tmp_path, "Let the human explain a rejection")
    directory = tmp_path / ".lab/stories" / story.id
    for name, text in (
        ("implementation.md", "# Implementation\n\nOld implementation.\n"),
        ("redteam.md", "# Red Team Report\n\nOld review.\n"),
        ("trial.md", "# Completion Trial\n\n## Overall Verdict\n\nREADY\n"),
    ):
        (directory / name).write_text(text)
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
    monkeypatch.setattr("lab.tui._start_model_action", lambda *args, **kwargs: None)
    application = CatfishLogbook(tmp_path, story.id)

    async with application.run_test(size=(100, 32)) as pilot:
        await pilot.press("a", "r")
        assert isinstance(application.screen, FeedbackScreen)
        application.screen.query_one(
            "#feedback-input", Input
        ).value = "The side pane still cannot be read"
        await pilot.press("enter")
        await pilot.pause()

        updated = load_story(tmp_path, story.id)
        assert updated.stage is Stage.IMPLEMENTATION
        assert not updated.artifacts.implementation
        feedback = next((directory / "evidence").glob("human-feedback-*.md"))
        assert "side pane still cannot be read" in feedback.read_text()
        item = inbox_payload(tmp_path)["stories"][0]
        assert item["requested_action"] == f"lab run builder {story.id} --harness"
        assert item["feedback"]["reason"] == "The side pane still cannot be read"
        assert "FEEDBACK RECORDED" in application._situation_content


@pytest.mark.asyncio
async def test_tutorial_waits_for_orientation_and_can_pause(tmp_path: Path) -> None:
    initialize(tmp_path)
    story = create_story(tmp_path, "A deliberately paced tutorial")
    started: list[bool] = []
    paused: list[bool] = []

    def toggle_pause() -> bool:
        paused.append(True)
        return True

    application = CatfishLogbook(
        tmp_path,
        story.id,
        initial_view="tutorial",
        tutorial_start=lambda: started.append(True),
        tutorial_pause=toggle_pause,
    )

    async with application.run_test(size=(100, 32)) as pilot:
        assert isinstance(application.screen, TutorialIntroScreen)
        assert started == []

        await pilot.press("b")
        assert started == [True]
        assert isinstance(application.screen, AnalysisScreen)

        await pilot.press("space")
        assert paused == [True]
        assert "PAUSED" in str(application.screen.query_one("#analysis-hint", Label).content)


@pytest.mark.asyncio
async def test_persisted_delay_returns_to_status_line_after_restart(tmp_path: Path) -> None:
    initialize(tmp_path)
    story = create_story(tmp_path, "Explain token exhaustion")
    record_delay(tmp_path, story.id, "monthly token budget exhausted", harness="codex")
    application = CatfishLogbook(tmp_path, story.id)

    async with application.run_test(size=(100, 32)):
        assert application._situation_content.startswith("DELAYED · codex")
        assert "monthly token budget exhausted" in application._situation_content
