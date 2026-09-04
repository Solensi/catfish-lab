# Logbook Readability and Evidence Redesign

## User observation

The original narrative was difficult to scan and only announced that roles had produced files. It
did not communicate what a reviewing role reported or how that report flowed into evidence.

## Implemented behavior

- The original Story, Lab, Logbook, role, approval, and artifact terminology remains intact.
- Each visible role card has `REPORTED` and `SOURCE` fields with width-aware wrapping.
- Role-specific Markdown sections determine the reported summary: for example, the Red Team uses
  `Confirmed defects` before `Suspected defects` or `Design concerns`.
- A reopening connects the preserved Red Team report to the controller's remediation response.
- New role-run ledger events record `output_sha256`; new preserved reviews record
  `artifact_sha256`.
- A current artifact is quoted only when its recorded digest matches. Historical runs whose output
  path was overwritten before hashing are omitted from the evidence-bearing stream.
- Interactive terminals receive restrained ANSI styling; snapshots remain plain text for harnesses.

## Verification

- The full suite passed 52 tests after the first redesign.
- Focused Logbook tests passed after the legacy-event filtering refinement.
- Ruff reported no lint violations.
- A snapshot of US-002 showed seven preserved evidence-bearing entries, including the Red Team
  finding, controller response, source path, and integrity status for each reopening.

## Remaining uncertainty

Existing preserved review files predate per-artifact seals. They display their current digest and
are explicitly labelled `LEGACY / UNSEALED`; future preserved reviews can display `MATCH`.
