# Decision

Decision ID: DEC-001
Story: US-002

## Evidence reviewed

The canonical product specification, the Product role's US-002 story, the
existing deterministic domain/controller tests, and the first Builder refusal.

## Selected direction

- Use route switching for `/browse`, `/chat/:profile_id`, `/bank`, and `/result`.
- Use fictional birthplace and early-pet facts for the deterministic demo fixture.
- Apply Unicode NFKC, case-folding, punctuation removal, and whitespace collapse;
  accept only explicit normalized aliases.
- Limit a demo round to 12 player messages.
- Use the product specification's defensive lesson about combining harmless
  details and avoiding knowledge-based account recovery.
- Retain the existing seeded implementation where it satisfies the story, and
  patch only demonstrable gaps.

## Rejected alternatives

Split-screen and true multi-window presentation are deferred because routes are
the specified reliability-first baseline. Semantic LLM answer matching remains
outside the authoritative win condition.

## Human rationale

The user explicitly instructed the harness to choose the simplest implementation
for non-blocking ambiguity, record it, continue the project, and use Catfish Lab.
These choices directly follow that instruction and the product specification.

## AI recommendations considered

The Product role recommended a seeded fake-provider implementation before live AI.

## Known uncertainty

Visual polish and final wording can change after the deterministic loop is proven.

## Approval

Approved by human: yes
Date: 2026-09-03
