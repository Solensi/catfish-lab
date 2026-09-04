# Red Team Report

## Confirmed defects

None remain in the exercised interaction path.

The first poster treatment was a confirmed usability failure: nested borders, uppercase labels,
repeated slogans, redundant rules, machine commands, and irrelevant LIGHT approvals competed for
attention. Human feedback rejected it before release. The final render removes those elements.

## Suspected defects

- Some terminal fonts may render the fish mark imperfectly. No control or meaning depends on it.
- A user who checks “Don’t show again” must use `lab tutorial` for future tours; there is deliberately
  no separate preference-management screen for one boolean.

## Missing tests

- Visual inspection in the user's own terminal dimensions and font.
- Keyboard exercise on a native Windows console.

## Design concerns

Identity can easily grow back into clutter. Future screens should preserve the rule: one mark, one
title, one orientation sentence, one divider.

## Areas tested without finding a defect

- Start, skip, checked and unchecked invitation outcomes.
- Explicit tutorial runs leaving startup preference unchanged.
- LIGHT role collapse without losing role names or keys.
- Human-language next actions and relevant approval display.
- Lint, 55 Lab tests, Lab doctor, and strict documentation build.
