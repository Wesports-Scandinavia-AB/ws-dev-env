# WeSports development environment (shared)

This file is distributed from Wesports-Scandinavia-AB/ws-dev-env to Claude
and Codex. Edit the source file AGENTS.WeSports.md in the repository. Then
update with git pull and sync-instructions.py (or bootstrap). Do not edit
the installed copy.

## Computer

- Repositories live under the root in `~/.ws-dev-env.json`, usually
  `~/source/repos`. Use the same path on each computer so Claude can find
  its per-project memory.
- Add programs everyone needs to `packages.json` in ws-dev-env instead of
  only running `winget install` on your own computer.
- Before leaving or wiping a computer, run `check.ps1` in ws-dev-env.
  The items it lists exist only on that computer.

## Secrets

- Never put secrets in git, OneDrive, email, Teams or chat. Share passwords
  and keys with `wsg secret`, a one-time link encrypted before it leaves
  the computer.
- Keep `.env` and `.dev.vars` outside git and transfer them separately.
- Use one SSH key per computer. Never transfer a private key: generate a
  new key on the new computer and remove the old computer's public key
  from the servers.

## Code

- Name database migrations `YYYYMMDDHHMMSS_name.sql`, never with sequential
  numbers. Sequential numbers collide across branches; timestamps provide
  unique names without coordination.
- Use `wsg` (the `wsg` skill) for Microsoft 365, Teams and Arena from the terminal.
- Write all repository files in English, including documentation, agent
  instructions, comments and user-facing messages.
