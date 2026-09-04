"""Role context policies and artifact contracts."""

from dataclasses import dataclass
from pathlib import Path

from .config import load_config
from .context import ContextPolicy

GLOBAL_DENY = (
    ".env",
    ".env.*",
    "**/.env",
    "**/.env.*",
    "**/*secret*",
    "**/*credential*",
    ".git/**",
    ".venv/**",
    "venv/**",
    "node_modules/**",
    "target/**",
    "dist/**",
    "build/**",
    "site/**",
)

DEFAULT_PROJECT_CONTEXT = (
    "src/**/*",
    "app/**/*",
    "lib/**/*",
    "packages/**/*",
    "lab/**/*",
    "tests/**/*",
    "docs/**/*",
    ".github/**/*",
    "*.py",
    "*.js",
    "*.ts",
    "*.tsx",
    "*.rs",
    "*.go",
    "*.java",
    "*.md",
    "*.toml",
    "*.yaml",
    "*.yml",
    "package.json",
    "Cargo.toml",
    "go.mod",
    "Dockerfile",
    "compose.yaml",
)


@dataclass(frozen=True)
class RoleContract:
    artifact: str
    template: str
    policy: ContextPolicy
    blind_required: bool = False


def _context_settings(repo_root: Path | None) -> tuple[tuple[str, ...], tuple[str, ...], int]:
    if repo_root is None:
        return DEFAULT_PROJECT_CONTEXT, GLOBAL_DENY, 1_000_000
    config = load_config(repo_root)
    context = config.get("context", {})
    security = config.get("security", {})
    if not isinstance(context, dict) or not isinstance(security, dict):
        raise ValueError("context and security configuration must be mappings")
    raw_include = context.get("include_globs", DEFAULT_PROJECT_CONTEXT)
    raw_deny = security.get("deny_globs", ())
    max_bytes = context.get("max_bytes", 1_000_000)
    if not isinstance(raw_include, list) or not all(isinstance(item, str) for item in raw_include):
        raise ValueError("context.include_globs must be a list of paths")
    if not isinstance(raw_deny, list) or not all(isinstance(item, str) for item in raw_deny):
        raise ValueError("security.deny_globs must be a list of paths")
    if not isinstance(max_bytes, int) or not 1 <= max_bytes <= 10_000_000:
        raise ValueError("context.max_bytes must be between 1 and 10000000")
    deny = tuple(dict.fromkeys((*GLOBAL_DENY, *raw_deny)))
    return tuple(raw_include), deny, max_bytes


def contract_for(role: str, story_id: str, repo_root: Path | None = None) -> RoleContract:
    project_context, deny, max_bytes = _context_settings(repo_root)

    def policy(allowed: tuple[str, ...], *extra_deny: str) -> ContextPolicy:
        return ContextPolicy(allowed, deny + extra_deny, max_bytes=max_bytes)

    shared = (
        "README.md",
        "AGENTS.md",
        ".lab/HARNESS.md",
        ".lab/project.md",
        "pyproject.toml",
        "docs/**/*.md",
        f".lab/stories/{story_id}/story.md",
        f".lab/stories/{story_id}/request.md",
    )
    implementation = project_context
    contracts = {
        "product": RoleContract("story.md", "story.md", policy(shared)),
        "scientist": RoleContract(
            "hypothesis.md",
            "hypothesis.md",
            policy(shared + implementation),
        ),
        "architect": RoleContract(
            "candidates/A.md",
            "proposal.md",
            policy(
                shared + implementation + (f".lab/stories/{story_id}/hypothesis.md",),
                f".lab/stories/{story_id}/candidates/B.md",
            ),
            True,
        ),
        "heretic": RoleContract(
            "candidates/B.md",
            "proposal.md",
            policy(
                shared + implementation + (f".lab/stories/{story_id}/hypothesis.md",),
                f".lab/stories/{story_id}/candidates/A.md",
            ),
            True,
        ),
        "builder": RoleContract(
            "implementation.md",
            "implementation.md",
            policy(
                shared
                + implementation
                + (
                    f".lab/stories/{story_id}/decision.md",
                    f".lab/stories/{story_id}/evidence/human-feedback-*.md",
                ),
            ),
        ),
        "redteam": RoleContract(
            "redteam.md",
            "redteam.md",
            policy(
                shared
                + (
                    f".lab/stories/{story_id}/implementation.md",
                    f".lab/stories/{story_id}/evidence/**/*",
                    "pyproject.toml",
                    "uv.lock",
                )
                + implementation,
            ),
        ),
        "judge": RoleContract(
            "trial.md",
            "trial.md",
            policy(
                shared
                + (
                    f".lab/stories/{story_id}/evidence/**/*",
                    f".lab/stories/{story_id}/redteam.md",
                    "pyproject.toml",
                    "uv.lock",
                )
                + implementation,
            ),
        ),
        "archivist": RoleContract(
            "archive.md",
            "archive.md",
            policy((f".lab/stories/{story_id}/**/*.md",), "**/*secret*"),
        ),
    }
    try:
        return contracts[role]
    except KeyError as error:
        raise ValueError(f"unknown role: {role}") from error
