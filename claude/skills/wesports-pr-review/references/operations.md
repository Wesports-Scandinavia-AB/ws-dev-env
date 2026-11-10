# Portable operations

Requires Python 3.10+, Git and GitHub CLI on PATH. No external Python packages, specific
shell, personal scripts or particular agent vendor are required. Use `python3` where
that is the Python 3 command. Helpers use gh's credential helper per Git command, without
changing global config; interactive Git login prompts are disabled. Speak the user's
language even though the repository-ready instructions and helper messages are English.

## Preflight, queue and version checks

```text
python <helper> doctor --repo owner/repo --checkout <clone>
python <helper> session
python <helper> list --repo owner/repo --repo owner/other
python <helper> events --repo owner/repo --pr 123
python <helper> version --repo owner/repo --pr 123
python <helper> version --repo owner/repo --pr 123 --expect-head <head-sha> --expect-base <base-sha> --expect-base-branch <branch>
```

`doctor` checks gh login, reported repository permissions and origin/pushurl identity.
Also check Git transport with `git ls-remote origin HEAD`. Comments mode needs review
permission and write access for coordination refs. Fix mode also needs code-push and
merge permissions. Metadata is not a guarantee that protections allow a particular
action. Explain actual denials; never elevate privileges or bypass them.
The helper supports github.com; do not silently use it for another GitHub host.

`list` fetches every page and sorts all repositories by creation time. Failure in any
selected repo fails the whole snapshot; do not present partial counts as complete.
Read descriptions, discussion and CI through gh with explicit repo as needed. Also
paginate PRs based on a branch when checking dependencies before branch deletion.

`version` reads the PR head and resolves the **current tip of its target branch**,
not a local/stale base ref. Save both full SHAs and the branch name as review context.
With expectations supplied it exits 1 if either commit or the target branch changed,
or the PR is closed/draft. Supply all three expectations for final checks.
Fetch the exact pair, recompute merge-base, assess new interactions, update independent
review and affected checks before trying again. Never label prior evidence valid for a
new pair. If the base branch itself is retargeted, reassess scope/deployment even if it
happens to point to the same commit. Do not broaden deployment authorization by retargeting.

## Shared claims across machines

Claims use `refs/pr-review/claims/<number>` in the selected repository. The skill name
is now wesports-pr-review, but the coordination namespace intentionally stays unchanged
so older participating clients still see the same claims. Metadata commits have an
empty tree and only protocol version, session, owner display name, head and expiry.
No code branches, comments, secrets or business records are created for coordination.

Create a fresh session id with `session` for each execution. Keep it distinct from
the saved run id, including when resuming an existing run.

```text
python <helper> claim list --repo owner/repo --checkout <clone>
python <helper> claim take --repo owner/repo --checkout <clone> --pr 123 --session <session> --head <sha> --owner <github-login>
python <helper> claim renew --repo owner/repo --checkout <clone> --pr 123 --session <session> --head <sha>
python <helper> claim check --repo owner/repo --checkout <clone> --pr 123 --session <session> --head <sha>
python <helper> claim free --repo owner/repo --checkout <clone> --pr 123 --session <session>
```

For merge/deploy coordination use the same commands with `--resource merge-deploy`
instead of `--pr`. Acquire before final checks and hold through merge/deploy. Inspect
all relevant main runs inside it, including other sessions' runs. Wait for active
deploys and require verified recovery from a failed latest deployment before another
merge. Renew both claims while waiting. For Data hold only through merge, never manual
deployment. Comments mode never takes this merge/deploy claim.

Exit 0 means the action succeeded, 1 means busy/lost ownership, and 2 means an error.
Do not publish/push/merge after 1 or 2. No silent fallback to a local-only lock if
the server rejects refs or write access is unavailable.

Updates/deletion use exact-OID `--force-with-lease`. Creation requires absence; takeover
of an expired claim requires the same observed OID. Another owner's renewal cannot be
overwritten. This is a cooperative protocol, not a barrier against manual changes.
The Git semantics are described in https://git-scm.com/docs/git-push.

Claims last one hour by default. Renew at least every ten minutes and immediately
before external writes, including while tests/review agents work. Use bounded waits.
On lost ownership stop writes and retain unpublished work. An old owner cannot release
a new owner's claim. Investigate obviously incorrect timestamps; clocks must be synced.
All participating reviewers must use this shared protocol. Old local `prclaim` sessions
do not participate: reconcile any such active work before acquiring a new shared claim.

