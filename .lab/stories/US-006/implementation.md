# Implementation

## Approved scope

Give Catfish Lab a memorable but restrained identity, simplify the information hierarchy, and make
the first-start tutorial a genuine opt-in with a persistent “Don’t show again” checkbox.

## Files changed

- `lab/logbook.py` — quiet Catfish identity line, sentence-case screens, collapsed LIGHT roles,
  relevant approvals only, and human-readable next actions.
- `lab/tutorial.py` — First Cast invitation, keyboard-controlled checkbox, saved dismissal preference,
  and revised Too-Confident Machine tutorial framing.
- `lab/cli.py` — offers the tutorial before the Logbook without forcing it; explicit tutorial runs do
  not alter the startup preference.
- `tests/test_lab_logbook.py` and `tests/test_lab_tutorial.py` — identity, hierarchy, prompt, checkbox,
  persistence, and workflow regressions.
- `README.md`, `docs/README.md`, `docs/lab/quickstart.md`, `docs/lab/logbook.md`, and
  `docs/lab/cli-reference.md` — behavior and identity documentation.
- `.gitignore`, `pyproject.toml`, and `uv.lock` — preference marker and version 0.5.0.

## Patch

The initial heavy poster treatment was rejected during the human review because it made decoration
compete with the application. The final system uses one `≋<°)))><` mark, one title, one orienting
sentence, and one divider. Story state and the next action remain dominant.

LIGHT stories show the five participating roles plus one line naming the Scientist, Architect, and
blind Heretic as full-only. Internal artifact paths are available in role detail rather than placed
in the main decision surface.

On first startup, Enter begins the disposable First Cast, `s` or Escape skips it, and Space toggles
`[✓] Don’t show this invitation again`. The saved preference affects only the invitation;
`lab tutorial` always works.

## Tests

- Ruff passed.
- 55 Lab tests passed.
- `lab doctor` passed.
- Strict MkDocs build passed.

## Remaining uncertainty

The fish glyph may vary across terminal fonts, but no navigation or meaning depends on it. Visual
inspection on the user's own terminal remains the decisive usability check.
