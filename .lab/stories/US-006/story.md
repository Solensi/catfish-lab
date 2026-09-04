# User Story

## Statement

As a first-time Catfish user,
I want the Logbook to feel recognizable without making me decode its interface,
So that I understand the situation and next action at a glance.

## User value

Catfish gains a memorable identity while remaining calm, approachable, and useful on narrow or
unfamiliar terminals.

## Acceptance criteria

- [x] Every Logbook screen uses one restrained Catfish identity line and one plain-language subtitle.
- [x] Decorative frames and repeated motifs do not compete with work status or navigation.
- [x] LIGHT stories collapse skipped research roles without hiding their names or inspection keys.
- [x] The primary next step is human language rather than an internal CLI command.
- [x] The first startup offers the tutorial rather than launching it automatically.
- [x] Space toggles a visible `[✓] Don’t show this invitation again` preference.
- [x] Starting or skipping without the checkmark leaves the invitation available next time.
- [x] `lab tutorial` remains rerunnable and never changes the startup preference.
- [x] The tutorial uses the memorable “First Cast” and “Too-Confident Machine” case.
- [ ] Lab tests, lint, doctor, and documentation build pass.

## Out of scope

A graphical logo, animation, mouse navigation, or replacement TUI framework.

## Unknowns

Terminal glyph rendering varies. The interface must remain understandable if the fish mark renders
imperfectly because meaning never depends on the mark.

## AI experiment required?

no

## Notes

“Posterized” means a strong hierarchy and recurring identity, not maximal decoration.