## Worktrees, code changes and merge

- Claim before PR fetch. Fetch head into `refs/pr-review/<session>/pr<N>` and target
  branch into a separate session ref. Verify both SHAs against `version`. Never use
  FETCH_HEAD. On a race reread current versions instead of accepting a mismatch.
- Create a unique temp/scratchpad worktree with
  `git -C <clone> -c core.longpaths=true worktree add --detach <path> <head-sha>`.
  Verify HEAD and use explicit working directories for code, diffs and tests. Use the
  command flag for longpaths, not shared config. Never reuse another execution's worktree.
- Install locked dependencies when needed; do not share writable node_modules or alter
  a shared venv. Run Python against worktree code. Test actual combined behavior against
  the pinned current target where appropriate, not only the isolated PR's old base.
- Before source fixes reserve a round in the saved run. Re-run gates and obtain a new
  independent review. Before push check the current pair and claim; push without force
  to the PR's actual head repository/remote. Forks must not accidentally write to the base repo.
- Merge from a neutral directory outside every checkout using
  `gh pr merge N --repo owner/repo --squash --match-head-commit <reviewed-head>`.
  Respect required queues/protections. Delete a branch only if no other open PR uses
  it as base; otherwise keep it, without automatically retargeting others.
- Verify actual merged status and merge commit, including the actual base parent when
  comparing with pinned review context. A queue can introduce a new base; update evidence
  for its tested combined state. Do not call a queued PR merged or an old review current.
- Track the actual merge's deployment using short waits so claims can be renewed.
- Before cleanup inspect status, unpublished commits and valuable files. Remove with
  `git -C <clone> worktree remove <path>`, not routine force or recursive deletion.
  If generated files block cleanup, inspect them and confirm the absolute target is
  this execution's worktree within its chosen temp/scratchpad root before deleting.
  Preserve valuable work with an explanatory path. Remove only your own refs.

## Saved runs, receipts and waiting items

Read [resume.md](resume.md) for run creation, continuation, mode/scope changes and rounds.
Each run saves repos, mode, named PR restrictions, start preference, status and per-PR
progress. Record with `--run <id>` after each PR. The helper atomically writes separate
per-PR files, avoiding a shared monolithic state file. Run/PR fix reservations survive
new heads, compaction and resumption. The main agent is the writer of run state.

State lives outside the skill. `PR_REVIEW_STATE_DIR` overrides it; the default remains
the existing platform state directory named `pr-review` for backward compatibility.
Use complete repository identity plus PR number. No personal state belongs in ws-dev-env.
Old receipts without a base are historical notes, not evidence for a current head/base pair.

```text
python <helper> history --repo owner/repo --pr 123
python <helper> record --run <run-id> --repo owner/repo --pr 123 --input <receipt.json>
```

Receipts require `head`, `base` and `result` (reviewed, fixed, merged, waiting). Save
`baseBranch` from version too, so target-branch changes can be checked after resuming. Optional
fields are `handledEvents`, a short `note`, structured `waiting` and `verification`.
New waiting records must provide reason, owner, question when applicable and nextStep
as documented in resume.md. Verification entries must use the receipt's exact pair.
Store no PR bodies, sensitive business records, screenshots or secrets in state.

Publish a common GitHub receipt even without findings: reviewed head/base and target branch, mode, actual
checks/journey outcomes and remaining gaps. Include run id and rounds consumed so the
context is visible to colleagues. Keep the compatible marker
`<!-- pr-review:v1 head=<sha> base=<sha> mode=<comments|fix> -->`.
Use a normal comment if a review type is disallowed. Reuse an existing matching receipt
instead of repeatedly posting it. A receipt is not a guarantee of bug-free code.

Record event versions actually read/handled, and exact ids/versions of your own posts.
Do not mark every event arriving during work as handled or filter everything by the
same login. New external replies may arrive during your own writes. Cross-machine
history is established from GitHub receipts, current versions and shared claims, not
another person's local state. A waiting item is actionable only when its actual
dependency changes. Existing legacy state.json/logs/claims stay local and preserved.
