from pathlib import Path

from lab.capsule import CapabilityManifest, Isolation, build_capsule, context_digest
from lab.context import ContextPolicy


def test_capsule_physically_omits_forbidden_artifact(tmp_path: Path) -> None:
    candidate = tmp_path / ".lab/stories/US-014/candidates/A.md"
    candidate.parent.mkdir(parents=True)
    candidate.write_text("ARCH_ONLY_123")
    (tmp_path / "spec.md").write_text("spec")
    capsule = build_capsule(
        tmp_path,
        ContextPolicy(("**/*",), (".lab/stories/US-014/candidates/A.md",)),
    )
    try:
        assert capsule.manifest["isolation"] == Isolation.CAPSULED_TOOL.value
        assert not (capsule.workspace / ".lab/stories/US-014/candidates/A.md").exists()
        assert "ARCH_ONLY_123" not in (capsule.root / "MANIFEST.json").read_text()
    finally:
        capsule.destroy()


def test_context_digest_ignores_manifest_enumeration_order() -> None:
    capabilities = CapabilityManifest("workspace_only", True, False)
    files = [{"path": "b", "sha256": "2"}, {"path": "a", "sha256": "1"}]
    first = context_digest(
        role_hash="r",
        constitution_hash="c",
        files=files,
        task_hash="t",
        capabilities=capabilities,
    )
    second = context_digest(
        role_hash="r",
        constitution_hash="c",
        files=list(reversed(files)),
        task_hash="t",
        capabilities=capabilities,
    )
    assert first == second
