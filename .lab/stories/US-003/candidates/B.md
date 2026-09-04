# Candidate Proposal

## Summary

**Observation:** The current design stores role output at mutable story paths, then uses recorded hashes to decide whether those paths still represent the original run.

**Assumption attacked:** Durable, truthful history can be built by attaching hashes to mutable artifact paths and suppressing narration when their current content no longer matches.

**Alternative:** Make every completed role output an immutable, content-addressed evidence object. Treat familiar files such as `candidates/B.md` or `redteam.md` only as current-stage working views. Ledger events reference immutable object hashes, and the Logbook renders historical reports from those objects rather than reopening mutable paths.

## Core idea

On every successful role run:

1. Validate the returned artifact.
2. Compute its SHA-256 digest.
3. Store the exact bytes once under a content-addressed path such as:

   `.lab/objects/sha256/<digest>`

4. Write or replace the story’s conventional artifact path as the current working view.
5. Append a ledger event containing the object digest, logical artifact name, and current-view path.
6. Build Logbook history from the immutable object referenced by the event.

**Inference:** This separates two concepts currently conflated by a story path:

- the latest editable artifact for workflow convenience;
- the historical artifact produced by a particular run.

A reopening can therefore replace `redteam.md` without erasing or ambiguously relabeling the earlier review.

## Assumptions

- **Observation:** SHA-256 is already the selected integrity primitive.
- **Observation:** New role outputs already receive content hashes.
- **Observation:** Overwritten legacy paths must not be presented as historical conclusions.
- **Inference:** Lab artifacts are small enough that retaining immutable copies is cheaper and simpler than reconstructing history from mutable files.
- **Recommendation:** Preserve legacy records without rewriting them. Only new events should require an object reference.
- **Uncertainty:** The supplied evidence does not establish expected long-term object-store size or whether repository users want all stored objects committed to version control.

## Architecture / behavior

Introduce an object-store boundary with a narrow API:

```python
def store_artifact(repo_root: Path, content: bytes) -> ArtifactObject:
    ...

def load_artifact(repo_root: Path, digest: str) -> bytes:
    ...

def verify_artifact(repo_root: Path, digest: str) -> bool:
    ...
```

`ArtifactObject` contains the SHA-256 digest, byte count, and repository-relative object path.

A new successful role event records:

```json
{
  "output_artifact": ".lab/stories/US-003/candidates/B.md",
  "output_sha256": "sha256:...",
  "output_object": ".lab/objects/sha256/...",
  "object_bytes": 1234
}
```

The object writer uses exclusive creation. If the digest already exists, it verifies that the existing bytes match instead of overwriting them.

The Logbook applies these rules:

- A new event with a valid object displays the report from that immutable object.
- A changed working path is labelled as a changed current view but does not invalidate the historical report.
- A missing or hash-mismatched object produces an integrity warning and no quoted summary.
- A legacy event without an object remains `LEGACY / UNSEALED`; its mutable path is never promoted to historical evidence.
- READY or WAITING continues to reflect current workflow files, not historical object availability.

`lab doctor` verifies both chains:

- ledger linkage and record hashes;
- every referenced object’s existence, filename/digest agreement, and content digest.

Evidence indexes cite the immutable object and may additionally cite the current working path when it matches.

## Expected advantages

- **Inference:** Historical narration remains available after legitimate workflow overwrites instead of being discarded merely because a path changed.
- **Inference:** Integrity verification becomes local and direct: an event names the exact bytes it claims existed.
- **Inference:** Reopening no longer needs timestamp-based preservation copies as a separate historical mechanism.
- **Inference:** Multiple runs producing identical bytes deduplicate automatically.
- **Inference:** Snapshot stability improves because historical reports do not depend on mutable path contents.
- **Recommendation:** Keep the ledger chain for ordering and event integrity; use the object store for artifact identity rather than attempting to make the ledger carry full Markdown content.

## Failure modes

- Objects could be deleted while ledger events remain, making history incomplete.
- Corrupt objects could be detected but not recovered without another repository copy.
- Committing every object may increase repository size over time.
- Sensitive content accidentally accepted as a role artifact would become deliberately durable.
- Two persistence mechanisms—working views and immutable objects—could confuse operators unless documentation names their distinct authority.
- A partial write between object creation, working-view update, and ledger append could leave an unreferenced object or a current view without a recorded event.
- Legacy evidence remains uncertain because immutable objects cannot retroactively prove what old mutable paths contained.

## Cost / complexity

The design adds an object-store module, atomic write handling, doctor checks, event fields, and Logbook lookup logic. It can remove or simplify timestamped preservation behavior for new artifacts.

**Inference:** The implementation cost is moderate, but the conceptual model is simpler than maintaining historical truth through mutable paths plus several special cases.

**Recommendation:** Do not add a database, garbage collector, or compression initially. Unreferenced objects are harmless and can be reported by `lab doctor` without automatic deletion.

## Testability

Smallest experiment capable of testing the alternative:

1. Before inspection, define success as:
   - two role runs at the same logical path remain independently readable;
   - changing the working path does not change either historical report;
   - changing one byte in an object causes `lab doctor` to fail;
   - changing one byte in a ledger event causes `lab doctor` to fail;
   - repeated snapshots are byte-identical when state is unchanged;
   - legacy unsealed records are not quoted as historical conclusions.
2. In a disposable story, write artifact content `v1` and record its object.
3. Replace the same working path with `v2` through a second recorded run.
4. Render the Logbook twice and verify that it cites both immutable objects with matching hashes.
5. Modify only the current working file and verify that historical summaries remain unchanged while the current view is marked changed.
6. Modify one object byte and verify a nonzero `lab doctor` result naming the affected digest.
7. Restore the object, modify a ledger event, and verify ledger tampering is independently detected.
8. Run the existing tests and lint gate.

This directly compares the alternative with path-and-hash narration under the overwrite condition that matters most.

## What would falsify this proposal?

The proposal is falsified if immutable objects do not preserve independently verifiable historical reports across working-path overwrites, if object tampering is not detected, or if snapshots become unstable without state changes.

It should also be rejected if deterministic measurement shows that the added object lifecycle creates more unrecoverable partial states than the current preservation mechanism, or if repository growth exceeds an explicitly agreed operational limit under representative role-run volume.

**Uncertainty:** Cross-platform atomic-write behavior, especially on Windows, remains unobserved and requires a separate platform run.
