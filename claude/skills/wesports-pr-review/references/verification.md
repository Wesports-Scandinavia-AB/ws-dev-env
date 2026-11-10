# Verify the affected user journey

For a visible behavior change identify the action, intended user/role, expected result
and meaningful regression. Derive scenarios from the actual PR and existing behavior.
This includes screens, APIs, imports and reports. Documentation-only changes can be
marked not applicable with a reason.

Choose an isolated local/test or authorized preview environment running the reviewed
version. Use fixtures or synthetic data. Review authorization does not authorize
production writes, payments, customer messages or changes to live business data. Use
local substitutes for those side effects. Never ask for secrets in chat.

Exercise the happy path and failure/role cases affected by the PR. For example, record
absence as an employee, verify the total and manager view, and check company isolation.
Do not apply every possible scenario to every PR. Use browser/app tools when available,
otherwise a meaningful integration test of the same behavior. Explain what remains
unverified if only part of the journey is covered. A green build is not UI evidence.

Store `verification` in the receipt as a list of entries with `flow`, `status`,
`environment`, `head`, `base` and `detail`. Status is `passed`, `failed`, `not-run` or
`not-applicable`. Commits must match the receipt. For not-run state the reason, such
as missing authorized test login. Failed verification is a finding when caused by
the change. Fix or wait on material uncertainty instead of treating not-run as passed.
Justified not-applicable is valid when there is no user journey to exercise.

Retest affected behavior after fixes or base/head movement. Evidence from a stale
worktree or unrelated deployed version does not cover the PR. Summarize for the user
in plain language; retain technical evidence in the receipt without sensitive records.
