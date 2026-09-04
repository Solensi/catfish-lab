"""Disposable, guided introduction to a complete Catfish Lab story."""

import shutil
import sys
import tempfile
import textwrap
import threading
from collections.abc import Callable
from contextlib import nullcontext
from pathlib import Path

from .artifacts import create_story
from .config import initialize
from .controller import run_role
from .logbook import _key_input, _read_key, render, watch
from .model import FakeModelAdapter
from .workflow import approve_story, record_artifact

PRODUCT = """# User Story

## Statement

As a curious team, we want to test whether one model can sustain meaningfully different roles,
so that disagreement becomes evidence instead of theatre.

## User value

A visitor can watch the Lab think in public without mistaking narration for proof.

## Acceptance criteria

- [ ] Two blind proposals disagree in a measurable way.
- [ ] The completion claim survives the Red Team and the Judge.

## Out of scope

Real production changes. This is a synthetic tutorial.
"""

SCIENTIST = """# Hypothesis

## Observation

One model is playing every role, so different names alone prove nothing.

## Question

Can isolated context and opposing incentives produce useful disagreement?

## Hypothesis

The Architect and the blind Heretic will propose observably different paths when neither sees the
other's work, and a later trial will preserve that disagreement as inspectable evidence.

## Evidence that would change our mind

Near-identical proposals, missing provenance, or a completion claim without a separate review.
"""

ARCHITECT = """# Candidate Proposal

## Summary

Build a small, conventional pipeline: explicit stages, typed state, deterministic tests, and one
readable projection over the evidence ledger.

## Core idea

Reliability comes from simple boundaries that a future maintainer can explain and reproduce.

## Failure modes

The safe design may become procedural and fail to provoke meaningful alternatives.
"""

HERETIC = """# Candidate Proposal

## Summary

The blind Heretic rejects the comforting assumption that a tidy pipeline is enough. Preserve every
role output as an immutable object, then let the Logbook reveal disagreement, revision, and doubt.

## Core idea

Make intellectual change visible. A corrected belief is more interesting than a polished final file.

## Failure modes

Perfect provenance can become a museum nobody enjoys visiting.
"""

CRITIQUE = """# Critique

## Claim under challenge

Candidate A values understandable control; Candidate B values durable intellectual history.

## Failure mechanism

Either becomes weak alone: control without memory hides learning, while memory without a clear
workflow overwhelms the visitor.

## How to test it

Combine the readable pipeline with sealed reports and ask the Judge to trace one conclusion.
"""

EXPERIMENT = """# Experiment

## Question

Can a visitor trace a disagreement from role report to source evidence?

## Test cases

Watch the live analysis, open both blind proposals, and inspect the final trial.

## Success criteria

Every role is visible; every quoted report has a source; the Judge can identify the chosen
synthesis.

## Evidence format

One deterministic JSON result and the sealed role artifacts.
"""

DECISION = """# Decision

Decision ID: DEC-TUTORIAL
Story: US-001

## Evidence reviewed

Both blind proposals, their critique, and the synthetic traceability result.

## Selected direction

Combine the Architect's readable pipeline with the blind Heretic's insistence on visible history.

## Human rationale

The tutorial should be understandable first and intriguing second.

## Approval

Approved by simulated human: yes
"""

BUILDER = """# Implementation

## Approved scope

Assemble a disposable tutorial using the real controller, ledger, gates, and Logbook.

## Files changed

- `tutorial/guided-expedition.md`

## Patch

```diff
+ The Lab now tells its own story while exposing every source.
```

## Tests

The synthetic traceability result passed.
"""

REDTEAM = """# Red Team Report

## Confirmed defects

No production defect: this run is explicitly synthetic and isolated from the real ledger.

## Suspected defects

The performance is persuasive; a visitor could still confuse simulated success with production
proof.

## Missing tests

Docker and Windows remain outside this disposable tutorial.
"""

TRIAL = """# Completion Trial

Story: US-001

## Acceptance Criterion 1
Verdict: PASS

Evidence: both blind proposals are present and independently attributed.

## Red Team Findings

The synthetic boundary is prominently disclosed.

## Overall Verdict

READY

## Missing Evidence

Production behavior is deliberately not claimed.
"""

