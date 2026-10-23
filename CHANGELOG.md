# Changelog

User-visible changes are recorded here, newest version first. Version numbers
use `MAJOR.MINOR.PATCH`. `Unreleased` means the version is still being prepared;
it does not imply that a release or tag has been published.

## [0.1.0] - Unreleased

### Added

- Install Codex CLI alongside Claude Code on Windows and Mac.
- Distribute shared `AGENTS.WeSports.md` instructions to both coding agents
  while preserving personal instructions and backing up changed files.
- Install all shared and personal skill bundles, including the wsg-cli skill,
  for both Claude Code and Codex. Configure skill destinations in the package
  list and synchronize them separately with `sync-skills.py`.
- Include Ghostty in the Mac setup.
- Track version changes in this changelog and generate the latest-version
  summary at the top of the README, with automated consistency checks.

### Changed

- Write repository documentation and agent instructions in English.
- Focus shared agent guidance on helping non-developers build useful products,
  making safe changes, choosing clear UX patterns and verifying results.
- Keep computer setup and migration details in the setup guides, and follow
  each project's database migration conventions.

### Fixed

- Report skill name conflicts instead of silently leaving coding agents with
  different skill installations or overwriting personal skills.
- Refresh the wsg-cli skill for every configured coding agent on repeat setup.

This is the first documented version, covering the existing setup and the
changes currently being prepared. Earlier work is recorded in Git history.
