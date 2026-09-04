# User Story

## Statement

As an awareness-game player
I want to complete one deterministic round using a synthetic persona
So that I can experience how casual disclosures become recovery risks without
requiring live AI access.

## User value

The complete defensive lesson is demonstrable offline before probabilistic AI
or UI polish enters the critical path.

## Acceptance criteria

- [ ] One demo profile can move through browsing, chat, recovery, and result.
- [ ] The UI-facing public profile type cannot contain recovery answers.
- [ ] A deterministic fake provider supplies the profile and bounded canned replies.
- [ ] Recovery success uses normalized explicit accepted answers, never an LLM.
- [ ] Recovery always validates against the profile opened for the round.
- [ ] A defensive debrief reports matched fact count without exposing raw answers.
- [ ] The full loop is covered by tests and works without an API key.

## Out of scope

Flet presentation, live model calls, portrait licensing, buffering, scoring, and
prompt evaluation.

## Unknowns

None that block this deterministic slice.

## AI experiment required?

no

## Notes

This is a light-depth story. The domain primitives were created during the Lab
bootstrap; this story owns the next controller/fake-provider application slice.
