"""One discoverable index over the durable documents attached to a Lab case."""

from dataclasses import dataclass
from pathlib import Path

from .artifacts import load_story, story_dir


@dataclass(frozen=True)
class CaseFile:
    """A human label and stable repository-relative path for one case document."""

    title: str
    author: str
    relative_path: str
    path: Path

    @property
    def ready(self) -> bool:
        return self.path.is_file()


CASE_FILE_LAYOUT = (
    ("Original request", "Human", "request.md"),
    ("Scoped story", "Product Steward", "story.md"),
    ("Hypothesis", "Scientist", "hypothesis.md"),
    ("Candidate A", "Architect", "candidates/A.md"),
    ("Candidate B", "blind Heretic", "candidates/B.md"),
    ("Proposal critique", "Lab workflow", "critiques/review.md"),
    ("Experiment plan", "Lab workflow", "experiment.md"),
    ("Human decision", "Lab workflow", "decision.md"),
    ("Implementation record", "Builder", "implementation.md"),
    ("Adversarial review", "Red Team", "redteam.md"),
    ("Completion trial", "Judge", "trial.md"),
    ("Experiment archive", "Archivist", "archive.md"),
    ("Evidence map", "Archivist", "evidence/EVIDENCE.md"),
    ("Evidence index", "Archivist", "evidence/evidence-index.json"),
)


def case_files(repo_root: Path, story_id: str) -> list[CaseFile]:
    """Return expected documents first, followed by arbitrary recorded evidence."""

    load_story(repo_root, story_id)
    directory = story_dir(repo_root, story_id)
    files = [
        CaseFile(title, author, relative, directory / relative)
        for title, author, relative in CASE_FILE_LAYOUT
    ]
    indexed = {item.path for item in files}
    evidence = directory / "evidence"
    if evidence.is_dir():
        for path in sorted(candidate for candidate in evidence.rglob("*") if candidate.is_file()):
            if path not in indexed:
                relative = path.relative_to(directory).as_posix()
                files.append(CaseFile(path.name, "Recorded evidence", relative, path))
    return files


def render_case_file(case_file: CaseFile) -> str:
    """Read a text artifact in a form that remains legible in the Markdown viewer."""

    content = case_file.path.read_text(encoding="utf-8", errors="replace")
    if case_file.path.suffix.lower() == ".json":
        return f"```json\n{content.rstrip()}\n```"
    return content
