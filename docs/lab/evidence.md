# Evidence and Integrity

The Lab distinguishes four statement types:

- **Observed evidence:** a file, deterministic result, test output, or recorded event.
- **Inference:** an interpretation that was not directly measured.
- **Recommendation:** a proposed action.
- **Uncertainty:** a question the available evidence cannot answer.

The Logbook says `REPORTED` because it shows what an artifact states; it does not silently promote
that statement to truth.

## Trust hierarchy

1. Reproducible external observation or deterministic test.
2. Content-addressed artifact preserved in story evidence.
3. Integrity-linked ledger and run metadata.
4. Current unsealed artifact.
5. Derived Logbook summary or Archivist narrative.

Lower items aid discovery but cannot contradict stronger evidence.

## Ledger chain

Each new line contains `sequence`, `previous_hash`, and `record_hash`. The hash covers the canonical
event and previous pointer. Writes use a portable exclusive lock, flush, and filesystem sync.
`lab doctor` reports mutation, reordering, or an unlinked record inserted after chaining began.

Historical entries remain readable. The first chained event anchors to the last legacy line's
canonical digest; migration never rewrites history.

## Artifact seals

New role runs record `output_sha256`; new reopenings record `artifact_sha256`. The Logbook quotes a
current role artifact only when its digest matches. An old run pointing to an overwritten path is
omitted from evidence-bearing reports. Preserved legacy reviews remain visible but are explicitly
labelled `LEGACY / UNSEALED` with their current digest.

## Evidence indexes

`lab index-evidence US-NNN` writes `evidence/EVIDENCE.md` for people and
`evidence/evidence-index.json` for harnesses. They include story state, matching ledger events,
artifact sizes and hashes, generation time, and ledger status. The index is a map, not new evidence.

## Secret handling

Context policies deny `.env`, secret-like, credential-like, and Git paths. Full prompts are not
saved. Prompt and visible-file hashes support reproducibility without publishing private text.
