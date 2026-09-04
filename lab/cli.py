"""Local Catfish Lab CLI."""

import shutil
import subprocess
from pathlib import Path
from typing import Annotated

import typer

from .archive import write_evidence_index
from .artifacts import create_story, load_story
from .casefiles import case_files
from .config import TEMPLATES, initialize
from .controller import OutputContractError, reject_assessment, reopen_story, run_role
from .doctor import diagnose
from .harnesses import (
    active_profile,
    adapter_for_active,
    load_harnesses,
    profile_availability,
    select_harness,
)
from .logbook import render, watch
from .model import CodexTextAdapter, FakeModelAdapter, LabModelError, ProvidedTextAdapter
from .stages import Stage
from .tutorial import (
    dismiss_tutorial_prompt,
    offer_tutorial,
    run_tutorial,
    tutorial_prompt_dismissed,
)
from .workflow import (
    approve_story,
    create_request,
    draft_artifact,
    inbox_json,
    inbox_payload,
    next_actions,
    record_artifact,
    record_delay,
    request_next_action,
    set_story_depth,
)

app = typer.Typer(no_args_is_help=True)


def repo_root() -> Path:
    """Find an initialized Lab without depending on any host project's filenames."""
    current = Path.cwd().resolve()
    for candidate in (current, *current.parents):
        if (candidate / ".lab/config.yaml").is_file():
            return candidate
    raise typer.BadParameter("no Catfish Lab found; run `lab init` in the project root")


def _selected_adapter(root: Path, *, fake: bool, codex: bool, harness: bool, model: str | None):
    if sum((fake, codex, harness)) > 1:
        raise typer.BadParameter("choose only one of --fake, --codex, or --harness")
    if fake:
        raise RuntimeError("fake adapter output must be supplied by the caller")
    if codex:
        return CodexTextAdapter(model_id=model)
    return adapter_for_active(root, model_id=model)


def _run_with_delay(
    root: Path,
    *,
    role: str,
    story_id: str,
    adapter,
) -> Path:
    try:
        return run_role(root, role=role, story_id=story_id, adapter=adapter)
    except (LabModelError, OutputContractError) as error:
        try:
            harness = active_profile(root).name
        except ValueError:
            harness = "unconfigured"
        record_delay(root, story_id, str(error), harness=harness)
        raise typer.BadParameter(f"Work delayed: {error}") from error


@app.command("init")
def init_command() -> None:
    """Create missing Lab files without overwriting customizations."""
    # Initialization is intentionally rooted at the caller's current directory.
    # This lets an installed Catfish Lab attach to Python, Node, Rust, or plain
    # document repositories without requiring one of Catfish's own source files.
    created = initialize(Path.cwd().resolve())
    typer.echo(f"Catfish Lab initialized; created {len(created)} file(s).")
    typer.echo("Harness handoff: .lab/HARNESS.md")


@app.command("new-story", hidden=True)
def new_story(
    title: str = typer.Option(..., "--title"),
    depth: str = typer.Option("light", "--depth"),
) -> None:
    """Create the next collision-safe story directory."""
    if depth not in {"light", "full"}:
        raise typer.BadParameter("depth must be light or full")
    story = create_story(repo_root(), title, lab_depth=depth)
    typer.echo(story.id)


@app.command("request")
def request_command(
    prompt: str | None = typer.Option(None, "--prompt", help="The request to preserve."),
    source: Annotated[
        Path | None,
        typer.Option("--file", exists=True, dir_okay=False, readable=True),
    ] = None,
    title: str | None = typer.Option(None, "--title"),
    depth: str = typer.Option("light", "--depth"),
) -> None:
    """Submit arbitrary work to the Lab and print its story ID."""
    import sys

    if prompt is not None and source is not None:
        raise typer.BadParameter("use either --prompt or --file, not both")
    if source is not None:
        prompt = source.read_text(encoding="utf-8")
    elif prompt is None:
        prompt = typer.prompt("Request") if sys.stdin.isatty() else sys.stdin.read()
    try:
        story_id = create_request(repo_root(), prompt, title=title, depth=depth)
    except ValueError as error:
        raise typer.BadParameter(str(error)) from error
    typer.echo(story_id)


