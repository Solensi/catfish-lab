"""Catfish Lab configuration and non-destructive bootstrap."""

from pathlib import Path

import yaml

from .harnesses import HARNESS_CONFIG

REQUIRED_ROLES = (
    "product",
    "scientist",
    "architect",
    "heretic",
    "builder",
    "redteam",
    "judge",
    "archivist",
)
REQUIRED_TEMPLATES = (
    "story",
    "hypothesis",
    "proposal",
    "critique",
    "experiment",
    "decision",
    "implementation",
    "redteam",
    "trial",
    "archive",
)

STORY_README = """# Story Workspace: {story_id}

This directory begins deliberately sparse. A missing role artifact means that role has not completed
its work; it is not permission to invent an opinion on the role's behalf.

| Role | Artifact created after a successful run |
|---|---|
| The Product Steward | `story.md` |
| The Scientist | `hypothesis.md` |
| The Architect | `candidates/A.md` |
| The blind Heretic | `candidates/B.md` |
| The Builder | `implementation.md` |
| The Red Team | `redteam.md` |
| The Judge | `trial.md` |
| The Archivist | `archive.md` |

The full workflow also records `critiques/review.md`, `experiment.md`, files under `evidence/`, and
`decision.md`. Run `lab status {story_id}` for the next valid action or `lab logbook {story_id}` to
inspect the complete situation interactively. `story.yaml` is machine state; do not hand-edit gates.
"""

CONSTITUTION = """# Catfish Lab Constitution

1. Humans have final authority.
2. Claims are not evidence.
3. If agents disagree about something measurable, prefer an experiment over rhetorical debate.
4. An implementation agent may not act as its own final reviewer.
5. A run must not inherit hidden conversational state from another run.
6. Agent communication occurs through explicit artifacts.
7. Every experiment must define a falsifiable or observable success criterion before results are inspected.
8. Unexpected failures are valid experimental results and must not be hidden.
9. Prefer the simplest solution that survives the relevant tests.
10. DONE is a claim that must be demonstrated.
11. Agents must distinguish observed evidence, inference, recommendation, and uncertainty.
12. Private application secrets, API keys, and hidden recovery answers must never be included in Lab prompts or logs.
13. Role names describe responsibilities, not distinct underlying models.
14. When a deterministic test can answer a question, prefer it over another LLM opinion.
15. Human decisions must record a short rationale when overriding experimental evidence.
"""

PROJECT_CHARTER = """# Project Charter

This file is durable context shared with every working role. Keep it short and project-specific.

## Mission

Build and maintain this repository so a new person can understand, run, test, and extend it.

## Definition of healthy

- Setup is reproducible on a fresh clone and documented for native and container use.
- Behavior is covered by proportionate automated tests and observable evidence.
- User-facing language explains intent before implementation detail.
- Architecture, operator instructions, and current behavior agree.
- Maintenance work leaves fewer unexplained files and no disposable residue.

## Local conventions

Record repository-specific constraints, supported platforms, and commands here.

## Known boundaries

Secrets and private data never enter Lab artifacts. Human approval remains required at explicit gates.
"""

HARNESS_GUIDE = """# Catfish Lab Harness Guide

This file is the portable handoff contract for any tool-capable coding agent working in this project.

1. Run `lab init`, then read `lab inbox --json`.
2. Act only on a story's `requested_action`; an empty `stories` list means nothing is queued.
3. Read its `request_artifact`, `.lab/project.md`, `.lab/constitution.md`, and cited artifacts.
   If the inbox includes `feedback`, its reason and artifact are required remediation context.
4. Perform repository edits and deterministic checks with your normal tools. Text-only Lab roles must
   never pretend that a patch was applied.
5. Report a blocker immediately with `lab delay US-NNN --reason "concise diagnostic"`.
6. Re-read the inbox after each action. Continue only within the user's request and stop at every
   human approval gate.
7. Before a completion claim, run the project's checks, `lab index-evidence US-NNN`, and `lab doctor`.

Never place secrets, credentials, private prompts, or hidden conversational state in Lab artifacts.
The ledger and sealed artifacts are authoritative; Logbook narration is a derived reading aid.

OpenCode users may launch this repository's bundled tool-capable proxy with
`opencode --agent catfish .`; its instruction lives at `.opencode/agents/catfish.md`.
"""

