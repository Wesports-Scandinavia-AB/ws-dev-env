# Save and resume a review run

Start a saved run only after the user selects repositories, mode and PR restrictions:

```text
python <helper> run-start --repo owner/repo --repo owner/other --mode fix
python <helper> run-start --repo owner/repo --mode comments --only owner/repo#123 --start owner/repo#123
python <helper> run-show --run latest
python <helper> run-show --run <run-id>
```

Keep the returned run id across compaction and resume. It identifies saved choices
and the fix budget, not claim ownership. Each execution gets a fresh claim session.

On "continue where we left off", choose the run referenced in context. Use latest
only if unambiguous; ask if several could match. Recap projects, mode, outcomes and
waiting items. Restore answered choices, including fix-and-merge, without expanding
scope or resetting counters. Explain missing saved context and ask for missing choices.
A completed run can be continued when the user requests it, retaining its budget.

Run preflight and fetch fresh PRs, head/base pairs, events, reviews, CI, deployments
and claims. Saved state is not proof of present status. Reconcile work interrupted
between push, merge and receipt writes against GitHub before acting. Never push or
merge a PR already merged during the interruption.

Do not adopt an old session's claim. Leave active old claims alone until released or
expired. Inspect retained worktrees and preserve valuable work; prefer a fresh worktree
and transfer confirmed unpublished work only after ownership and version checks.

```text
python <helper> record --run <run-id> --repo owner/repo --pr 123 --input <receipt.json>
python <helper> fix-round --run <run-id> --repo owner/repo --pr 123
python <helper> run-status --run <run-id> --status waiting
python <helper> run-status --run <run-id> --status active
python <helper> run-configure --run <run-id> --mode comments
```

Record every completed/waiting PR. Reserve each fix round before editing. At most
three exclusive reservations exist per PR per run. Commits, base movement and resume
use the same budget. A crash may conservatively consume a round. Never erase counters
or silently start another run to evade exhaustion.

For an explicit mode/scope change use `run-configure`, preserving run id, progress
and rounds. Repeated `--repo` replaces repository selection, repeated `--only` replaces
the named PR restriction, and `--all-prs` clears it when the user asks for all PRs.
Do not infer permission to add repos or change comments mode into fix mode.

A waiting receipt requires `head`, `base`, `result: waiting`, and a `waiting` object:

```json
{
  "kind": "decision",
  "reason": "Manager visibility is not specified",
  "owner": "PR author; decision owner not yet identified",
  "question": "Should managers see their team or the whole company?",
  "nextStep": "Obtain the visibility decision, then verify affected roles"
}
```

For CI/access/another-session waits, question may be null and nextStep names the
event enabling progress. Name a real owner when known, otherwise say unknown.
Do not invent one or automatically message people. Surface questions to the current
user and in the authorized review. Store no secrets or sealed deal content.

Mark paused only at the user's request, waiting for unresolved items, or complete
when all work is handled. After the user asks to resume, mark active. Do not schedule
future runs automatically or restore a mode the user explicitly changed away from.
