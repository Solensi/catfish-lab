"""Positive context resolution with deny rules taking precedence."""

from dataclasses import dataclass
from fnmatch import fnmatch
from pathlib import Path


class ContextError(ValueError):
    pass


@dataclass(frozen=True)
class ContextPolicy:
    allowed_globs: tuple[str, ...]
    forbidden_globs: tuple[str, ...]
    max_bytes: int = 1_000_000


def _matches(path: str, patterns: tuple[str, ...]) -> bool:
    return any(fnmatch(path, pattern) or fnmatch(f"/{path}", pattern) for pattern in patterns)


def resolve_repo_path(repo_root: Path, candidate: Path) -> Path:
    root = repo_root.resolve()
    if candidate.is_absolute():
        raise ContextError(f"absolute path is forbidden: {candidate}")
    resolved = (root / candidate).resolve()
    if not resolved.is_relative_to(root):
        raise ContextError(f"path escapes repository: {candidate}")
    return resolved


def resolve_context(repo_root: Path, policy: ContextPolicy) -> list[Path]:
    root = repo_root.resolve()
    selected: dict[str, Path] = {}
    for pattern in policy.allowed_globs:
        if Path(pattern).is_absolute() or ".." in Path(pattern).parts:
            raise ContextError(f"unsafe allowed glob: {pattern}")
        for path in root.glob(pattern):
            if path.is_symlink():
                raise ContextError(f"symlinks are not allowed in context: {path.relative_to(root)}")
            if not path.is_file():
                continue
            relative = path.relative_to(root).as_posix()
            if relative == ".git" or relative.startswith(".git/"):
                continue
            if _matches(relative, policy.forbidden_globs):
                continue
            try:
                if path.stat().st_size > policy.max_bytes:
                    continue
                payload = path.read_bytes()
                payload.decode("utf-8")
            except (OSError, UnicodeDecodeError):
                # Broad project globs should find source without letting an
                # image, archive, or generated binary poison a role run.
                continue
            if b"\0" in payload:
                continue
            selected[relative] = path
    ordered = [selected[key] for key in sorted(selected)]
    total = sum(path.stat().st_size for path in ordered)
    if total > policy.max_bytes:
        raise ContextError(f"resolved context exceeds {policy.max_bytes} bytes")
    return ordered
