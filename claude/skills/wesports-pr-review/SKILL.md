---
name: wesports-pr-review
description: Review open pull requests in user-selected repositories, oldest first. Ask where to start and whether to comment only or fix and merge. Resume saved runs with fresh GitHub checks. Use for wesports-pr-review, pr-review, prvarv or requests to review PRs; distinguish these from requests to edit this skill.
---

# WeSports PR review

Drive the review for users who may not program. Handle Git, worktrees, tests and
technical troubleshooting yourself. Speak the user's language and explain user impact.
Paths below are relative to this skill. Read [operations.md](references/operations.md)
for commands and coordination, and [repositories.md](references/repositories.md) after
selecting repositories. No personal paths or separately installed system skills are needed.

## 1. Select repositories or resume

Ask which projects' proposed changes to review. Offer Arena
(`Wesports-Scandinavia-AB/wesports-arena`), Data (`Wesports-Scandinavia-AB/wesports-data`),
both, or other repositories. Use choices already given without asking again. Do not
infer scope from the working directory or past runs. Do not list PRs before scope is
clear. If helpful, explain that a PR is a proposed change not yet incorporated into
the project's main version.

On "continue where we left off", follow [resume.md](references/resume.md). Restore
the saved repository selection, mode, scope and progress; recap and refresh GitHub.
Do not re-ask answered questions, reset fix-round counters or adopt an old execution's
claim ownership. Ask a focused question if several runs could match or context is absent.

## 2. Check the environment

Use `scripts/pr_review.py` with Python 3.10+. Check Git, GitHub CLI, login, repo access
and clone origins using `doctor`. Locate clones in the supplied workspace; if missing,
create an isolated clone in the session's temp directory. Leave existing clones' files,
index, current branch, remotes and global configuration unchanged.

Check availability of independent agent tools. If missing, explain the limitation;
do not claim independent review or merge without it. Resolve routine setup issues
within existing permissions. If user action is needed, explain the missing access and
a concrete next step without asking a non-programmer to design the implementation.
Never print secrets or credential-bearing URLs. Do not install system tools or raise
privileges without the environment's required permission.

## 3. Show the queue and choose how to proceed

Fetch all open PRs in selected repositories using `list`. Show one combined list,
oldest creation time first, breaking ties by repository then PR number. Include project,
PR link, title, author and date. Read descriptions and enough diff to briefly explain
each change's purpose and affected users. Say when intent is unclear instead of guessing.
Mark drafts, already reviewed versions and claims held by others. Report an empty list
and stop if there is nothing open.

Ask together, only for choices not already supplied:

1. Which PR should we start with, or should we start with the oldest?
2. Should I **review and comment**, or **review, fix and merge**?

Explain the alternatives before the answer:

- **Review and comment:** publish verified feedback on GitHub. Do not edit source,
  commit fixes, push code, change PR bases or merge. Worktrees, dependencies, tests,
  coordination refs and receipts remain part of the work.
- **Review, fix and merge:** fix verified issues with clear solutions, test, obtain
  independent review and squash-merge when nothing blocks it and required checks pass.
  Includes PRs without findings and all authors, including the requesting user. Do not
  ask for another merge confirmation. Explain that Arena merges deploy to production;
  Data requires a separate manual deployment. Establish other repos' deployment
  consequences before choosing this mode.

An explicit `--fix` selects fix-and-merge mode; explain that merge and automatic deployment
are included. An explicit comments-only request selects comments mode. Wait for missing
choices before claiming/reviewing. Save choices with `run-start`. Follow the selected
start PR, then oldest first, within any explicit restriction to named PRs. Keep mode
and scope until the user changes them. Persist explicit changes with `run-configure`,
retaining the same run id and fix-round counters.

## 4. Handle one PR at a time

1. Read live status, target branch, head SHA and actual target-branch SHA with `version`.
   Skip drafts even when oldest; do not mark them ready or push fixes. Take the shared
   PR claim before first PR fetch. Skip claims held by others. Do not use the old local
   `prclaim` helper for team coordination.
2. Create a unique detached worktree at the verified head and pin the fetched target
   branch too. Review the merge-base diff. Read applicable agent/review rules, prior
   reviews and author responses. Follow contracts into consumers beyond changed files
   and across repositories where relevant.
3. Start a **separate review agent** with [reviewer.md](references/reviewer.md), worktree,
   repo/PR, pinned head/base and applicable rules. Supply raw evidence without steering
   conclusions. The reviewer reads/reports; the main agent manages changes, GitHub and
   claim renewal. Do not handle multiple PRs in parallel.