@app.command("request-action", hidden=True)
def request_action(story_id: str) -> None:
    """Ask the surrounding harness to perform a story's next valid action."""
    try:
        action = request_next_action(repo_root(), story_id)
    except ValueError as error:
        raise typer.BadParameter(str(error)) from error
    typer.echo(action)


@app.command("inbox")
def inbox(
    as_json: bool = typer.Option(False, "--json", help="Emit the stable harness protocol."),
    include_idle: bool = typer.Option(
        False, "--all", help="Include stories that have not been queued for the harness."
    ),
) -> None:
    """Show work explicitly queued for the surrounding coding harness."""
    root = repo_root()
    if as_json:
        typer.echo(inbox_json(root, include_idle=include_idle))
        return
    payload = inbox_payload(root, include_idle=include_idle)
    stories = payload["stories"]
    harness = payload["active_harness"]
    typer.echo(f"Active harness: {harness['label']} ({harness['kind']})")
    if not stories:
        typer.echo("The Lab inbox is empty.")
        return
    for story in stories:
        requested = story["requested_action"] or "not queued"
        typer.echo(f"{story['id']}  [{story['stage']}]  {story['title']}")
        typer.echo(f"  harness request: {requested}")
        for action in story["next_actions"]:
            typer.echo(f"  next: {action}")


@app.command("status")
def status(
    story_id: str | None = typer.Argument(None, help="Optional story to inspect."),
) -> None:
    """Show story stage, human gates, and artifacts."""
    root = repo_root()
    ids = (
        [story_id]
        if story_id
        else [path.name for path in sorted((root / ".lab/stories").glob("US-*"))]
    )
    if not ids:
        typer.echo("No stories.")
        return
    for identifier in ids:
        story = load_story(root, identifier)
        typer.echo(
            f"{story.id}  {story.title}\nstage: {story.stage.value}\ndepth: {story.lab_depth}"
        )
        gates = story.human
        typer.echo(
            "gates: "
            f"experiment={gates.experiment_approved} "
            f"implementation={gates.implementation_approved} done={gates.done_approved}"
        )
        actions = next_actions(root, identifier)
        typer.echo("next:")
        for action in actions:
            typer.echo(f"  {action}")


@app.command("depth", hidden=True)
def depth_command(story_id: str, depth: str) -> None:
    """Choose light delivery or the full experimental workflow before work begins."""
    try:
        set_story_depth(repo_root(), story_id, depth)
    except ValueError as error:
        raise typer.BadParameter(str(error)) from error
    typer.echo(f"{story_id} depth: {depth}")


@app.command("files")
def files_command(story_id: str) -> None:
    """List every expected and recorded document for one case."""

    root = repo_root()
    try:
        files = case_files(root, story_id)
    except (FileNotFoundError, ValueError) as error:
        raise typer.BadParameter(str(error)) from error
    typer.echo(f"{story_id} case files · .lab/stories/{story_id}/")
    for case_file in files:
        state = "READY" if case_file.ready else "WAITING"
        typer.echo(
            f"  {state:<7} {case_file.title:<22} .lab/stories/{story_id}/{case_file.relative_path}"
        )


@app.command("harness")
def harness_command(
    name: str | None = typer.Argument(None, help="Profile to make active."),
) -> None:
    """List harness profiles or select the one used by future role runs."""
    root = repo_root()
    if name:
        try:
            selected = select_harness(root, name)
        except ValueError as error:
            raise typer.BadParameter(str(error)) from error
        available, detail = profile_availability(selected)
        state = "ready" if available else "delayed"
        typer.echo(f"Active harness: {selected.label} [{state}] · {detail}")
        return
    try:
        active, profiles = load_harnesses(root)
    except ValueError as error:
        raise typer.BadParameter(str(error)) from error
    for profile in profiles:
        available, detail = profile_availability(profile)
        marker = "●" if profile.name == active else "○"
        state = "READY" if available else "DELAYED"
        typer.echo(f"{marker} {profile.name:<10} {profile.label:<20} {state:<7} {detail}")


@app.command("delay", hidden=True)
def delay_command(story_id: str, reason: str = typer.Option(..., "--reason")) -> None:
    """Tell the Logbook why requested work cannot proceed yet."""
    try:
        harness = active_profile(repo_root()).name
        record_delay(repo_root(), story_id, reason, harness=harness)
    except ValueError as error:
        raise typer.BadParameter(str(error)) from error
    typer.echo(f"Delay recorded for {story_id}: {reason}")


