# Changelog

User-visible changes are recorded here, newest version first. Version numbers
use `MAJOR.MINOR.PATCH`. `Unreleased` means the version is still being prepared;
it does not imply that a release or tag has been published.

## [0.1.0] - Unreleased

### Added

- Configure global Git ignores for local environment secret files on Windows
  and Mac, plus `.hidden`, while preserving existing excludes-file contents.
- Add the `make-change` skill to guide people without programming experience
  through clarifying, implementing and trying a change, then opening a PR and
  working through review and CI feedback until it is ready to merge. Ask
  focused questions only when needed; merging requires its own authorization.
- Ignore local environment secret files and document safe project-level setup.
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

- Update the TODO list to reflect the completed guided PR workflow, shared
  agent setup and version history, and clarify the remaining secrets and
  global Git configuration work.
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
