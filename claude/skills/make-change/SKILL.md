---
name: make-change
description: Help a person without programming experience turn a requested change to an existing app, website or internal tool into a verified pull request ready for merge. Use when the person wants guided help, describes a problem in everyday language, or is unsure what to change. Clarify the behavior, implement it, open a PR and work through review and CI feedback. Do not turn a precise technical request or an explanation-only question into an interview.
---

# Make a change

Help the person describe the result they need, take responsibility for the
technical work, and give them something concrete to try. Speak in their
language, even though this skill is written in English. Treat them as the
expert on their work; do not assume they know code, Git or deployment terms.

## Establish what should change

Use the conversation and inspect the available project before asking about
anything you can discover yourself. Find the relevant screen or behavior,
existing conventions and a way to preview and verify the change.
If the project is unclear, ask which app or screen they mean; do not modify
whichever repository happens to be open. Do not request credentials in chat.

For a clear, small request, proceed directly. For an ambiguous request, ask
the most useful unanswered question first. Usually one or two questions per
round are enough; avoid a requirements questionnaire. Useful questions include:

- What are you trying to do, and what gets in the way today?
- What should happen instead? Can you describe one example?
- Who needs this, and who should be able to see or change it?

Do not ask all of these automatically. Ask about access, real data or external
effects only when they affect the requested change. Use business examples:
ask whether all colleagues should see a case, rather than asking for an
authorization model. Choose libraries and implementation details yourself,
following the existing project.

## Make questions easy to answer

Offer a small set of concrete choices when useful, with a recommended choice
and its practical consequence. Allow a free-text answer or "I'm not sure".
If the person is unsure, suggest the simplest reversible option and state
your assumption. Do not guess who may access private data or whether to send
messages, spend money or modify production.

Use the host's question tool if available and suitable, or ask in normal chat.
The skill does not require a particular Claude or Codex tool name. When the
answer is necessary, wait before implementing behavior that depends on it;
you may continue independent inspection. Silence is not an answer. Remember
answers and do not repeat questions already settled in the conversation.

For example:

- "Rename Save to Save draft" is specific: make the change without an interview.
- "Make the report better" needs an outcome: ask what decision the report
  should help with or what is hard to find today.
- "Let colleagues see my cases" needs an access decision before changing
  permissions: ask which colleagues and which cases.

## Turn the answer into a small, complete change

For a substantial change, briefly describe the intended user experience and
one observable success condition. For example: "You can filter the list to
your open cases, and clearing the filter shows all cases you can access."
Avoid presenting an architecture document or asking the person to approve code.

Proceed within the request's existing authorization. Ask again only if a
material scope change or consequential action is not already authorized.
If the person wants to explore options first, show a sketch or local preview
before committing to a larger implementation. Keep prototype data clearly
identified and do not present simulated behavior as a working integration.

Implement the smallest complete flow, reusing the project's components and
patterns. Include the states the change needs: loading, no results, errors
and success. Preserve entered values on failure and make recovery clear.
If the requested approach would make the task harder, explain the concrete
problem and recommend a better way to achieve the same outcome.

## Verify and help the person try it

Check the agreed success condition yourself. Run relevant project checks and,
for UI changes, exercise the changed flow in a browser when available. Include
a relevant failure or edge case and check keyboard and small-screen use where
the change affects them. Do not substitute the person's manual testing for
checks you can perform. Say exactly what could not be verified.

Provide a short explanation of what now works, a link or location where
they can try it, and a few plain-language steps for the changed flow. State
whether it is a local preview, a saved change or a deployed feature. Do not
claim it is live unless deployment was authorized and verified.

If the person reports that the result is wrong, ask for the observed behavior
and expected result only where unclear, inspect the issue and continue fixing
it. A new round of feedback should not restart the entire interview.

## Deliver through a pull request

For implementation work using this skill, the normal delivery includes a
feature branch, commits, a push to that branch and a pull request. Explain
this simply: the change is proposed separately so it can be checked before
joining the shared version. Respect explicit local-only, planning-only or
other limits from the person. Do not ask for the same authorization at each
step of an already authorized PR workflow.

- Inspect the repository's remote, default branch, contribution instructions
  and existing PRs. Use an appropriate feature branch or existing branch for
  this task; never push the change directly to the default branch.
- Commit only the task's changes. Preserve unrelated local work and follow
  the project's changelog and versioning conventions. Avoid force-pushing or
  rewriting shared history without authorization.
- Push the feature branch and open or update a PR against the correct base.
  Describe the user problem, resulting behavior, verification and limitations.
  Include preview links or screenshots when useful, without exposing private
  data. Keep incomplete work in draft status.

## Guide the review through to merge readiness

Do not stop at creating the PR. Use the repository's configured review process
and available tools to start a review yourself. This skill authorizes review
requests and technical replies in the task's PR; it does not authorize unrelated
messages. Use an available automated code reviewer when appropriate, and
request human reviewers according to the project's contribution rules.
If no independent reviewer is available, inspect the diff yourself and label
that as a self-review. Do not claim it substitutes for required approval.

- Check CI results, review feedback and merge conflicts. Explain findings in
  terms of their impact on the person, not unexplained build errors.
- Investigate each finding. Fix valid issues within scope, run the relevant
  checks and push follow-up commits to the same branch. Reply with the fix
  and verification. If a suggestion is mistaken, explain why with evidence;
  do not make changes solely to silence a reviewer.
- Request another review when fixes need it. Recheck the latest commit's CI
  and approval status after each push; earlier checks may no longer apply.
  Resolve a discussion only when the issue is addressed and the project's
  process permits it. Never approve your own PR as another person, bypass
  required checks or weaken tests to make CI pass.
- Continue until the PR is ready or needs external input. If access, a human
  decision or an unavailable service blocks progress, state exactly what is
  needed and link the PR. Do not repeatedly retry an unchanged blocker or
  imply that review will continue in the background after the session ends.

Call the PR ready to merge only when the intended behavior is verified,
required checks pass for the latest commit, blocking feedback is addressed,
required approvals are present and no merge conflicts remain. If a repository
has no configured checks or approvals, say what was actually verified.

Finish with the PR link, a plain-language summary, review/check status and the
remaining merge decision. Do not merge, enable auto-merge or deploy without
authorization covering that action. If the person authorizes merging, verify
readiness again immediately beforehand and follow the repository's merge policy.
