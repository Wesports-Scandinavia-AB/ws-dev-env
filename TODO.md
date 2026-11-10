# TODO

1. [ ] Complete local secrets management. Local `.env`/`.dev.vars` guidance
  and global Git ignores are in place; define how users set up, retrieve and
  update machine-specific credentials without exposing them in chat or Git.
2. [ ] Add automatic updates for the tools and repositories managed by this
  development environment, with a clear way to review or control updates.
3. [x] Create a skill that guides agents in writing code for our projects
  (`make-change`): clarify the need with non-developers, implement and verify
  the change, push a feature branch, open a PR and work through review and CI
  feedback until it is ready to merge. Merging requires authorization.
4. [ ] Review the global Git configuration behavior, including how ws-dev-env
  should preserve and update existing `core.excludesFile` settings. Initial
  ignore installation exists; updating an existing managed block still needs
  review.
5. [x] Distribute shared instructions and all shared/personal skills to both
  Claude Code and Codex, including the wsg-cli skill.
6. [x] Add a version changelog, generate the latest-version notes in README
  and add agent instructions and CI checks to keep them synchronized.
