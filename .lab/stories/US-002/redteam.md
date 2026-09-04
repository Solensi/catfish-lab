# Red Team Report

## Confirmed defects

- **Observation:** `ResultView.next_round()` calls `controller.next_round()` without catching `GameControllerError`. The first invocation changes the controller from `RESULT` to `BROWSING`; a repeated invocation then raises `GameControllerError("the current round has not produced a result")`.
- **Inference:** A rapid double click or overlapping delivery of the “Next profile” event can escape the UI error boundary and interrupt the interaction.
- **Recommendation:** Catch `GameControllerError` in the result handler or make completion navigation idempotent. Add a presentation-level test that invokes the handler twice.

## Suspected defects

- **Observation:** The application permits recovery immediately after opening a profile, before any chat message has occurred. The result nevertheless labels matched submitted answers as “Recovery facts correctly inferred.”
- **Inference:** A player can receive a successful “inferred” result without participating in the awareness exercise’s conversation mechanic.
- **Uncertainty:** The acceptance criteria require that chat can start, but do not explicitly require at least one message before recovery.
- **Recommendation:** Either require a completed chat turn before beginning recovery or change the result wording to describe facts “submitted correctly.”

- **Observation:** Supplied runtime evidence demonstrates server startup and HTTP 200, while visual browser automation remains explicitly untested.
- **Uncertainty:** It has not been demonstrated that rendered controls, callbacks, route transitions, form entry, and portrait loading support a complete round in the pinned Flet client.
- **Recommendation:** Record one successful and one failed round through a real browser or Flet client.

## Missing tests

- A repeated or overlapping “Next profile” event test proving the result handler cannot leak a controller exception.
- A pinned-runtime browser test covering browse → open profile → chat → bank → successful result → next profile.
- The same browser flow with an incorrect answer and visible `RECOVERY FAILED`.
- A browser assertion that the seeded portrait is served and rendered.
- A policy test defining whether recovery before any conversation is intentionally allowed.
- A UI-boundary inspection proving rendered controls, callback payloads, and serialized public values contain no private recovery data.

## Design concerns

- **Observation:** UI handlers apply the controller error boundary inconsistently: profile, chat, recovery-start, and recovery-submit handlers catch `GameControllerError`, while the result transition handler does not.
- **Inference:** Future handlers may similarly expose otherwise safely translated controller errors.
- **Recommendation:** Apply a common UI action wrapper or require an exception-contract test for every controller-backed callback.

- **Observation:** Route state, closure-local runtime state, and controller state remain separately maintained.
- **Inference:** Correct presentation continues to depend on synchronization among three state stores, particularly during repeated or overlapping callbacks.
- **Recommendation:** Derive presentation state from the controller where practical and make navigation callbacks idempotent.

## Areas tested without finding a defect

- **Observation:** Pending profile opens cannot reactivate a round after it is abandoned.
- **Observation:** Concurrent chat operations are serialized and cannot exceed the configured message limit.
- **Observation:** Pending chat replies are rejected after recovery begins or the round changes.
- **Observation:** Recovery validation is deterministic and requires both accepted answers.
- **Observation:** Public and private persona models are distinct, and `PublicProfile` rejects recovery data.
- **Observation:** Provider failures and domain transition failures are translated to `GameControllerError`.
- **Observation:** Invalid chat-route identities and invalid Bank phases are guarded.
- **Observation:** Result labels explicitly distinguish successful and failed recovery.
- **Observation:** Supplied evidence reports linting, formatting, Lab doctor, 44 tests, portrait integrity, and API-key-free runtime startup passing.
