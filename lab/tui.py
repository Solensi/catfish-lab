"""Responsive Textual frontend for the Catfish Logbook."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path

from rich.markdown import Markdown as RichMarkdown
from textual.app import App, ComposeResult
from textual.binding import Binding
from textual.containers import Horizontal, Vertical, VerticalScroll
from textual.css.query import NoMatches
from textual.screen import ModalScreen
from textual.widgets import (
    Button,
    Checkbox,
    Footer,
    Input,
    Label,
    ListItem,
    ListView,
    Static,
)

from .artifacts import load_story
from .casefiles import CaseFile, case_files, render_case_file
from .controller import reject_assessment
from .harnesses import active_profile, load_harnesses, profile_availability, select_harness
from .ledger import read_records, verify_ledger
from .logbook import (
    BRAND_MARK,
    ROLE_PIPELINE,
    ROLE_TITLES,
    _action_label,
    _evidence_bearing,
    _InteractiveState,
    _start_model_action,
    observation,
)
from .workflow import approve_story, create_request, next_actions, request_next_action


class StoryItem(ListItem):
    def __init__(self, story_id: str, label: str) -> None:
        super().__init__(Label(label))
        self.story_id = story_id


class StoryList(ListView):
    """The case index: arrow keys first, familiar j/k keys as a bonus."""

    BINDINGS = [
        Binding("j", "cursor_down", "Next story", show=False),
        Binding("k", "cursor_up", "Previous story", show=False),
        Binding("right", "read_case", "Read case", show=False),
    ]

    def action_read_case(self) -> None:
        self.app.query_one("#case-scroll", CaseScroll).focus()


class ReviewScroll(VerticalScroll):
    """A reading surface with both arrow and conventional TUI navigation."""

    can_focus = True
    BINDINGS = [
        Binding("j", "scroll_down", "Scroll down", show=False),
        Binding("k", "scroll_up", "Scroll up", show=False),
    ]


class CaseScroll(ReviewScroll):
    """The main reading pane; left returns to the story rail."""

    BINDINGS = [*ReviewScroll.BINDINGS, Binding("left", "stories", "Stories", show=False)]

    def action_stories(self) -> None:
        self.app.query_one("#story-list", StoryList).focus()


class RequestScreen(ModalScreen[tuple[str, str] | None]):
    """Small request form; advanced workflow controls remain out of the way."""

    BINDINGS = [Binding("escape", "cancel", "Cancel")]

    def compose(self) -> ComposeResult:
        with Vertical(classes="dialog"):
            yield Label("Open a new case", classes="dialog-title")
            yield Label("Describe the outcome in ordinary language.", classes="dialog-copy")
            yield Input(placeholder="What should change?", id="request-input")
            yield Checkbox("Use the full experimental route", id="full-depth")
            with Horizontal(classes="dialog-actions"):
                yield Button("Cancel", id="cancel")
                yield Button("Open case", id="submit", variant="primary")

    def on_mount(self) -> None:
        self.query_one("#request-input", Input).focus()

    def on_input_submitted(self, event: Input.Submitted) -> None:
        self._submit()

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "cancel":
            self.dismiss(None)
        else:
            self._submit()

    def _submit(self) -> None:
        prompt = self.query_one("#request-input", Input).value.strip()
        if not prompt:
            self.notify("Describe the outcome first.", severity="warning")
            return
        depth = "full" if self.query_one("#full-depth", Checkbox).value else "light"
        self.dismiss((prompt, depth))

    def action_cancel(self) -> None:
        self.dismiss(None)


class HarnessScreen(ModalScreen[str | None]):
    BINDINGS = [Binding("escape", "cancel", "Cancel")]

    def __init__(self, repo_root: Path) -> None:
        super().__init__()
        self.repo_root = repo_root
        self._profile_names: list[str] = []

    def compose(self) -> ComposeResult:
        active, profiles = load_harnesses(self.repo_root)
        with Vertical(classes="dialog"):
            yield Label("Choose a harness", classes="dialog-title")
            yield Label(
                "The voice may change. The evidence contract does not.",
                classes="dialog-copy",
            )
            self._profile_names = [profile.name for profile in profiles]
            for index, profile in enumerate(profiles):
                available, _ = profile_availability(profile)
                marker = "●" if profile.name == active else "○"
                health = "ready" if available else "unavailable"
                yield Button(
                    f"{marker}  {profile.label} · {health}",
                    id=f"harness-{index}",
                    classes="harness-choice",
                )
            yield Button("Cancel", id="cancel")

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "cancel":
            self.dismiss(None)
            return
        index = int(str(event.button.id).removeprefix("harness-"))
        self.dismiss(self._profile_names[index])

    def action_cancel(self) -> None:
        self.dismiss(None)


class ReadingScreen(ModalScreen[None]):
    BINDINGS = [Binding("escape", "dismiss", "Close"), Binding("q", "dismiss", "Close")]

    def __init__(self, title: str, content: str) -> None:
        super().__init__()
        self.reading_title = title
        self.content = content

    def compose(self) -> ComposeResult:
        with Vertical(classes="reading"):
            yield Label(self.reading_title, classes="dialog-title")
            with ReviewScroll(classes="reading-scroll"):
                yield Static(RichMarkdown(self.content), classes="reading-copy")
            yield Label("j/k or ↑/↓ scroll · Esc returns", classes="dialog-copy")

    def on_mount(self) -> None:
        self.query_one(ReviewScroll).focus()

    def action_dismiss(self) -> None:
        self.dismiss(None)


class CaseFileItem(ListItem):
    def __init__(self, story_id: str, case_file: CaseFile) -> None:
        marker = "✓ READY" if case_file.ready else "○ WAITING"
        super().__init__(
            Label(
                f"{marker}  {case_file.title} · {case_file.author}\n"
                f".lab/stories/{story_id}/{case_file.relative_path}"
            )
        )
        self.case_file = case_file


class CaseFileList(ListView):
    BINDINGS = [
        Binding("j", "cursor_down", "Next file", show=False),
        Binding("k", "cursor_up", "Previous file", show=False),
    ]


class CaseFilesScreen(ModalScreen[None]):
    """Keyboard-first index of every expected and recorded case document."""

    BINDINGS = [
        Binding("escape", "dismiss", "Close"),
        Binding("q", "dismiss", "Close"),
        Binding("e", "ignore", "Already here", show=False),
    ]

    def __init__(self, repo_root: Path, story_id: str) -> None:
        super().__init__()
        self.repo_root = repo_root
        self.story_id = story_id
        self.files = case_files(repo_root, story_id)

    def compose(self) -> ComposeResult:
        with Vertical(classes="reading case-files"):
            yield Label(f"{self.story_id} · Case files", classes="dialog-title")
            yield Label(
                "Every expected document is listed, including work that has not arrived yet.",
                classes="dialog-copy",
            )
            yield CaseFileList(
                *(CaseFileItem(self.story_id, case_file) for case_file in self.files),
                id="case-file-list",
            )
            yield Label("j/k or ↑/↓ moves · Enter opens · Esc returns", classes="dialog-copy")

    def on_mount(self) -> None:
        self.query_one(CaseFileList).focus()

    def on_list_view_selected(self, event: ListView.Selected) -> None:
        if not isinstance(event.item, CaseFileItem):
            return
        case_file = event.item.case_file
        if not case_file.ready:
            self.notify(
                f"{case_file.title} has not been written yet.",
                severity="warning",
            )
            return
        source = f".lab/stories/{self.story_id}/{case_file.relative_path}"
        self.app.push_screen(
            ReadingScreen(
                f"{case_file.title} · {case_file.author}",
                f"*Source: `{source}`*\n\n---\n\n{render_case_file(case_file)}",
            )
        )

    def action_dismiss(self) -> None:
        self.dismiss(None)

    def action_ignore(self) -> None:
        pass


def _approval_kind(action: str) -> str:
    parts = action.split()
    return parts[2] if parts[:2] == ["lab", "approve"] and len(parts) > 2 else "decision"


def _approval_evidence(repo_root: Path, story_id: str, action: str) -> str:
    """Assemble the evidence relevant to one human gate without hiding its sources."""

    gate = _approval_kind(action)
    sources = {
        "experiment": (
            ("Critique", "critique.md"),
            ("Experiment plan", "experiment.md"),
        ),
        "implementation": (
            ("Decision", "decision.md"),
            ("Experiment result", "evidence/results.json"),
        ),
        "done": (
            ("Completion Trial", "trial.md"),
            ("Red Team Report", "redteam.md"),
            ("Implementation", "implementation.md"),
        ),
    }.get(gate, (("Story", "story.md"),))
    directory = repo_root / ".lab/stories" / story_id
    lines = [f"# Evidence for the {gate} decision", ""]
    found = False
    for label, relative in sources:
        path = directory / relative
        lines.extend((f"## {label}", f"*Source: `.lab/stories/{story_id}/{relative}`*", ""))
        if path.is_file():
            found = True
            lines.extend(
                (path.read_text(encoding="utf-8", errors="replace").strip(), "", "---", "")
            )
        else:
            lines.extend(("**Missing. Do not accept this gate yet.**", "", "---", ""))
    if not found:
        lines.append("No gate evidence is available. Leave this decision unchanged.")
    return "\n".join(lines)


@dataclass(frozen=True)
class GateDecision:
    approved: bool = False
    rejection_reason: str | None = None


class FeedbackScreen(ModalScreen[str | None]):
    """Require useful human feedback before returning a completion claim."""

    BINDINGS = [Binding("escape", "cancel", "Back")]

    def compose(self) -> ComposeResult:
        with Vertical(classes="dialog feedback-dialog"):
            yield Label("Send the assessment back", classes="dialog-title")
            yield Label(
                "Tell the Builder what did not earn acceptance. This becomes durable evidence.",
                classes="dialog-copy",
            )
            yield Input(
                placeholder="What must change before you will accept this?",
                id="feedback-input",
            )
            with Horizontal(classes="dialog-actions"):
                yield Button("Back  [Esc]", id="cancel")
                yield Button("Record feedback", id="submit", variant="primary")

    def on_mount(self) -> None:
        self.query_one("#feedback-input", Input).focus()

    def on_input_submitted(self, event: Input.Submitted) -> None:
        self._submit()

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "cancel":
            self.dismiss(None)
        else:
            self._submit()

    def _submit(self) -> None:
        reason = self.query_one("#feedback-input", Input).value.strip()
        if not reason:
            self.notify("Explain what must change first.", severity="warning")
            return
        self.dismiss(reason)

    def action_cancel(self) -> None:
        self.dismiss(None)


class AdvanceScreen(ModalScreen[GateDecision | None]):
    """An evidence-first human gate with complete keyboard operation."""

    BINDINGS = [
        Binding("e", "review", "Review evidence", priority=True),
        Binding("v", "review", "Review evidence", show=False, priority=True),
        Binding("y", "accept", "Accept & advance", priority=True),
        Binding("r", "request_changes", "Request changes", priority=True),
        Binding("escape", "cancel", "Not yet", priority=True),
    ]

    def __init__(self, repo_root: Path, story_id: str, action: str) -> None:
        super().__init__()
        self.repo_root = repo_root
        self.story_id = story_id
        self.action = action
        self.gate = _approval_kind(action)
        self.evidence = _approval_evidence(repo_root, story_id, action)

    def compose(self) -> ComposeResult:
        prompts = {
            "experiment": "Authorize this experiment?",
            "implementation": "Authorize implementation of the selected direction?",
            "done": "Accept the completion claim?",
        }
        with Vertical(classes="dialog advance-dialog"):
            yield Label("Advance · human gate", classes="dialog-title")
            yield Label(prompts.get(self.gate, "Accept this decision?"), classes="gate-question")
            yield Label(
                "Nothing changes until you review the evidence and choose explicitly.",
                classes="dialog-copy",
            )
            with Horizontal(classes="dialog-actions advance-actions"):
                yield Button("Review evidence  [e]", id="review", variant="primary")
                yield Button("Not yet  [Esc]", id="cancel")
                if self.gate == "done":
                    yield Button("Send back  [r]", id="request-changes")
                yield Button("Accept  [y]", id="accept", variant="success")

    def on_mount(self) -> None:
        self.query_one("#review", Button).focus()

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "review":
            self.action_review()
        elif event.button.id == "request-changes":
            self.action_request_changes()
        elif event.button.id == "cancel":
            self.dismiss(None)
        else:
            self.dismiss(GateDecision(approved=True))

    def action_review(self) -> None:
        self.app.push_screen(
            ReadingScreen(f"{self.story_id} · {self.gate.title()} evidence", self.evidence)
        )

    def action_accept(self) -> None:
        self.dismiss(GateDecision(approved=True))

    def action_request_changes(self) -> None:
        if self.gate != "done":
            self.notify("Feedback is recorded when reviewing the final assessment.")
            return
        self.app.push_screen(FeedbackScreen(), self._feedback_result)

    def _feedback_result(self, reason: str | None) -> None:
        if reason:
            self.dismiss(GateDecision(rejection_reason=reason))

    def action_cancel(self) -> None:
        self.dismiss(None)


class TutorialIntroScreen(ModalScreen[bool]):
    """A calm orientation before the synthetic ledger begins moving."""

    BINDINGS = [
        Binding("b", "begin", "Begin", priority=True),
        Binding("escape", "leave", "Leave tutorial", priority=True),
        Binding("q", "leave", "Leave tutorial", show=False, priority=True),
    ]

    def compose(self) -> ComposeResult:
        with Vertical(classes="dialog tutorial-dialog"):
            yield Label("FIRST CAST · orientation", classes="dialog-title")
            yield Static(
                RichMarkdown(
                    "# One claim. Eight responsibilities.\n\n"
                    "You are about to watch a **synthetic** claim enter the real Lab workflow. "
                    "It does not touch your project.\n\n"
                    "The run unfolds slowly in **Live Analysis**. Each finding names its source. "
                    "Press **Space** to pause, **j/k** to read, **Esc** to inspect roles, "
                    "and **l** to return to the analysis.\n\n"
                    "Nothing begins until you choose **Begin**."
                ),
                classes="dialog-copy",
            )
            with Horizontal(classes="dialog-actions"):
                yield Button("Leave tutorial  [Esc]", id="cancel")
                yield Button("Begin the First Cast  [b]", id="begin", variant="primary")

    def on_mount(self) -> None:
        self.query_one("#begin", Button).focus()

    def on_button_pressed(self, event: Button.Pressed) -> None:
        self.dismiss(event.button.id == "begin")

    def action_begin(self) -> None:
        self.dismiss(True)

    def action_leave(self) -> None:
        self.dismiss(False)


class AnalysisScreen(ModalScreen[None]):
    """Source-linked analysis that follows the evidence ledger in realtime."""

    BINDINGS = [
        Binding("space", "toggle_tutorial", "Pause/resume", show=False, priority=True),
        Binding("escape", "dismiss", "Close"),
        Binding("q", "quit_tutorial", "Close"),
    ]

    def __init__(
        self,
        repo_root: Path,
        story_id: str | None = None,
        *,
        tutorial_pause: Callable[[], bool] | None = None,
    ) -> None:
        super().__init__()
        self.repo_root = repo_root
        self.story_id = story_id
        self.tutorial_pause = tutorial_pause
        self.tutorial_paused = False
        self._rendered = ""

    def compose(self) -> ComposeResult:
        with Vertical(classes="reading"):
            yield Label("Live analysis", classes="dialog-title")
            yield Label(
                "Following role findings, delays, and their source artifacts.",
                classes="dialog-copy",
            )
            with ReviewScroll(classes="reading-scroll"):
                yield Static("Waiting for evidence…", id="analysis-copy", classes="reading-copy")
            hint = (
                "Space pauses · j/k or ↑/↓ scroll · Esc explores roles"
                if self.tutorial_pause
                else "Updates every second · j/k or ↑/↓ scroll · Esc returns"
            )
            yield Label(hint, id="analysis-hint", classes="dialog-copy")

    def on_mount(self) -> None:
        self.refresh_analysis()
        self.set_interval(1.0, self.refresh_analysis)
        self.query_one(ReviewScroll).focus()

    def _content(self) -> str:
        try:
            records = read_records(self.repo_root / ".lab/ledger.jsonl")
        except (OSError, ValueError) as error:
            return f"# Evidence cannot be read\n\n{error}\n\nRun `lab doctor` before continuing."
        if self.story_id:
            records = [record for record in records if record.get("story_id") == self.story_id]
        records = _evidence_bearing(records)[-20:]
        if not records:
            return "# The Logbook is listening\n\nNo evidence-bearing analysis has arrived yet."
        lines: list[str] = []
        if (self.repo_root / ".lab/TUTORIAL").is_file():
            lessons = (
                (2, "1/5 · THE REQUEST", "A plain request becomes a durable case."),
                (5, "2/5 · THE CAST", "Each specialist speaks through a separate artifact."),
                (9, "3/5 · THE TEST", "Competing ideas meet an observable experiment."),
                (13, "4/5 · THE ATTACK", "The Builder cannot judge its own completion claim."),
                (
                    10_000,
                    "5/5 · THE RECEIPTS",
                    "Every finding below names its source. Press Esc to inspect the cast.",
                ),
            )
            label, guidance = next(
                (label, guidance) for ceiling, label, guidance in lessons if len(records) <= ceiling
            )
            lines.extend((f"# First Cast · {label}", guidance, "", "---", ""))
        else:
            lines.extend(("# Live analysis", ""))
        for record in reversed(records):
            role, kind, statement, source = observation(self.repo_root, record)
            story = str(record.get("story_id", "Lab"))
            lines.extend(
                (
                    f"## {role.title()} · {kind.title()} · {story}",
                    statement,
                    "",
                    f"*Source: {source}*",
                    "",
                )
            )
        return "\n".join(lines)

    def refresh_analysis(self) -> None:
        content = self._content()
        if content != self._rendered:
            self.query_one("#analysis-copy", Static).update(RichMarkdown(content))
            self._rendered = content

    def action_dismiss(self) -> None:
        self.dismiss(None)

    def action_quit_tutorial(self) -> None:
        if (self.repo_root / ".lab/TUTORIAL").is_file():
            self.app.exit()
        else:
            self.dismiss(None)

    def action_toggle_tutorial(self) -> None:
        if self.tutorial_pause is None:
            return
        self.tutorial_paused = self.tutorial_pause()
        state = "PAUSED · Space resumes" if self.tutorial_paused else "RUNNING · Space pauses"
        self.query_one("#analysis-hint", Label).update(
            f"{state} · j/k or ↑/↓ scroll · Esc explores roles"
        )


def _story_label(repo_root: Path, story_id: str) -> str:
    story = load_story(repo_root, story_id)
    records = [
        record
        for record in read_records(repo_root / ".lab/ledger.jsonl")
        if record.get("story_id") == story_id
    ]
    delayed = bool(records and records[-1].get("event") == "work_delayed")
    state = "delayed" if delayed else story.stage.value.replace("_", " ")
    return f"{story_id}  {state.title()}\n{story.title}"


def _story_markdown(repo_root: Path, story_id: str) -> str:
    story = load_story(repo_root, story_id)
    artifact_state = story.artifacts.model_dump()
    required = (
        ("story", "implementation", "redteam", "trial", "archive")
        if story.lab_depth == "light"
        else tuple(artifact_state)
    )
    complete = sum(artifact_state[name] for name in required)
    progress = "●" * complete + "○" * (len(required) - complete)
    actions = next_actions(repo_root, story_id)
    next_step = _action_label(actions[0]) if actions else "This case is at rest."
    lines = [
        f"# {story.title}",
        f"`{story.id}`  **{story.stage.value.replace('_', ' ').title()}**  "
        f"· {story.lab_depth.title()} route",
        "",
        f"**Progress**  {progress}  {complete}/{len(required)}",
        "",
        "## Next",
        next_step,
        "",
        "## Case files",
        "Press **e** to browse every document and its exact repository path.",
        "",
        "## Roles",
    ]
    for number, (role, artifact, purpose) in enumerate(ROLE_PIPELINE, 1):
        skipped = story.lab_depth == "light" and role in {"scientist", "architect", "heretic"}
        path = repo_root / ".lab" / "stories" / story_id / artifact
        ready = path.is_file() and (role != "product" or story.artifacts.story)
        symbol = "✓" if ready else ("–" if skipped else "○")
        status = "complete" if ready else ("full route" if skipped else "waiting")
        lines.append(f"- **{number}. {ROLE_TITLES[role]}**  `{symbol} {status}`  — {purpose}")
    records = _evidence_bearing(
        [
            record
            for record in read_records(repo_root / ".lab/ledger.jsonl")
            if record.get("story_id") == story_id
        ]
    )
    if records:
        role, kind, statement, source = observation(repo_root, records[-1])
        lines.extend(
            (
                "",
                "## Latest finding",
                f"**{role.title()} · {kind.title()}**",
                "",
                statement,
                "",
                f"*Source: {source}*",
            )
        )
    return "\n".join(lines)


class CatfishLogbook(App[str | None]):
    CSS_PATH = "logbook.tcss"
    TITLE = "Catfish Lab"
    SUB_TITLE = "Logbook"
    BINDINGS = [
        Binding("1", "role(0)", "Role 1", show=False),
        Binding("2", "role(1)", "Role 2", show=False),
        Binding("3", "role(2)", "Role 3", show=False),
        Binding("4", "role(3)", "Role 4", show=False),
        Binding("5", "role(4)", "Role 5", show=False),
        Binding("6", "role(5)", "Role 6", show=False),
        Binding("7", "role(6)", "Role 7", show=False),
        Binding("8", "role(7)", "Role 8", show=False),
        Binding("n", "new_request", "New case"),
        Binding("a", "advance", "Advance"),
        Binding("e", "case_files", "Case files"),
        Binding("h", "harness", "Harness"),
        Binding("l", "analysis", "Analysis"),
        Binding("question_mark", "help", "Help"),
        Binding("r", "refresh_lab", "Refresh", show=False),
        Binding("q", "quit", "Quit"),
    ]

    def __init__(
        self,
        repo_root: Path,
        story_id: str | None = None,
        *,
        initial_view: str | None = None,
        tutorial_start: Callable[[], None] | None = None,
        tutorial_pause: Callable[[], bool] | None = None,
    ) -> None:
        super().__init__()
        self.repo_root = repo_root
        self.active_story_id = story_id
        self.initial_view = initial_view
        self.tutorial_start = tutorial_start
        self.tutorial_pause = tutorial_pause
        self.role_state = _InteractiveState(story_id=story_id)
        self._known_story_ids: list[str] = []
        self._selection_initialized = False
        self._syncing_story_list = False
        self._brand_content = ""
        self._case_content = ""
        self._situation_content = ""

    def _brand_markup(self) -> str:
        profile = active_profile(self.repo_root)
        available, _ = profile_availability(profile)
        health = "ready" if available else "delayed"
        return (
            f"[bold]{BRAND_MARK}  CATFISH LAB[/bold]\n"
            f"[dim]Logbook · Make the claim. Show the trace. · {profile.label} {health}[/dim]"
        )

    def compose(self) -> ComposeResult:
        story_ids = self._story_ids()
        self._known_story_ids = story_ids
        self._brand_content = self._brand_markup()
        yield Static(self._brand_content, id="brand")
        with Horizontal(id="workspace"):
            with Vertical(id="story-pane"):
                yield Label("Stories", classes="pane-title")
                yield StoryList(
                    *(
                        StoryItem(story_id, _story_label(self.repo_root, story_id))
                        for story_id in story_ids
                    ),
                    id="story-list",
                )
            with Vertical(id="case-pane"):
                yield Label(
                    "Case · Tab / → reads · j/k scrolls · ← returns",
                    classes="pane-title case-pane-title",
                )
                with CaseScroll(id="case-scroll"):
                    yield Static(RichMarkdown("# Open a case"), id="case")
        yield Static("Ready.", id="situation")
        yield Footer()

    async def on_mount(self) -> None:
        await self._sync_story_list()
        # Role work happens in a background thread. Poll the filesystem, but only
        # repaint widgets when their content actually changes (see _refresh_case).
        self.set_interval(1.0, self.refresh_lab)
        if self.initial_view == "tutorial":
            self.push_screen(TutorialIntroScreen(), self._tutorial_intro_result)
        elif self.initial_view in {"analysis", "feed"}:
            self.push_screen(
                AnalysisScreen(
                    self.repo_root,
                    self.active_story_id,
                    tutorial_pause=self.tutorial_pause,
                )
            )
        else:
            self.query_one("#story-list", StoryList).focus()

    def _tutorial_intro_result(self, begin: bool) -> None:
        if not begin:
            self.exit()
            return
        if self.tutorial_start:
            self.tutorial_start()
        self.push_screen(
            AnalysisScreen(
                self.repo_root,
                self.active_story_id,
                tutorial_pause=self.tutorial_pause,
            )
        )

    def _story_ids(self) -> list[str]:
        return [path.name for path in sorted((self.repo_root / ".lab/stories").glob("US-*"))]

    async def _sync_story_list(self) -> None:
        story_ids = self._story_ids()
        story_list = self.query_one("#story-list", ListView)
        rebuilt = story_ids != self._known_story_ids
        if rebuilt:
            self._syncing_story_list = True
            await story_list.clear()
            for story_id in story_ids:
                await story_list.append(StoryItem(story_id, _story_label(self.repo_root, story_id)))
            self._known_story_ids = story_ids
            self._syncing_story_list = False
        else:
            for item in story_list.query(StoryItem):
                item.query_one(Label).update(_story_label(self.repo_root, item.story_id))
        if story_ids and self.active_story_id not in story_ids:
            self.active_story_id = story_ids[-1]
        if self.active_story_id in story_ids and (
            rebuilt or not self._selection_initialized or story_list.index is None
        ):
            story_list.index = story_ids.index(self.active_story_id)
        self._selection_initialized = True
        self._refresh_case()

    def _refresh_case(self) -> None:
        brand = self._brand_markup()
        if brand != self._brand_content:
            self.query_one("#brand", Static).update(brand)
            self._brand_content = brand
        case = self.query_one("#case", Static)
        if self.active_story_id:
            content = _story_markdown(self.repo_root, self.active_story_id)
            self.role_state.story_id = self.active_story_id
        else:
            content = (
                "# The board is clear\n\nPress **n** to describe something worth building, "
                "repairing, investigating, or maintaining."
            )
        if content != self._case_content:
            # Textual's Markdown widget parses through asyncio's default thread
            # pool. A Rich renderable is just as legible here and exits cleanly
            # on runtimes where that executor is unavailable.
            case.update(RichMarkdown(content))
            self._case_content = content
        situation = self.role_state.message or "Ready. Press n for a new case."
        if self.active_story_id and not self.role_state.busy:
            story_records = [
                record
                for record in read_records(self.repo_root / ".lab/ledger.jsonl")
                if record.get("story_id") == self.active_story_id
            ]
            latest = story_records[-1] if story_records else None
            if latest and latest.get("event") == "work_delayed":
                harness = latest.get("harness") or "selected harness"
                reason = latest.get("reason") or "No diagnostic was recorded."
                situation = f"DELAYED · {harness}: {reason} · l opens the evidence"
        if verify_ledger(self.repo_root / ".lab/ledger.jsonl"):
            situation = "Evidence integrity warning · run lab doctor"
        if situation != self._situation_content:
            situation_widget = self.query_one("#situation", Static)
            situation_widget.update(situation)
            situation_widget.set_class(
                "DELAYED" in situation.upper() or "WARNING" in situation.upper(),
                "delayed",
            )
            self._situation_content = situation

    async def refresh_lab(self) -> None:
        try:
            await self._sync_story_list()
        except NoMatches:
            # A timer tick may overlap a modal transition or application teardown.
            # The next tick will repaint; there is no useful state to mutate here.
            return

    def _select_story(self, item: ListItem | None) -> None:
        """Make cursor movement authoritative so polling cannot fight the user."""

        if (
            self._selection_initialized
            and not self._syncing_story_list
            and isinstance(item, StoryItem)
            and item.story_id != self.active_story_id
        ):
            self.active_story_id = item.story_id
            self.role_state.story_id = self.active_story_id
            self.role_state.message = ""
            self._refresh_case()

    def on_list_view_highlighted(self, event: ListView.Highlighted) -> None:
        self._select_story(event.item)

    def on_list_view_selected(self, event: ListView.Selected) -> None:
        self._select_story(event.item)

    def action_new_request(self) -> None:
        self.push_screen(RequestScreen(), self._new_request_result)

    async def _new_request_result(self, result: tuple[str, str] | None) -> None:
        if result is None:
            return
        prompt, depth = result
        try:
            self.active_story_id = create_request(self.repo_root, prompt, title=None, depth=depth)
        except ValueError as error:
            self.notify(str(error), severity="error")
            return
        self.role_state.story_id = self.active_story_id
        self.role_state.message = f"{self.active_story_id} opened. Press a to advance."
        await self._sync_story_list()

    def action_advance(self) -> None:
        if not self.active_story_id:
            self.notify("Open or create a case first.", severity="warning")
            return
        if self.role_state.busy:
            self.notify("A role is already working.")
            return
        actions = next_actions(self.repo_root, self.active_story_id)
        if not actions:
            self.notify("This case is at rest.")
            return
        action = actions[0]
        if action.startswith("lab approve "):
            self.push_screen(
                AdvanceScreen(self.repo_root, self.active_story_id, action),
                self._approval_result,
            )
            return
        requested = request_next_action(self.repo_root, self.active_story_id)
        _start_model_action(self.repo_root, self.role_state, self.active_story_id, requested)
        self._refresh_case()

    async def _approval_result(self, decision: GateDecision | None) -> None:
        if decision is None or not self.active_story_id:
            self.role_state.message = "No state changed."
            self._refresh_case()
            return
        actions = next_actions(self.repo_root, self.active_story_id)
        if not actions or not actions[0].startswith("lab approve "):
            self.role_state.message = (
                "The case changed while the decision was open. Review it again."
            )
            await self._sync_story_list()
            return
        action = actions[0]
        if decision.rejection_reason:
            try:
                rejection = reject_assessment(
                    self.repo_root,
                    story_id=self.active_story_id,
                    reason=decision.rejection_reason,
                )
                requested = request_next_action(self.repo_root, self.active_story_id)
            except ValueError as error:
                self.notify(str(error), severity="error")
                return
            _start_model_action(
                self.repo_root,
                self.role_state,
                self.active_story_id,
                requested,
            )
            relative = rejection.feedback.relative_to(self.repo_root)
            self.role_state.message = (
                f"FEEDBACK RECORDED · {relative} · HANDOFF to the coding harness"
            )
            await self._sync_story_list()
            return
        if not decision.approved:
            self.role_state.message = "No state changed."
            self._refresh_case()
            return
        try:
            approve_story(self.repo_root, self.active_story_id, action.split()[2])
        except (ValueError, IndexError) as error:
            self.notify(str(error), severity="error")
            return
        self.role_state.message = "Human approval recorded."
        following = next_actions(self.repo_root, self.active_story_id)
        if following:
            requested = request_next_action(self.repo_root, self.active_story_id)
            _start_model_action(self.repo_root, self.role_state, self.active_story_id, requested)
        await self._sync_story_list()

    def action_harness(self) -> None:
        self.push_screen(HarnessScreen(self.repo_root), self._harness_result)

    def _harness_result(self, name: str | None) -> None:
        if name is None:
            return
        profile = select_harness(self.repo_root, name)
        available, detail = profile_availability(profile)
        state = "ready" if available else "delayed"
        self.role_state.message = f"Harness changed to {profile.label} · {state} · {detail}"
        self._refresh_case()

    def action_analysis(self) -> None:
        self.push_screen(
            AnalysisScreen(
                self.repo_root,
                self.active_story_id,
                tutorial_pause=self.tutorial_pause,
            )
        )

    def action_case_files(self) -> None:
        if not self.active_story_id:
            self.notify("Open or create a case first.", severity="warning")
            return
        self.push_screen(CaseFilesScreen(self.repo_root, self.active_story_id))

    def action_role(self, index: int) -> None:
        if not self.active_story_id or not 0 <= index < len(ROLE_PIPELINE):
            return
        role, artifact, purpose = ROLE_PIPELINE[index]
        directory = self.repo_root / ".lab/stories" / self.active_story_id
        path = directory / artifact
        if not path.is_file():
            path = self.repo_root / ".lab/roles" / f"{role}.md"
        content = path.read_text(encoding="utf-8") if path.is_file() else "No artifact yet."
        self.push_screen(ReadingScreen(f"{ROLE_TITLES[role]} · {purpose}", content))

    def action_help(self) -> None:
        self.push_screen(
            ReadingScreen(
                "How to use the Logbook",
                "# Keyboard first\n\n"
                "Use **↑/↓** or **j/k** to move through stories. The case view follows "
                "your cursor and stays there.\n\n"
                "# Four useful actions\n\n"
                "- **n** opens a case in ordinary language.\n"
                "- **a** advances work or opens an evidence-first human gate.\n"
                "- **e** browses every case file and its exact path.\n"
                "- **h** changes the model harness.\n"
                "- **l** opens live analysis with its sources.\n\n"
                "At a gate, press **e** to review evidence, **j/k** to scroll, **y** to accept, "
                "**r** to send a final assessment back with a reason, or **Esc** to leave it "
                "unchanged. In the main view, press **Tab** or **→** to enter the case text, "
                "scroll it with **j/k**, and press **←** to return to stories. Use **1–8** to "
                "inspect the named roles. "
                "Mouse controls remain available; press **q** to leave.",
            )
        )


def run_logbook(
    repo_root: Path,
    story_id: str | None = None,
    *,
    initial_view: str | None = None,
    tutorial_start: Callable[[], None] | None = None,
    tutorial_pause: Callable[[], bool] | None = None,
) -> None:
    CatfishLogbook(
        repo_root,
        story_id,
        initial_view=initial_view,
        tutorial_start=tutorial_start,
        tutorial_pause=tutorial_pause,
    ).run()
