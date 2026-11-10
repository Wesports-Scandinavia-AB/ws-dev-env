---
name: ws-dev-env
description: Set up or update a WeSports development computer with ws-dev-env, and check that nothing will be lost before leaving a computer. Use when the user asks about a new computer, switching computers, moving to a new computer, setting up their computer, updating the development environment, wiping a computer, checking before leaving a computer, or sharing a program, repository or agent rule with the whole team.
---

# ws-dev-env

The `Wesports-Scandinavia-AB/ws-dev-env` repository describes a WeSports
development computer: programs (`packages.json`), repositories (`repos.txt`),
shared Claude and Codex instructions (`AGENTS.WeSports.md`) and shared skills
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

Inspect local changes first, then use `git pull --ff-only` in ws-dev-env.
Never discard work to update. Run `bootstrap.ps1` again for missing installations. Existing
installations are skipped and shared instructions are refreshed. `-DryRun`
shows what would happen without making changes.

On Mac, run `bootstrap.sh` (`--dry-run`). To update instructions only, run
`git pull` and `python sync-instructions.py` in the repository (`python3` on Mac).
Synchronization copies AGENTS.WeSports.md to both tools and preserves personal
instructions. Ask the user to start a new agent session afterwards.

To synchronize skills only, run `python sync-skills.py --with-wsg` (`python3`
on Mac). Every shared and personal skill is installed for each coding agent
declared with `skill_dir` in `packages.json`. The `wsg` skill is refreshed
from the installed package. Resolve any reported name conflict rather than
overwriting a person's existing skill.

To update already-installed managed programs, preview with
`python scripts/update-tools.py` (`python3` on Mac), then run with `--apply` when
the user requested program updates. The updater targets only declared package
channels, including existing Codex and wsg. It preserves Python 3.12 and pnpm 9
compatibility channels; do not claim it installs every newest major. After wsg
updates, rerun `sync-skills.py --with-wsg`. Start a new agent session afterwards.
Run the commands yourself and explain any access, local-change or skill conflicts
without asking a non-developer to resolve Git internals. Follow README's update guide.

## Sharing with everyone

Add programs, repositories, rules and skills the whole team needs to
ws-dev-env, not just the local computer. Personal additions belong in the
user's own layer (`-Personal owner/repo`, with the same layout). Never add
secrets, tokens or personal paths to ws-dev-env.