CONFIG = """version: 1
paths:
  project_spec:
    - .lab/project.md
context:
  include_globs:
    - src/**/*
    - app/**/*
    - lib/**/*
    - packages/**/*
    - lab/**/*
    - tests/**/*
    - docs/**/*
    - .github/**/*
    - "*.py"
    - "*.js"
    - "*.ts"
    - "*.tsx"
    - "*.rs"
    - "*.go"
    - "*.java"
    - "*.md"
    - "*.toml"
    - "*.yaml"
    - "*.yml"
    - package.json
    - Cargo.toml
    - go.mod
    - Dockerfile
    - compose.yaml
  max_bytes: 1000000
security:
  deny_globs:
    - .env
    - .env.*
    - "**/.env"
    - "**/.env.*"
    - "**/*secret*"
    - "**/*credential*"
    - ".git/**"
    - ".venv/**"
    - "venv/**"
    - "node_modules/**"
    - "target/**"
    - "dist/**"
    - "build/**"
    - "site/**"
  redact_environment: true
runs:
  require_fresh_session: true
  record_prompt_hash: true
  record_context_hashes: true
  save_full_prompts: false
human_gate:
  required_before_builder: true
  required_before_done: true
artifacts:
  story_prefix: US
  experiment_prefix: EXP
  decision_prefix: DEC
"""

ROLE_MISSIONS = {
    "product": (
        "Turn an idea into a scoped user story.",
        "user value and observable acceptance criteria",
        "story.md",
    ),
    "scientist": (
        "Turn uncertainty into a testable question.",
        "falsifiable evidence",
        "hypothesis.md",
    ),
    "architect": (
        "Commit to one conventional maintainable proposal.",
        "simplicity, boundaries, and testability",
        "candidates/A.md",
    ),
    "heretic": (
        "Attack an assumption shared by the obvious solution.",
        "a genuinely independent alternative",
        "candidates/B.md",
    ),
    "builder": (
        "Implement only a human-approved design.",
        "correct code and tests; return a unified patch because the run is text-only",
        "implementation.md",
    ),
    "redteam": (
        "Find reproducible requirement violations.",
        "concrete defects and counterexamples",
        "redteam.md",
    ),
    "judge": (
        "Treat DONE as an unproven claim and conduct the Completion Trial.",
        "criterion-by-criterion evidence",
        "trial.md",
    ),
    "archivist": (
        "Produce concise portfolio evidence from finalized artifacts.",
        "accurate experimental history with path-level citations",
        "archive.md",
    ),
}

TEMPLATES = {
    "story": "# User Story\n\n## Statement\n\nAs a ...\nI want ...\nSo that ...\n\n## User value\n\n## Acceptance criteria\n\n- [ ]\n\n## Out of scope\n\n## Unknowns\n\n## AI experiment required?\n\nno\n\n## Notes\n",
    "hypothesis": "# Hypothesis\n\n## Observation\n\n## Question\n\n## Hypothesis\n\n## Independent variable\n\n## Dependent variables\n\n## Controls\n\n## Evidence that would change our mind\n\n## Smallest useful experiment\n\n## Confounders\n",
    "proposal": "# Candidate Proposal\n\n## Summary\n\n## Core idea\n\n## Assumptions\n\n## Architecture / behavior\n\n## Expected advantages\n\n## Failure modes\n\n## Cost / complexity\n\n## Testability\n\n## What would falsify this proposal?\n",
    "critique": "# Critique\n\n## Claim under challenge\n\n## Failure mechanism\n\n## Observable consequence\n\n## How to test it\n\n## Severity if true\n",
    "experiment": "# Experiment\n\n## Question\n\n## Hypothesis\n\n## Candidate A\n\n## Candidate B\n\n## Independent variable\n\n## Dependent variables\n\n## Controls\n\n## Test cases\n\n## Success criteria\n\n## Stop conditions\n\n## Confounders\n\n## Evidence format\n",
    "decision": "# Decision\n\nDecision ID: DEC-___\nStory: US-___\n\n## Evidence reviewed\n\n## Selected direction\n\n## Rejected alternatives\n\n## Human rationale\n\n## AI recommendations considered\n\n## Known uncertainty\n\n## Approval\n\nApproved by human: no\nDate:\n",
    "implementation": "# Implementation\n\n## Approved scope\n\n## Files changed\n\n## Patch\n\n## Tests\n\n## Remaining uncertainty\n",
    "redteam": "# Red Team Report\n\n## Confirmed defects\n\n## Suspected defects\n\n## Missing tests\n\n## Design concerns\n\n## Areas tested without finding a defect\n",
    "trial": "# Completion Trial\n\nStory: US-___\n\n## Acceptance Criterion 1\nVerdict: UNTESTED\n\nEvidence:\n\n## Red Team Findings\n\n## Overall Verdict\n\nNOT_READY\n\n## Missing Evidence\n",
    "archive": "# Experiment Archive\n\n## Evidence index\n\nCite `.lab/stories/US-___/evidence/EVIDENCE.md` and the relevant source artifacts.\n\n## What we believed\n\n## What we tried\n\n## What happened\n\n## What surprised us\n\n## What changed\n\n## What remains uncertain\n\n## Human decision\n\n## Portfolio takeaway\n",
}


