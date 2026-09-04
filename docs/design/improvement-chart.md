# Improvement chart

This is the presentation-readiness map, not a promise disguised as a scorecard. **Shipped** means a
change has local evidence. **Human check** means software work is complete but the result needs eyes
or authority. **Next** means deliberately unclaimed work.

| Priority | Surface | Friction found | Improvement | Proof or next evidence | State |
|---|---|---|---|---|---|
| P0 | Product identity | The repository looked like a game, a research paper, and a harness at once. | One promise, one mark, and one public product; unrelated prototype history stays outside Git. | Staged release contents, package contents, Docker context, and context-policy tests. | Shipped |
| P0 | Logbook | Poster-like raw ANSI screens demanded too much terminal literacy. | Component TUI with a stable story rail, one readable case, focused dialogs, mouse/focus support, and a small key vocabulary. | Headless interaction test plus presentation-laptop review. | Human check |
| P0 | Reliability | Rich text left a Python executor alive after the interface closed. | Synchronous Rich rendering; repaint only when content changes. | Start, open live analysis, exit, and assert no worker remains. | Shipped |
| P0 | Realtime evidence | The evidence view was a static moment even though the interface called it live. | Live Analysis now follows ledger and artifact changes every second and keeps sources attached. | TUI test mutates evidence while the reader is open. | Shipped |
| P0 | Keyboard control | Numeric role keys were registered after Textual compiled bindings, and polling stole story selection. | Bind `1`–`8` at class creation; make arrow/j/k cursor movement authoritative across refreshes. | Headless tests inspect roles, type digits in a request, and hold selection through refresh. | Shipped |
| P0 | Human gates | Approval buttons neither led to the evidence nor explained a complete keyboard route. | Advance opens a dedicated gate: `e` visits sources, `j`/`k` reads, `y` accepts, and Esc preserves state. | Headless trial review and approval test. | Shipped |
| P0 | Human rejection | “Not yet” preserved authority but gave the Lab no reason or remediation path. | Final `r` requires feedback, seals it, preserves superseded work, and queues the Builder. | Controller, inbox, context-policy, CLI, and keyboard TUI tests. | Shipped |
| P0 | Split-pane reading | `j`/`k` moved stories but the adjacent case text could not receive keyboard focus. | Tab/→ enters a focus-marked case scroller; j/k or arrows read; ← returns to stories. | Headless focus and scroll-position test. | Shipped |
| P0 | Failure visibility | A recorded provider delay could disappear from the status line after navigation or restart. | Reconstruct the active DELAYED diagnostic from the ledger whenever the worker is idle. | Restart test preserves a token-exhaustion reason. | Shipped |
| P0 | Artifact discovery | Role documents were durable but hidden behind a dot-directory and numeric shortcuts. | Add a keyboard-first Case files browser on `e` plus `lab files STORY`, showing READY/WAITING state and exact paths. | TUI open test and CLI path-index test. | Shipped |
| P0 | Visual coherence | The raw tutorial offer and Textual defaults introduced pale boxes that looked unrelated to the Logbook. | Turn the invitation into a color-aware FIRST CAST poster and explicitly skin inputs, toggles, buttons, focus, and footer states in the teal/amber system. | Plain-terminal poster render and stylesheet-loading TUI tests. | Shipped |
| P0 | Portability | `lab init` required an unrelated game-spec filename. | Initialization targets the current directory; later commands discover `.lab/config.yaml`. | Initialize and diagnose a blank non-Python repository. | Shipped |
| P0 | Role quality | Every role received 44 KB of archived game context and inactive GUI source. | Active-only allowlists cover Lab code, tests, docs, CI, and containers. | Context-policy assertions and capsule manifest. | Shipped |
| P0 | First five minutes | Clone instructions contained a fake URL and documentation advertised an unwanted Pages path. | Honest after-clone Docker/uv routes and local-only handbook commands. | Follow README from a clean checkout. | Shipped |
| P1 | Presentation | There was no repeatable story between “what is it?” and evidence. | A six-minute route with beats, commands, fallback, and claims to avoid. | Rehearse once on the presentation device. | Human check |
| P1 | Public contribution | GitHub visitors had no structured issue, PR, conduct, support, or security route. | Minimal community files with evidence prompts and private-security guidance. | GitHub community-profile check after repository creation. | Shipped |
| P1 | Tutorial | The invitation dropped directly into a fast-moving evidence stream. | Add a native orientation that starts nothing until `b`, slow the default pace, and expose pause plus j/k reading controls. | Headless orientation/start/pause test plus human pacing review. | Human check |
| P1 | OpenCode | OpenCode users had no named route and might accidentally give an isolated role repository tools. | Add a first-class text-only profile with all tools denied, a documented provider/model setup, and a separate bundled tool-capable Catfish agent. | Adapter command/environment test; live authenticated run remains a human-machine check. | Human check |
| P1 | Cross-device confidence | Linux CI is evidence for Linux, not every device. | Add macOS and Windows smoke jobs after the first public repository exists. | CI matrix runs on all three operating systems. | Next |
| P1 | Harness setup | Provider availability is visible, but first configuration still assumes CLI familiarity. | Add an in-TUI profile editor and connection test without ever displaying secrets. | Adapter contract tests plus manual local/Ollama check. | Next |
| P2 | Distribution | Editable local installation is useful but not a release channel. | Publish signed versioned releases and a package only after pre-1.0 trial evidence is accepted. | Wheel install in blank repo; release provenance. | Next |
| P2 | Accessibility | Color is restrained but keyboard, low-color, and screen-reader behavior need dedicated review. | Add color-independent states, focus-order tests, and terminal compatibility notes. | Manual accessibility checklist and snapshot matrix. | Next |

## Ordering rule

Protect the P0 loop—**ask → build → attack → judge → accept → remember**—before adding more roles,
panes, providers, or decoration. A new feature earns its place only if it shortens the path, improves
evidence, or makes a boundary more honest.

## Patterns consulted

The front door follows [GitHub's repository best practices](https://docs.github.com/en/repositories/creating-and-managing-repositories/best-practices-for-repositories)
and [README guidance](https://docs.github.com/en/repositories/managing-your-repositorys-settings-and-features/customizing-your-repository/about-readmes): explain purpose, usefulness, setup, help, and contribution expectations near the code. Community files follow
[GitHub's community-profile model](https://docs.github.com/en/communities/setting-up-your-project-for-healthy-contributions/about-community-profiles-for-public-repositories?apiVersion=2022-11-28).
The Logbook adopts Textual's component, focus, layout, and testing patterns from its
[application guide](https://textual.textualize.io/guide/app/) and
[layout guide](https://textual.textualize.io/styles/layout/). Catfish keeps its own evidence model,
terminology, and visual identity.