@app.command("reopen", hidden=True)
def reopen(
    story_id: str,
    target: str = typer.Option("implementation", "--to"),
    reason: str = typer.Option(..., "--reason"),
) -> None:
    """Record a backward transition for remediation and preserve the old review."""
    try:
        stage = Stage(target)
    except ValueError as error:
        raise typer.BadParameter(f"unknown stage: {target}") from error
    preserved = reopen_story(repo_root(), story_id=story_id, target=stage, reason=reason)
    suffix = f"; preserved {preserved.relative_to(repo_root())}" if preserved else ""
    typer.echo(f"Reopened {story_id} at {stage.value}{suffix}")


@app.command("run", hidden=True)
def run(
    role: str,
    story_id: str,
    fake: bool = typer.Option(False, "--fake", help="Use deterministic template output."),
    codex: bool = typer.Option(False, "--codex", help="Use a fresh tool-disabled Codex run."),
    harness: bool = typer.Option(False, "--harness", help="Use the active harness profile."),
    source: Annotated[
        Path | None,
        typer.Option("--from", exists=True, dir_okay=False, readable=True),
    ] = None,
    model: str | None = typer.Option(None, "--model"),
) -> None:
    """Run one fresh text-only role invocation."""
    if sum((fake, codex, harness, source is not None)) > 1:
        raise typer.BadParameter("choose one of --fake, --codex, --harness, or --from")
    root = repo_root()
    contract_template = {
        "product": "story",
        "scientist": "hypothesis",
        "architect": "proposal",
        "heretic": "proposal",
        "builder": "implementation",
        "redteam": "redteam",
        "judge": "trial",
        "archivist": "archive",
    }.get(role)
    if contract_template is None:
        raise typer.BadParameter(f"unknown role: {role}")
    output = TEMPLATES[contract_template]
    if source is not None:
        adapter = ProvidedTextAdapter(source.read_text(encoding="utf-8"))
    elif fake:
        adapter = FakeModelAdapter([output])
    else:
        adapter = _selected_adapter(root, fake=fake, codex=codex, harness=harness, model=model)
    destination = _run_with_delay(root, role=role, story_id=story_id, adapter=adapter)
    typer.echo(destination.relative_to(root))


@app.command("approve", hidden=True)
def approve(kind: str, story_id: str, yes: bool = typer.Option(False, "--yes")) -> None:
    """Record an explicit human approval gate."""
    if kind not in {"experiment", "implementation", "done"}:
        raise typer.BadParameter("kind must be experiment, implementation, or done")
    root = repo_root()
    if not yes and not typer.confirm(f"Approve {kind} for {story_id}?", default=False):
        raise typer.Abort()
    try:
        approve_story(root, story_id, kind)
    except ValueError as error:
        raise typer.BadParameter(str(error)) from error
    typer.echo(f"Recorded human approval: {kind} for {story_id}")


@app.command("request-changes")
def request_changes(story_id: str, reason: str = typer.Option(..., "--reason")) -> None:
    """Reject the completion assessment with actionable human feedback."""
    root = repo_root()
    try:
        rejection = reject_assessment(root, story_id=story_id, reason=reason)
        action = request_next_action(root, story_id)
    except ValueError as error:
        raise typer.BadParameter(str(error)) from error
    typer.echo(f"Feedback: {rejection.feedback.relative_to(root)}")
    typer.echo(f"Preserved {len(rejection.preserved)} superseded artifacts")
    typer.echo(f"Queued remediation: {action}")


@app.command("record", hidden=True)
def record(
    kind: str,
    story_id: str,
    source: Annotated[Path, typer.Option("--from", exists=True, dir_okay=False, readable=True)],
) -> None:
    """Record a completed critique, experiment, evidence file, or decision."""
    destination = record_artifact(repo_root(), story_id, kind, source)
    typer.echo(destination.relative_to(repo_root()))


@app.command("draft", hidden=True)
def draft(kind: str, story_id: str) -> None:
    """Create an editable critique, experiment, or decision template."""
    destination = draft_artifact(repo_root(), story_id, kind)
    typer.echo(destination.relative_to(repo_root()))


