# Working on ws-dev-env

These instructions apply to this repository. `AGENTS.WeSports.md` is the
separate source of guidance distributed to users' computers.

- Write repository content in English.
- Preserve unrelated local changes and never commit generated Python caches.
- Update `CHANGELOG.md` in the same change as code, configuration, instructions
  or documentation. Describe the practical effect for users, not individual
  implementation steps. Record fixes and limitations honestly.
- Keep versions newest first. Add changes to the current `Unreleased` version.
  If the latest version already has a release date, create a new version above
  it: increment PATCH for compatible fixes, MINOR for compatible additions and
  MAJOR for breaking changes. Do not rewrite previous release history.
- Before publishing a version, replace `Unreleased` with its actual release
  date (`YYYY-MM-DD`). Create or push a version tag only when release publishing
  is authorized. Do not describe uncommitted work as released.
- After editing the changelog, run `python scripts/update-readme.py` (use
  `python3` on Mac). The README's latest-version block is generated; edit its
  source in the changelog, not the block itself.
- Before committing or pushing, run `python scripts/update-readme.py --check`,
  `python -B -m unittest discover -s tests -v` and `git diff --check`.
  For bootstrap changes, also validate PowerShell and Bash syntax.
- When adding a local coding agent, define its `skill_dir` in `packages.json`
  so it receives the same shared and personal skills as the other agents.
