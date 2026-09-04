"""Append-only, integrity-linked JSONL provenance ledger."""

import hashlib
import json
import os
import time
from contextlib import contextmanager
from datetime import UTC, datetime
from pathlib import Path
from uuid import uuid4


class LedgerError(ValueError):
    pass


@contextmanager
def _append_lock(path: Path):
    """Serialize writers with a portable, atomic lock-file creation."""
    lock_path = path.with_name(f"{path.name}.lock")
    deadline = time.monotonic() + 10
    descriptor: int | None = None
    while descriptor is None:
        try:
            descriptor = os.open(lock_path, os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o600)
        except FileExistsError:
            if time.monotonic() >= deadline:
                raise LedgerError(f"timed out waiting for ledger lock: {lock_path.name}") from None
            time.sleep(0.01)
    try:
        os.write(descriptor, str(os.getpid()).encode())
        yield
    finally:
        os.close(descriptor)
        lock_path.unlink(missing_ok=True)


def _canonical(record: dict[str, object]) -> bytes:
    payload = {key: value for key, value in record.items() if key != "record_hash"}
    return json.dumps(payload, sort_keys=True, ensure_ascii=False, separators=(",", ":")).encode()


def record_hash(record: dict[str, object]) -> str:
    """Return the stable digest for a record, including its previous-hash pointer."""
    return hashlib.sha256(_canonical(record)).hexdigest()


def append_record(path: Path, record: dict[str, object]) -> None:
    """Append one durable event and link it to the preceding line.

    Older unlinked ledgers remain appendable: the first linked event anchors itself
    to the canonical digest of the last legacy record.
    """
    path.parent.mkdir(parents=True, exist_ok=True)
    with _append_lock(path):
        existing = read_records(path)
        previous = existing[-1] if existing else None
        previous_hash = (
            str(previous.get("record_hash") or record_hash(previous))
            if previous is not None
            else None
        )
        enriched = dict(record)
        enriched.setdefault("event_id", f"evt_{uuid4().hex}")
        enriched.setdefault("recorded_at", datetime.now(UTC).isoformat())
        enriched["sequence"] = len(existing) + 1
        enriched["previous_hash"] = previous_hash
        enriched["record_hash"] = record_hash(enriched)
        encoded = json.dumps(enriched, sort_keys=True, ensure_ascii=False)
        with path.open("a", encoding="utf-8") as stream:
            stream.write(encoded + "\n")
            stream.flush()
            os.fsync(stream.fileno())


def read_records(path: Path) -> list[dict[str, object]]:
    if not path.exists():
        return []
    records = []
    for number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
        try:
            value = json.loads(line)
        except json.JSONDecodeError as error:
            raise LedgerError(f"invalid ledger line {number}: {error}") from error
        if not isinstance(value, dict):
            raise LedgerError(f"ledger line {number} is not an object")
        records.append(value)
    return records


def verify_ledger(path: Path) -> list[str]:
    """Return integrity failures without rejecting historical unlinked records."""
    records = read_records(path)
    failures: list[str] = []
    chain_started = False
    prior: dict[str, object] | None = None
    for number, record in enumerate(records, 1):
        linked = "record_hash" in record
        if chain_started and not linked:
            failures.append(f"line {number}: unlinked record after integrity chain began")
        if linked:
            chain_started = True
            expected_previous = (
                str(prior.get("record_hash") or record_hash(prior)) if prior is not None else None
            )
            if record.get("previous_hash") != expected_previous:
                failures.append(f"line {number}: previous hash mismatch")
            if record.get("record_hash") != record_hash(record):
                failures.append(f"line {number}: record hash mismatch")
            if record.get("sequence") != number:
                failures.append(f"line {number}: sequence mismatch")
        prior = record
    return failures
