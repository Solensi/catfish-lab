# Implementation

## Approved scope

Implement DEC-001’s deterministic demo round while retaining the existing seeded implementation and patching only demonstrable gaps.

- **Observation:** The supplied implementation already provides seeded profiles, canned chat, deterministic normalization and validation, public/private separation, route switching, a 12-message default, and the approved defensive lesson.
- **Observation:** The Bank route can render without the controller being in recovery phase, and the result view does not explicitly label success or failure.
- **Inference:** Guarding the Bank view and displaying the authoritative outcome closes these presentation/state gaps without changing the approved design.

## Files changed

- `catfish/ui/router.py`
- `tests/test_game_controller.py`

## Patch

```diff
diff --git a/catfish/ui/router.py b/catfish/ui/router.py
--- a/catfish/ui/router.py
+++ b/catfish/ui/router.py
@@ -3,6 +3,7 @@
 import flet as ft
 
 from catfish.domain.models import PublicProfile, RoundDebrief
+from catfish.domain.state import RoundPhase
 from catfish.observability import event
 from catfish.services.game_controller import GameController, GameControllerError
 
@@ -111,6 +112,14 @@ def create_app(page: ft.Page, controller: GameController):
 
     @ft.component
     def BankView():
+        if controller.phase is not RoundPhase.RECOVERY:
+            return ft.Column(
+                controls=[
+                    ft.Text("No recovery attempt is active."),
+                    ft.Button("Browse", on_click=lambda _: page.navigate("/browse")),
+                ]
+            )
+
         birthplace = ft.TextField(label="Fictional birthplace response")
         first_pet = ft.TextField(label="Fictional early-pet response")
         error, set_error = ft.use_state("")
@@ -170,6 +179,11 @@ def create_app(page: ft.Page, controller: GameController):
         return ft.Column(
             controls=[
                 ft.Text("ROUND COMPLETE", size=34, weight=ft.FontWeight.BOLD),
+                ft.Text(
+                    "RECOVERY SUCCEEDED" if result.succeeded else "RECOVERY FAILED",
+                    size=22,
+                    weight=ft.FontWeight.BOLD,
+                    color="#277A4B" if result.succeeded else "#B42318",
+                ),
                 ft.Text(f"Privacy style: {result.resistance_style.value}"),
                 ft.Text(
                     f"Recovery facts correctly inferred: "
diff --git a/tests/test_game_controller.py b/tests/test_game_controller.py
--- a/tests/test_game_controller.py
+++ b/tests/test_game_controller.py
@@ -23,6 +23,24 @@ async def test_complete_demo_round_without_api_key() -> None:
     assert controller.phase is RoundPhase.RESULT
 
 
+@pytest.mark.asyncio
+@pytest.mark.parametrize(
+    ("birthplace", "first_pet"),
+    [
+        ("Rotterdam", "Rex"),
+        ("Middelburg", "Spot"),
+        ("Rotterdam", "Spot"),
+    ],
+)
+async def test_any_incorrect_recovery_answer_prevents_success(
+    birthplace: str, first_pet: str
+) -> None:
+    controller = GameController(DemoProvider())
+    (profile,) = await controller.browse()
+    await controller.open_profile(profile.id)
+    controller.begin_recovery()
+    result = controller.submit_recovery(birthplace=birthplace, first_pet=first_pet)
+    assert not result.succeeded
+
+
 @pytest.mark.asyncio
 async def test_message_limit_is_bounded() -> None:
     controller = GameController(DemoProvider(), max_messages=1)
```

## Tests

Defined success criteria before validation:

- Navigating to the Bank surface without an active recovery phase must not expose the recovery form.
- A result must explicitly communicate whether recovery succeeded or failed.
- If either submitted fact is incorrect, `RoundDebrief.succeeded` must be false.

Recommended controller validation:

```bash
uv run ruff check .
uv run ruff format --check .
uv run pytest
```

No tests were run in this text-only Builder role.

## Remaining uncertainty

- **Uncertainty:** Flet rendering and route behavior require validation against the repository’s pinned Flet version.
- **Recommendation:** A distinct reviewer should run the quality gate and manually complete both a successful and failed demo round before DONE is approved.
