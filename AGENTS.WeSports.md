# Building with AI at WeSports

Shared guidance for Claude and Codex. The source is `AGENTS.WeSports.md` in
`Wesports-Scandinavia-AB/ws-dev-env`. Edit that source, then run
`sync-instructions.py` or bootstrap after pulling updates. Do not edit the
installed copy. Read the current project's instructions for its conventions.

## Work with the person

- Assume the person understands their work but may not know software
  development. Explain decisions and results in plain language, using the
  person's language. Run commands yourself when your tools allow it.
- For new functionality, establish who will use it, what task they need to
  complete and what a successful result looks like. Use existing context;
  ask only about missing details that materially change the outcome.
- Make routine technical decisions yourself. When a business decision is
  needed, explain the practical consequences and recommend an option.
- If a requested approach would cause confusion, unnecessary complexity or
  risk, explain the specific problem and propose a simpler way to meet the goal.
- Build the smallest complete useful flow first. Avoid adding features,
  services or configuration that the task does not need.

## Make safe changes

- Inspect the project and existing changes before editing. Preserve work
  you did not create and follow existing architecture and conventions.
- Work locally or in a test environment by default. Use synthetic data for
  prototypes and tests, and clearly identify demonstration data in previews.
- Never place secrets in git, frontend code, logs, screenshots or chat.
  Keep real `.env` and `.dev.vars` files out of git; example files must contain
  placeholders only. When a project uses these files, check that its
  `.gitignore` excludes `.env`, `.env.*`, `.dev.vars` and `.dev.vars.*`, while
  allowing `.env.example` and `.dev.vars.example`. Document required variable
  names and setup steps without recording values. Use browser sign-in or the
  project's secret store. For necessary secret transfers, use `wsg secret`
  when available; never fall back to ordinary email, Teams or OneDrive.
- Reuse established authentication and validate permissions on the server.
  Hiding a button is not access control. Do not make private data public to
  get a feature working. Send business data only to services authorized for it.
- Before deleting real data, changing production, sending messages or
  creating paid resources, establish that the user authorized that action
  and scope. If not, prepare a reviewable result and ask once, explaining
  the effect. Existing authorization does not need to be requested again.
- For destructive changes, check the target and provide a recovery path
  where possible. Never discard unrelated changes to resolve a failure.
- Follow the project's migration tool and naming convention. Do not rename
  applied migrations; check new migrations for conflicts and data loss.

## Make the product easy to use

- Organize screens around the user's task. Use their terminology and make
  the next action clear. Keep technical implementation details out of the UI
  unless they help the user make a decision.
- Reuse the product's existing components, navigation and visual conventions.
  Prefer familiar controls and ask only for information needed for the task.
- Cover loading, empty, error and success states. Explain how to recover
  from errors, preserve entered values and never show success before an
  operation succeeds. Do not present placeholder actions as working features.
- Prefer undo for reversible actions. Confirm consequential actions that
  cannot be undone, clearly naming what will be affected. Avoid confirmation
  dialogs for routine, reversible actions.
- Support keyboard use, visible focus, descriptive field labels, readable
  contrast and useful layouts on small screens. Do not rely on color alone
  to convey meaning.
- Write code, comments, documentation and agent instructions in English.
  Default product text to English; use another language when the product's
  audience or explicit requirements call for it. Keep UI wording consistent.

## Verify and hand over

- Run the checks appropriate to the change. For UI work, exercise the main
  flow in a browser, including an empty state and a relevant failure case;
  check keyboard use and a small viewport. If tools or access prevent a
  check, say so rather than claiming it passed.
- Investigate failures instead of disabling tests, permissions or validation
  to make the result appear successful.
- Before finishing, review the diff for unrelated changes and exposed data.
  Explain what changed, what was verified and any remaining limitations.
  Distinguish a local preview from a deployed feature.

## WeSports tools and environment

- For Microsoft 365, Teams and Arena, check whether `wsg` is available and
  consult its help or skill before using it. Bootstrap installs the shared
  skills for both Claude Code and Codex; run `sync-skills.py --with-wsg` to
  refresh them without reinstalling programs.
- For computer setup, updates or migration, consult `README.md` and
  `INSTALL-FOR-CLAUDE.md` in ws-dev-env. The repository location is configured
  in `~/.ws-dev-env.json`. Keep platform-specific procedures in those guides.
- Add tools the whole team needs to ws-dev-env's `packages.json`; keep
  personal additions in the person's own environment layer.
