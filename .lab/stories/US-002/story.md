# User Story

## Statement

As an awareness tester  
I want to complete one fictional social-engineering round without live AI access  
So that I can experience how casually shared information can become sensitive in account recovery.

## User value

Provides a reliable, understandable demonstration of the project’s core defensive lesson, including when profile-generation services are unavailable.

## Acceptance criteria

- [ ] The player can open a synthetic profile and start a chat.
- [ ] Demo mode uses a seeded profile and deterministic canned replies without requiring profile-generation API access.
- [ ] The player can move from chat to the fictional Bank of Earth recovery surface.
- [ ] Recovery requires two fictional facts associated with the active persona.
- [ ] Submitted answers are normalized and validated deterministically against explicit accepted variants.
- [ ] Both accepted answers produce a successful round result; any incorrect answer prevents success.
- [ ] The profile used for validation remains the same profile opened for the round.
- [ ] Public profile data sent to the UI contains no recovery answers or private persona record.
- [ ] The result shows how many facts were inferred and presents a defensive lesson about oversharing and knowledge-based recovery.
- [ ] The entire round can be completed without developer tools or a live AI call.
- [ ] Automated tests demonstrate the validation, profile-boundary, and active-profile invariants.

## Out of scope

- Live profile generation or live persona chat.
- Multiple profiles and background buffering.
- Scoring, animations, persistence, or true multi-window behavior.
- Teaching or rewarding real-world manipulation techniques.
- Real people, credentials, services, or recovery data.

## Unknowns

- Which two fictional recovery-fact categories will be used.
- The accepted normalization rules and aliases for each category.
- Whether the primary demo uses route switching or a split-screen layout.
- The maximum number of chat messages allowed per round.
- The exact defensive debrief copy.

## AI experiment required?

no

## Notes

- **Observation:** The product specification makes deterministic demo mode, public/private data separation, deterministic recovery validation, and a defensive debrief P0 requirements.
- **Inference:** A seeded end-to-end round is the smallest scope that demonstrates the core product value without making live AI availability part of the critical path.
- **Recommendation:** Implement this story with a fake provider before adding live AI behavior.
- **Uncertainty:** Final recovery categories, normalization policy, and presentation layout require human decisions.