ARCHIVE = """# Experiment Archive

## Evidence index

The generated evidence index maps every synthetic artifact and ledger event.

## What happened

The Scientist made the question falsifiable. The Architect built a path. The blind Heretic refused
its easiest assumption. The Builder synthesized them; the Red Team qualified the claim; the Judge
allowed it to stand.

## What surprised us

The disagreement became most useful when the Logbook connected it to sources rather than drama
alone.

## Portfolio takeaway

One model did not become eight minds. A disciplined Lab made eight responsibilities inspectable.
"""


def _input(root: Path, name: str, content: str) -> Path:
    path = root / "tutorial-inputs" / name
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")
    return path


def prepare_tutorial(root: Path) -> str:
    initialize(root)
    (root / ".lab/TUTORIAL").write_text(
        "GUIDED SYNTHETIC TUTORIAL — no production evidence\n", encoding="utf-8"
    )
    return create_story(
        root,
        "THE CASE OF THE TOO-CONFIDENT MACHINE [FIRST CAST]",
        lab_depth="full",
        request=(
            "A coding agent says the project works everywhere. Put that confident claim through "
            "isolated roles, a real test, adversarial review, and an evidence-backed archive."
        ),
    ).id


def populate_tutorial(
    root: Path,
    story_id: str,
    *,
    delay: float = 0,
    stop: threading.Event | None = None,
    running: threading.Event | None = None,
) -> None:
    def step(action) -> bool:
        while running is not None and not running.wait(0.1):
            if stop and stop.is_set():
                return False
        if stop and stop.wait(delay):
            return False
        # Pause may be requested while the inter-step timer is running. Recheck
        # immediately before writing the next artifact so no event slips through.
        while running is not None and not running.wait(0.1):
            if stop and stop.is_set():
                return False
        action()
        return True

    actions = [
        lambda: run_role(
            root, role="product", story_id=story_id, adapter=FakeModelAdapter([PRODUCT])
        ),
        lambda: run_role(
            root, role="scientist", story_id=story_id, adapter=FakeModelAdapter([SCIENTIST])
        ),
        lambda: run_role(
            root, role="architect", story_id=story_id, adapter=FakeModelAdapter([ARCHITECT])
        ),
        lambda: run_role(
            root, role="heretic", story_id=story_id, adapter=FakeModelAdapter([HERETIC])
        ),
        lambda: record_artifact(root, story_id, "critique", _input(root, "critique.md", CRITIQUE)),
        lambda: record_artifact(
            root, story_id, "experiment", _input(root, "experiment.md", EXPERIMENT)
        ),
        lambda: approve_story(root, story_id, "experiment"),
        lambda: record_artifact(
            root, story_id, "evidence", _input(root, "results.json", '{"traceable": true}\n')
        ),
        lambda: record_artifact(root, story_id, "decision", _input(root, "decision.md", DECISION)),
        lambda: approve_story(root, story_id, "implementation"),
        lambda: run_role(
            root, role="builder", story_id=story_id, adapter=FakeModelAdapter([BUILDER])
        ),
        lambda: run_role(
            root, role="redteam", story_id=story_id, adapter=FakeModelAdapter([REDTEAM])
        ),
        lambda: run_role(root, role="judge", story_id=story_id, adapter=FakeModelAdapter([TRIAL])),
        lambda: approve_story(root, story_id, "done"),
        lambda: run_role(
            root, role="archivist", story_id=story_id, adapter=FakeModelAdapter([ARCHIVE])
        ),
    ]
    for action in actions:
        if not step(action):
            return


def tutorial_prompt_dismissed(repo_root: Path) -> bool:
    return (repo_root / ".lab/tutorial-prompt-dismissed").is_file()


def dismiss_tutorial_prompt(repo_root: Path) -> None:
    marker = repo_root / ".lab/tutorial-prompt-dismissed"
    marker.parent.mkdir(parents=True, exist_ok=True)
    marker.write_text(
        "Tutorial invitation dismissed. Run `lab tutorial` whenever you want the tour.\n"
    )


def _invitation_style(text: str, code: str, *, enabled: bool) -> str:
    return f"\x1b[{code}m{text}\x1b[0m" if enabled else text


