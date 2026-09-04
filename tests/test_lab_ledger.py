import json
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

from lab.ledger import append_record, read_records, verify_ledger


def test_ledger_appends_exactly_one_json_object(tmp_path: Path) -> None:
    path = tmp_path / "ledger.jsonl"
    append_record(path, {"run_id": "one", "status": "success"})
    records = read_records(path)
    assert len(records) == 1
    assert records[0]["run_id"] == "one"
    assert records[0]["sequence"] == 1
    assert records[0]["previous_hash"] is None
    assert verify_ledger(path) == []


def test_ledger_detects_tampering(tmp_path: Path) -> None:
    path = tmp_path / "ledger.jsonl"
    append_record(path, {"event": "first"})
    append_record(path, {"event": "second"})
    records = read_records(path)
    records[0]["event"] = "rewritten"
    path.write_text("\n".join(json.dumps(record) for record in records) + "\n")

    failures = verify_ledger(path)

    assert "line 1: record hash mismatch" in failures


def test_new_chain_can_anchor_to_legacy_record(tmp_path: Path) -> None:
    path = tmp_path / "ledger.jsonl"
    path.write_text('{"status":"historical"}\n')
    append_record(path, {"event": "linked"})
    assert verify_ledger(path) == []


def test_concurrent_writers_form_one_chain(tmp_path: Path) -> None:
    path = tmp_path / "ledger.jsonl"
    with ThreadPoolExecutor(max_workers=8) as pool:
        list(pool.map(lambda number: append_record(path, {"number": number}), range(20)))

    records = read_records(path)
    assert len(records) == 20
    assert [record["sequence"] for record in records] == list(range(1, 21))
    assert verify_ledger(path) == []