4. Verify findings against code, tests and callers. Check CI for the reviewed version
   and run repository-mandated checks. Unknown, missing, skipped, cancelled or pending
   required checks are not passing results.
5. For user-visible behavior, follow [verification.md](references/verification.md).
   Exercise affected user journeys in an isolated local/test environment, including
   changed roles and failure paths. Record passed, failed or not-run with the reviewed
   version and environment. Green builds alone do not verify user journeys. Resolve
   material uncertainty before merge.
6. In comments mode, publish all new verified findings in one review, marking blockers
   according to repo rules. Do not duplicate answered findings. If GitHub disallows a
   review type on the user's own PR, use a regular PR comment without bypassing rights.
   With no findings, publish a factual version-bound review receipt.
7. In fix mode, reserve a round with `fix-round` **before source edits**. Fix confirmed
   issues with clear solutions in the PR worktree without unrelated redesign. If a
   product decision is needed, explain consequences and concrete options. Save a waiting
   item with reason, responsible person, question and next step. Do not guess behavior
   or ask non-programmers to decide implementation details.
8. Run relevant tests and the repo gate after fixes. Use a **new separate reviewer**
   for fixes, their consequences and equivalent paths. Reuse verified review of unchanged
   code only when its context still applies; otherwise review the whole diff. There are
   **three fix/re-review rounds per PR in the entire saved run**, not per commit. Own
   pushes, new head/base commits, context compaction and resume never reset the budget.
   On exhaustion leave a precise waiting item and continue other PRs.
9. Before publishing review, pushing, changing PR base or merging, verify/renew the
   claim and use `version --expect-head ... --expect-base ... --expect-base-branch ...`. If either commit or the branch changed,
   fetch and pin the new pair, recompute merge-base, inspect new interactions and update
   independent review, integration/user-flow tests and required checks. An unchanged
   head is insufficient when the target branch moved. Do not reset rounds. Never
   force-push; target the actual head repository, including forks. Recheck draft/open status.
10. Merge only in fix mode with no repo-defined blocker and passing required checks.
    Follow repo rules for non-blocking follow-ups. Acquire the shared merge/deploy claim
    before final live checks; retain it through merge and automatic deployment. Inside
    the claim inspect other main/deploy activity and verify the head/base pair again.
    Use `--match-head-commit` with the reviewed head; never use admin bypass. Where
    available, use strict up-to-date requirements or a merge queue to guard target
    movement between check and merge. If an unreviewed base is detected after merge,
    report it and immediately verify the combined state, not a fictitious prior review.
11. Follow the deployment for the actual merge commit. Do not merge the next Arena PR
    before it finishes. On failed deployment suspend merges in that flow and investigate
    within scope. Data is never deployed by this skill. Keep reviewed, fixed, merged
    and deployed outcomes distinct.
12. Save the local run receipt and a version-bound GitHub receipt, including no-finding
    reviews. Clean up or explain retained worktrees, preserve unpushed work and release
    claims according to operations.md.

## 5. Report progress and rebuild the queue

Immediately after each PR report its outcome, PR link and user impact in plain language.
Say "no verified findings", not "guaranteed bug-free". Fetch **all selected repos** again,
including relevant new events, CI and claims. Rebuild the queue with new PRs, changed
heads/bases and relevant external replies; remove closed/merged PRs. Continue oldest
first within scope without repeating starting/mode questions. Never just decrement
the initial list.

Show current open total, remaining actionable PRs and already handled/waiting items,
including per-repo counts when several are selected. Name the next PR and new arrivals.
A commented PR remains open without becoming unreviewed at every refresh. Track actual
handled event versions, not everything appearing after your own write. Do not ignore
all activity from the same login; it may come from a different session.

For each waiting PR show **what blocks it, who can resolve it, the question if a decision
is needed, and the next step**. Distinguish human decisions from CI, another reviewer
or access. Do not invent an owner. Resume only when new evidence enables a concrete
action. An explicit selection of unchanged code requests review again but does not
reset that run's fix budget.

Check GitHub even when the queue seems empty. Retry a failed refresh once; if it still
fails, say current counts are unverified and stop rather than use a stale queue. When
nothing more can proceed, report outcomes, waiting questions and fresh counts. Save
status paused only at the user's request, waiting for unresolved items, or complete
when finished. Do not schedule future runs or poll forever without an explicit request.