@app.command("logbook")
def logbook(
    story_id: str | None = typer.Argument(None, help="Optional story chapter to display."),
    live: bool = typer.Option(True, "--live/--snapshot", help="Follow new Lab events."),
) -> None:
    """Open the Lab's live narrative evidence console."""
    root = repo_root()
    if story_id:
        load_story(root, story_id)
    if live:
        import sys

        if sys.stdout.isatty() and story_id is None and not tutorial_prompt_dismissed(root):
            begin, dismiss = offer_tutorial()
            if dismiss:
                dismiss_tutorial_prompt(root)
            if begin:
                run_tutorial(snapshot=False, speed=1.5)
        watch(root, story_id)
    else:
        typer.echo(render(root, story_id))


@app.command("tutorial")
def tutorial(
    snapshot: bool = typer.Option(False, "--snapshot", help="Render the completed lesson once."),
    speed: float = typer.Option(1.5, "--speed", min=0.05, max=10.0),
) -> None:
    """Revisit the guided, disposable tour of the complete Lab."""
    import sys

    as_snapshot = snapshot or not sys.stdout.isatty()
    output = run_tutorial(snapshot=as_snapshot, speed=speed)
    if output is not None:
        typer.echo(output)


@app.command("docs")
def docs(
    build: bool = typer.Option(False, "--build", help="Build the static site and exit."),
    host: str = typer.Option("127.0.0.1", "--host"),
    port: int = typer.Option(8000, "--port", min=1, max=65535),
) -> None:
    """Serve the local handbook, or build it as a static site."""
    executable = shutil.which("mkdocs")
    if executable is None:
        raise typer.BadParameter(
            "documentation support is not installed; run `uv sync --extra docs`"
        )
    command = (
        [executable, "build", "--strict"]
        if build
        else [
            executable,
            "serve",
            "--dev-addr",
            f"{host}:{port}",
        ]
    )
    completed = subprocess.run(command, cwd=repo_root(), check=False)
    if completed.returncode:
        raise typer.Exit(completed.returncode)


@app.command("index-evidence", hidden=True)
def index_evidence(story_id: str) -> None:
    """Regenerate the Archivist's deterministic citation map."""
    markdown, machine = write_evidence_index(repo_root(), story_id)
    typer.echo(f"{markdown.relative_to(repo_root())}\n{machine.relative_to(repo_root())}")


@app.command("trial", hidden=True)
def trial(
    story_id: str,
    fake: bool = typer.Option(False, "--fake"),
    codex: bool = typer.Option(False, "--codex"),
    harness: bool = typer.Option(False, "--harness"),
    model: str | None = typer.Option(None, "--model"),
) -> None:
    """Run the Completion Trial judge."""
    if sum((fake, codex, harness)) > 1:
        raise typer.BadParameter("choose only one of --fake, --codex, or --harness")
    root = repo_root()
    adapter = (
        FakeModelAdapter([TEMPLATES["trial"]])
        if fake
        else _selected_adapter(root, fake=fake, codex=codex, harness=harness, model=model)
    )
    destination = _run_with_delay(
        root,
        role="judge",
        story_id=story_id,
        adapter=adapter,
    )
    typer.echo(destination.relative_to(root))


@app.command("archive", hidden=True)
def archive(
    story_id: str,
    fake: bool = typer.Option(False, "--fake"),
    codex: bool = typer.Option(False, "--codex"),
    harness: bool = typer.Option(False, "--harness"),
    model: str | None = typer.Option(None, "--model"),
) -> None:
    """Run the Archivist over finalized visible artifacts."""
    if sum((fake, codex, harness)) > 1:
        raise typer.BadParameter("choose only one of --fake, --codex, or --harness")
    root = repo_root()
    adapter = (
        FakeModelAdapter([TEMPLATES["archive"]])
        if fake
        else _selected_adapter(root, fake=fake, codex=codex, harness=harness, model=model)
    )
    destination = _run_with_delay(
        root,
        role="archivist",
        story_id=story_id,
        adapter=adapter,
    )
    typer.echo(destination.relative_to(root))


@app.command("doctor")
def doctor() -> None:
    """Validate deterministic installation invariants."""
    failures = diagnose(repo_root())
    if failures:
        for failure in failures:
            typer.echo(f"FAIL: {failure}", err=True)
        raise typer.Exit(1)
    typer.echo("Catfish Lab doctor: PASS")
