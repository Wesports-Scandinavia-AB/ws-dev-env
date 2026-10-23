---
name: ws-dev-env
description: Set up or update a WeSports development computer with ws-dev-env, and check that nothing will be lost before leaving a computer. Use when the user asks about a new computer, switching computers, moving to a new computer, setting up their computer, updating the development environment, wiping a computer, checking before leaving a computer, or sharing a program, repository or agent rule with the whole team.
---

# ws-dev-env

The `Wesports-Scandinavia-AB/ws-dev-env` repository describes a WeSports
development computer: programs (`packages.json`), repositories (`repos.txt`),
shared Claude and Codex instructions (`AGENTS.WeSports.md`) and Claude skills
(`claude/skills/`). It is cloned under the root in `~/.ws-dev-env.json`,
usually `~/source/repos/ws-dev-env`.

## Switching computers

1. **On the old computer**, run the check and review its findings with the user:

   ```
   powershell -ExecutionPolicy Bypass -File <root>\ws-dev-env\check.ps1
   ```

   Yellow means something will be lost: commit and push, or transfer secrets
   with `wsg secret`. Blue indicates reminders (memory, SSH keys).
   Do not say the computer can be wiped until the script reports "Nothing lost".

2. **On the new computer**, follow `INSTALL-FOR-CLAUDE.md` in the repository.

3. **SSH**: never transfer the private key. `bootstrap.ps1` creates a new key
   and prints its public part. Add it to the server from the old computer,
   which already has access:

   ```
   ssh <user>@<server> "echo '<public key>' >> ~/.ssh/authorized_keys"
   ```

   Once the new key works, remove the old computer's entry from `authorized_keys`.

## Updating

Run `git pull` in ws-dev-env, then run `bootstrap.ps1` again. Existing
installations are skipped and shared instructions are refreshed. `-DryRun`
shows what would happen without making changes.

On Mac, run `bootstrap.sh` (`--dry-run`). To update instructions only, run
`git pull` and `python sync-instructions.py` in the repository (`python3` on Mac).
Synchronization copies AGENTS.WeSports.md to both tools and preserves personal
instructions. Ask the user to start a new agent session afterwards.

## Sharing with everyone

Add programs, repositories, rules and skills the whole team needs to
ws-dev-env, not just the local computer. Personal additions belong in the
user's own layer (`-Personal owner/repo`, with the same layout). Never add
secrets, tokens or personal paths to ws-dev-env.
