# Independent review contract

This portable contract is based on `review-agent` and is supplied to a separate agent
in the available environment. No user-specific system skill is required.

Read the target in the specified worktree. Read applicable `AGENTS.md`, `CLAUDE.md`
and review rules. Verify the head and pinned target commit. Inspect the merge-base
diff representing what would actually merge. Use an explicit working directory.

Read and run checks as needed. Do not edit source, commit, push, publish comments,
merge, manage claims or delegate. Report version/evidence mismatches rather than
assessing another version as if it were requested.

The first pass covers the entire diff and surrounding code needed to understand each
changed path. Continue after the first issue and return all findings together. For
fixes inspect their diff, consequences and equivalent paths. Reuse review of unchanged
code only when its head/base context remains applicable. A changed target branch needs
assessment of new interactions even when the PR head did not change.

Flag issues only when introduced by the change, concrete, actionable and likely to
be fixed by the author. Demonstrate the scenario through code, callers or tests. Check
consumers outside changed files, especially new fields/formats. Exclude speculation,
pre-existing issues, intentional product decisions and immaterial style preferences.

For each finding return priority (P0 critical, P1 serious, P2 ordinary, P3 smaller),
a concrete title, file/minimal line location overlapping the diff, affected scenario,
user consequence, evidence, and blocker/follow-up classification under the repo rules.
Priority never overrides the repo's merge criteria.

If nothing qualifies, write "No verified findings." Add actual checks and material
gaps. For visible changes assess the supplied journey-verification evidence as well
as code/tests. Unexecuted journeys remain unexecuted even when CI passed. Never claim
code is bug-free or that tests ran when they did not.
