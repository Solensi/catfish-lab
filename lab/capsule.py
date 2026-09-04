"""Ephemeral positive-copy context capsules for tool-enabled blind runs."""

import shutil
import tempfile
from dataclasses import dataclass
from enum import StrEnum
from pathlib import Path

from .context import ContextPolicy, resolve_context
from .util import canonical_json, sha256_bytes, sha256_file


class Isolation(StrEnum):
    TEXT_ONLY = "text_only"
    CAPSULED_TOOL = "capsuled_tool"
    SOFT_TOOL = "soft_tool"


@dataclass(frozen=True)
class CapabilityManifest:
    filesystem: str
    shell: bool
    network: bool
    git_metadata: bool = False


@dataclass
class ContextCapsule:
    root: Path
    workspace: Path
    output: Path
    manifest: dict[str, object]

    def destroy(self) -> None:
        shutil.rmtree(self.root)


def context_digest(
    *,
    role_hash: str,
    constitution_hash: str,
    files: list[dict[str, object]],
    task_hash: str,
    capabilities: CapabilityManifest,
) -> str:
    payload = {
        "role_hash": role_hash,
        "constitution_hash": constitution_hash,
        "files": sorted(files, key=lambda item: str(item["path"])),
        "task_hash": task_hash,
        "capabilities": capabilities.__dict__,
    }
    return sha256_bytes(canonical_json(payload))


def build_capsule(
    repo_root: Path,
    policy: ContextPolicy,
    *,
    capabilities: CapabilityManifest | None = None,
) -> ContextCapsule:
    source_root = repo_root.resolve()
    capabilities = capabilities or CapabilityManifest("workspace_only", True, False)
    capsule_root = Path(tempfile.mkdtemp(prefix="catfish-lab-run-"))
    workspace = capsule_root / "workspace"
    output = capsule_root / "output"
    workspace.mkdir()
    output.mkdir()
    entries: list[dict[str, object]] = []
    try:
        for source in resolve_context(source_root, policy):
            relative = source.relative_to(source_root)
            destination = workspace / relative
            destination.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(source, destination, follow_symlinks=False)
            entries.append(
                {
                    "path": relative.as_posix(),
                    "capsule_path": f"workspace/{relative.as_posix()}",
                    "size": destination.stat().st_size,
                    "sha256": sha256_file(destination),
                }
            )
        manifest = {
            "version": 1,
            "isolation": Isolation.CAPSULED_TOOL.value,
            "capabilities": capabilities.__dict__,
            "files": entries,
        }
        (capsule_root / "MANIFEST.json").write_bytes(canonical_json(manifest) + b"\n")
        return ContextCapsule(capsule_root, workspace, output, manifest)
    except Exception:
        shutil.rmtree(capsule_root)
        raise
