# Persona reduction review

This review was performed by using the real CLI and Logbook on the request that became `US-005`.
It is a design record, not market research.

## Mara — capable solo developer

> “I already asked for the change. Why am I approving that same scope before anything happens?”

Observed friction: LIGHT submission led from Product framing to a second implementation gate.
Resolution: submitting a bounded LIGHT request now records implementation authority. FULL retains
its evidence-backed implementation gate because its design emerges later.

## Ivo — skeptical maintainer

> “The screen says one of twelve artifacts, but seven are marked skipped. Is progress broken?”

Observed friction: progress used the full workflow denominator for every story. Resolution: LIGHT
tracks five required role artifacts; FULL tracks all twelve. Skipped roles remain visible and
inspectable so absence is not confused with forgotten work.

## Noor — first-time user

> “What is this, and which of these eighteen commands gets my work done?”

Observed friction: the README explained implementation concepts before value, while `lab --help`
presented every control at once. Resolution: documentation now starts with the user promise, a
single Logbook launch, two depths, and explicit “use it / do not use it” guidance. The complete CLI
remains available as reference rather than onboarding.

## Shared failure — false comfort

> “The Builder wrote an implementation report, so why did none of my files change?”

Observed friction: the TUI treated Builder like a text-only model role even though construction
requires repository tools. Resolution: Builder is now an explicit HANDOFF to the surrounding coding
harness. The Logbook says what it is waiting for, the JSON inbox exposes the exact action, and
provider failures remain DELAYED evidence.

## Design influences

- [MkDocs](https://github.com/mkdocs/mkdocs) keeps source material as ordinary Markdown and provides
  a one-command local development server. Catfish follows that model with `lab docs`.
- [Material for MkDocs](https://github.com/squidfunk/mkdocs-material) demonstrates progressive
  navigation, search, readable code, and a polished dark/light documentation surface.
- [uv](https://github.com/astral-sh/uv) separates immediate installation from task-oriented guides;
  Catfish now separates the five-minute path from operator and architecture reference.
- [Gum](https://github.com/charmbracelet/gum) favors a small vocabulary of attractive terminal
  interactions. The Logbook keeps its memorable cast but reduces the common action to `n`, Enter,
  and `a`.
- [Textual](https://github.com/Textualize/textual) treats terminal interfaces as testable component
  systems. Catfish now uses a component TUI for focus, modals, scrolling, mouse input, and a stable
  footer while retaining plain snapshot output for automation.

These are interface and documentation patterns, not claims of architectural equivalence.
