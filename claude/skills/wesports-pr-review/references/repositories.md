# Repository rules and deployment

Use full repo identity for commands, claims and history. In conversation use `arena#N`,
`data#N`, or `owner/repo#N` for others. Pass explicit repo to gh and discover clones
through origin, not usernames or fixed paths.

## Arena

`Wesports-Scandinavia-AB/wesports-arena`.

- Read current agent instructions and `docs/REVIEW.md`; compare protections with the
  base. A PR must not weaken its own review requirements. Follow the complete gate and
  repo blocker/follow-up rules. Never weaken checks or use `--no-verify`.
- Check policies/in-handler authorization, tier3 boundaries, timestamped migrations,
  `exactOptionalPropertyTypes` and System map updates for topology changes.
- Follow new fields/formats through registry export, reserved config keys, publication
  contracts, integration catalog and Data. Export errors can affect every company.
- Do not edit `.github/workflows/`, applied migrations, `functions/_lib/gate.ts`'s auth
  spine or `db/import/`. Report findings there without fixing them.
- Merge to main deploys to production. Track the actual merge's run, not older green
  results. Use the shared merge/deploy claim. Check affected journeys and roles in an
  isolated environment, including company switching and truthful error/empty states.
- Do not dismiss flaky tests by reputation. Compare against base, rerun once for a
  verified flake and require green according to the gate.

## Data

`Wesports-Scandinavia-AB/wesports-data`.

- Read agent instructions, `docs/CONVENTIONS.md` and module docstrings. Preserve raw-first
  behavior, secret resolution/scrubbing and PII boundaries.
- Check what CI exists now. If absent, run affected pytest suites and pyflakes in the
  worktree using repo dependencies. Find a local Python environment or create an isolated
  venv, never alter a shared one. Use UTF-8. Compare platform failures on a separate
  base worktree instead of assuming they are old.
- Check tables/platforms/fields against Arena's catalog, `platformContract.json`, registry
  export reserved keys/credential filters and `PUBLISH_DATASETS`. Required Arena changes
  must merge before dependent Data PRs.
- Verify changed reporting/import journeys with synthetic or authorized test data,
  including values as consumed by Arena. Do not run production imports.
- Merge is not deployment. Read `infra/setup_vm.md` for context but never deploy.
  Report publication as unknown without an authorized read source. Do not guess from
  main or a missing personal helper, or ask a non-programmer to run VM commands.

## Other repositories

Read their own instructions, tests, merge criteria and publication flow. Do not apply
Arena-specific paths or assumptions. Establish undocumented checks from real project
configuration. Explain unclear deployment consequences before fix/merge mode is chosen.
Never raise privileges or bypass branch protection.