def role_text(name: str) -> str:
    mission, target, output = ROLE_MISSIONS[name]
    exclusions = {
        "architect": "Candidate B and Heretic reasoning.",
        "heretic": "Candidate A and Architect reasoning.",
        "builder": "Unapproved designs and authority to review itself.",
        "redteam": "Builder conversational reasoning.",
    }.get(name, "Artifacts not explicitly included by the context policy.")
    special_rule = (
        "The run is text-only: do not claim to edit or test files. Provide a complete unified "
        "diff in the Patch section for the controller/human to validate and import."
        if name == "builder"
        else (
            "Treat EVIDENCE.md as the citation map. Cite repository-relative artifact paths for "
            "factual claims, distinguish missing evidence from negative results, and never turn "
            "inference into observed history."
            if name == "archivist"
            else ""
        )
    )
    return f"""# Role: {name}

## Mission
{mission}

## Optimization target
{target}.

## You receive
The constitution, current task, and explicitly allowlisted artifacts.

## You do not receive
{exclusions}

## Rules
Use only supplied evidence. Mark observation, inference, recommendation, and uncertainty.
{special_rule}

## Required output
`{output}` following its template.

## Failure conditions
Invented evidence, hidden-context claims, secret disclosure, or violation of human authority.
"""


def initialize(repo_root: Path) -> list[Path]:
    lab_root = repo_root / ".lab"
    created: list[Path] = []
    for relative in ("schema", "roles", "templates", "stories", "runs"):
        (lab_root / relative).mkdir(parents=True, exist_ok=True)
    files = {
        lab_root / "README.md": (
            "# Catfish Lab State Directory\n\n"
            "Schema version: 1\n\n"
            "This directory stores role contracts, templates, story artifacts, run metadata, "
            "and the integrity-linked ledger. Use Lab CLI commands for state changes; do not "
            "hand-edit approvals or ledger history. Harness profiles live in `harnesses.yaml`. "
            "See `docs/lab/operator-guide.md`.\n"
        ),
        lab_root / "constitution.md": CONSTITUTION,
        lab_root / "project.md": PROJECT_CHARTER,
        lab_root / "HARNESS.md": HARNESS_GUIDE,
        lab_root / "config.yaml": CONFIG,
        lab_root / "harnesses.yaml": HARNESS_CONFIG,
        lab_root / "ledger.jsonl": "",
        lab_root / "stories" / ".gitkeep": "",
        lab_root / "runs" / ".gitkeep": "",
        lab_root
        / "schema"
        / "story.schema.json": '{"$schema":"https://json-schema.org/draft/2020-12/schema","title":"Catfish Lab story","type":"object","required":["id","title","stage","human","artifacts"]}\n',
        lab_root
        / "schema"
        / "run-record.schema.json": '{"$schema":"https://json-schema.org/draft/2020-12/schema","title":"Catfish Lab run record","type":"object","required":["run_id","role","story_id","status","isolation"]}\n',
        lab_root
        / "schema"
        / "decision.schema.json": '{"$schema":"https://json-schema.org/draft/2020-12/schema","title":"Catfish Lab decision","type":"object","required":["story_id","approved_by_human"]}\n',
    }
    files.update({lab_root / "roles" / f"{name}.md": role_text(name) for name in REQUIRED_ROLES})
    files.update({lab_root / "templates" / f"{name}.md": text for name, text in TEMPLATES.items()})
    for path, content in files.items():
        if not path.exists():
            path.write_text(content, encoding="utf-8")
            created.append(path)
    for directory in sorted((lab_root / "stories").glob("US-*")):
        overview = directory / "README.md"
        if directory.is_dir() and not overview.exists():
            overview.write_text(STORY_README.format(story_id=directory.name), encoding="utf-8")
            created.append(overview)
    return created


def load_config(repo_root: Path) -> dict[str, object]:
    value = yaml.safe_load((repo_root / ".lab/config.yaml").read_text(encoding="utf-8"))
    if not isinstance(value, dict) or value.get("version") != 1:
        raise ValueError(".lab/config.yaml must contain version: 1")
    return value