def render_tutorial_invitation(width: int, *, dont_show_again: bool, styled: bool = False) -> str:
    """Render a restrained poster that remains readable without color support."""

    width = max(52, min(width, 92))
    content_width = width - 4

    def row(content: str = "") -> str:
        return f"┃ {content:<{content_width}} ┃"

    def wrapped(content: str) -> list[str]:
        return [
            row(line)
            for line in textwrap.wrap(
                content,
                content_width,
                break_long_words=False,
                break_on_hyphens=False,
            )
        ]

    border = "38;2;91;211;194"
    amber = "1;38;2;242;184;75"
    teal = "1;38;2;120;224;208"
    copy = "38;2;174;192;195"
    dim = "38;2;126;151;156"
    toggle = "ON  ✓" if dont_show_again else "OFF"
    lines: list[tuple[str, str]] = [
        ("┏" + "━" * (width - 2) + "┓", border),
        (row("≋<°)))><  CATFISH LAB"), teal),
        (row("FIRST CAST  /  OPTIONAL ORIENTATION"), amber),
        ("┠" + "─" * (width - 2) + "┨", border),
        (row(), copy),
    ]
    for sentence in (
        "One synthetic request will pass through the real Lab workflow.",
        "Your project stays untouched. The temporary evidence is removed afterward.",
        "An orientation appears before anything begins. You control the pace.",
    ):
        lines.extend((line, copy) for line in wrapped(sentence))
        lines.append((row(), copy))
    lines.extend(
        (
            (row(f"DON'T SHOW AGAIN  {toggle}  ·  Space toggles"), dim),
            (row(), copy),
            (row("ENTER  continue to orientation"), teal),
            (row("S / ESC  not now"), amber),
            (row("Later: lab tutorial"), dim),
            ("┗" + "━" * (width - 2) + "┛", border),
        )
    )
    return "\n".join(_invitation_style(line, style, enabled=styled) for line, style in lines)


def offer_tutorial(*, read_key: Callable[[float], str | None] | None = None) -> tuple[bool, bool]:
    """Offer, rather than force, the tutorial and return (run, dismiss)."""
    reader = read_key or _read_key
    dont_show_again = False
    previous = ""
    terminal_mode = _key_input() if read_key is None else nullcontext()
    try:
        sys.stdout.write("\x1b[?1049h\x1b[?25l")
        with terminal_mode:
            while True:
                width = shutil.get_terminal_size((84, 28)).columns
                current = render_tutorial_invitation(
                    width,
                    dont_show_again=dont_show_again,
                    styled=sys.stdout.isatty(),
                )
                if current != previous:
                    sys.stdout.write("\x1b[2J\x1b[H" + current + "\n")
                    sys.stdout.flush()
                    previous = current
                key = reader(0.25)
                if key is None:
                    continue
                if key == " ":
                    dont_show_again = not dont_show_again
                    continue
                if key in {"\n", "\r"}:
                    return True, dont_show_again
                if key.lower() in {"s", "q"} or key == "\x1b":
                    return False, dont_show_again
    finally:
        sys.stdout.write("\x1b[?25h\x1b[?1049l")
        sys.stdout.flush()


def run_tutorial(*, snapshot: bool, speed: float) -> str | None:
    """Run the guided expedition in a temporary repository."""
    with tempfile.TemporaryDirectory(prefix="catfish-lab-tutorial-") as directory:
        root = Path(directory)
        story_id = prepare_tutorial(root)
        if snapshot:
            populate_tutorial(root, story_id)
            return render(root, story_id)
        stop = threading.Event()
        started = threading.Event()
        running = threading.Event()
        running.set()
        errors: list[Exception] = []

        def produce() -> None:
            try:
                while not started.wait(0.1):
                    if stop.is_set():
                        return
                populate_tutorial(root, story_id, delay=speed, stop=stop, running=running)
            except Exception as error:  # pragma: no cover - surfaced after terminal closes
                errors.append(error)

        def toggle_pause() -> bool:
            if running.is_set():
                running.clear()
                return True
            running.set()
            return False

        producer = threading.Thread(target=produce, name="catfish-lab-tutorial", daemon=True)
        producer.start()
        try:
            watch(
                root,
                story_id,
                interval=0.25,
                initial_view="tutorial",
                tutorial_start=started.set,
                tutorial_pause=toggle_pause,
            )
        finally:
            stop.set()
            started.set()
            running.set()
            producer.join(timeout=max(1.0, speed + 0.5))
        if errors:
            raise errors[0]
    return None
