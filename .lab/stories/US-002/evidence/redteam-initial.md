# Initial Red Team findings

Run provenance is stored in `.lab/ledger.jsonl` and `.lab/runs/`.

## Confirmed defects

1. `GameController.begin_recovery()` and `submit_recovery()` allowed domain
   `InvalidTransitionError` exceptions to bypass the UI's `GameControllerError`
   boundary.
2. The Bank guard and explicit result label had no direct presentation tests.

## Suspected defects

1. A synchronous lambda returned the coroutine for opening a profile; pinned
   Flet callback behavior had not been demonstrated.
2. The configured portrait asset did not exist and was not rendered.

## Design concerns

1. The debrief claimed disclosure behavior even when no chat occurred.
2. `RoundDebrief` allowed inconsistent success and match-count values.
3. The Python UI/controller boundary remains an in-process type boundary rather
   than a security sandbox, which is consistent with the product architecture
   but deserves continued tests.

The transition, presentation, callback, and debrief-consistency issues were
remediated. Portrait selection/rendering remains explicitly deferred to its own
asset/licensing story.
