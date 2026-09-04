"""Structural installation audit for Catfish Lab."""

import json
from pathlib import Path

from .artifacts import load_story
from .capsule import build_capsule
from .config import REQUIRED_ROLES, REQUIRED_TEMPLATES, load_config
from .context import ContextPolicy
from .harnesses import load_harnesses
from .ledger import read_records, verify_ledger
from .roles import contract_for


def diagnose(repo_root: Path) -> list[str]:
    failures: list[str] = []
    required = [
        repo_root / ".lab/constitution.md",
        repo_root / ".lab/HARNESS.md",
        repo_root / ".lab/project.md",
        repo_root / ".lab/config.yaml",
        repo_root / ".lab/harnesses.yaml",
        repo_root / ".lab/ledger.jsonl",
    ]
    required.extend(repo_root / f".lab/roles/{name}.md" for name in REQUIRED_ROLES)
    required.extend(repo_root / f".lab/templates/{name}.md" for name in REQUIRED_TEMPLATES)
    required.extend(
        repo_root / f".lab/schema/{name}.schema.json"
        for name in ("story", "run-record", "decision")
    )
    for path in required:
        if not path.exists():
            failures.append(f"missing: {path.relative_to(repo_root)}")
    try:
        config = load_config(repo_root)
        deny = tuple(config["security"]["deny_globs"])
        ContextPolicy(("**/*",), deny)
        contract_for("builder", "US-000", repo_root)
    except Exception as error:
        failures.append(f"invalid config: {error}")
    try:
        load_harnesses(repo_root)
    except Exception as error:
        failures.append(f"invalid harness config: {error}")
    try:
        read_records(repo_root / ".lab/ledger.jsonl")
        failures.extend(
            f"ledger integrity: {failure}"
            for failure in verify_ledger(repo_root / ".lab/ledger.jsonl")
        )
    except Exception as error:
        failures.append(f"invalid ledger: {error}")
    for path in sorted((repo_root / ".lab/stories").glob("US-*")):
        try:
            load_story(repo_root, path.name)
        except Exception as error:
            failures.append(f"invalid story {path.name}: {error}")
    try:
        capsule = build_capsule(
            repo_root,
            ContextPolicy((".lab/project.md", ".env"), (".env",)),
        )
        if any(entry["path"] == ".env" for entry in capsule.manifest["files"]):
            failures.append("capsule included forbidden .env")
        for entry in capsule.manifest["files"]:
            materialized = capsule.root / str(entry["capsule_path"])
            if not materialized.exists():
                failures.append(f"capsule missing materialized file: {entry['path']}")
        capsule.destroy()
    except Exception as error:
        failures.append(f"capsule self-test failed: {error}")
    for path in (repo_root / ".lab/schema").glob("*.json"):
        try:
            json.loads(path.read_text(encoding="utf-8"))
        except Exception as error:
            failures.append(f"invalid schema {path.name}: {error}")
    if not (repo_root / "tests").is_dir():
        failures.append("tests are not discoverable")
    return failures
