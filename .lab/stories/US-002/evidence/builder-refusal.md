# Builder refusal evidence

The first Builder run correctly declined to produce code because the selected
product decisions had not been materialized in an approved decision artifact.
It reported no changed files, no patch, and no tests. This output exposed that
the controller accepted a no-op Builder response as a successful implementation.

Run: `run_20260903T085717_219ef461` (see `.lab/ledger.jsonl` and matching run record)

The controller now rejects a Builder response that explicitly contains no patch
or no changed files. The story was reopened so a fresh Builder can run after the
decision artifact exists.
