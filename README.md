# ws-dev-env

A WeSports developer computer, described in one repo: which programs, which
repos, shared Claude/Codex instructions and Claude skills to set up. A new
computer becomes a clone and a script, and whatever someone adds reaches
everyone with `git pull` followed by bootstrap or instruction sync.

Windows and Mac each have their own entrypoint (`bootstrap.ps1` and
`bootstrap.sh`), but share the same list: `packages.json`, `repos.txt` and
`claude/` are common to both, so the result is the same regardless of
computer. Linux has no entrypoint yet.

## Getting started

Open a terminal, paste the line for your computer and press Enter. The line
installs what's needed to get going (git, GitHub CLI, Claude Code, Herdr) and
then starts Claude with the task. Claude does the rest; you only log in to
your browser when it asks you to.

**New Windows computer (PowerShell):**

```powershell
'Git.Git','GitHub.cli','Anthropic.ClaudeCode','Herdr.Herdr.Preview' | % { winget install -e --id $_ --accept-source-agreements --accept-package-agreements }; $env:Path=[Environment]::GetEnvironmentVariable('Path','Machine')+';'+[Environment]::GetEnvironmentVariable('Path','User'); claude "This is my NEW computer. Log me in to GitHub, clone Wesports-Scandinavia-AB/ws-dev-env to ~/source/repos/ws-dev-env and follow INSTALL-FOR-CLAUDE.md in the repo. I'm not a developer: run everything yourself and never ask me to paste commands."
```

**Old Windows computer**, before you leave it:

```powershell
'Git.Git','GitHub.cli','Anthropic.ClaudeCode','Herdr.Herdr.Preview' | % { winget install -e --id $_ --accept-source-agreements --accept-package-agreements }; $env:Path=[Environment]::GetEnvironmentVariable('Path','Machine')+';'+[Environment]::GetEnvironmentVariable('Path','User'); claude "I'm switching computers and this is the OLD one. Log me in to GitHub, clone Wesports-Scandinavia-AB/ws-dev-env to ~/source/repos/ws-dev-env and follow the Switching computers section in INSTALL-FOR-CLAUDE.md. I'm not a developer: run everything yourself and ask before you change anything."
```

**New Mac (Terminal):**

```bash
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"; eval "$([ -x /opt/homebrew/bin/brew ] && /opt/homebrew/bin/brew shellenv || /usr/local/bin/brew shellenv)"; brew install git gh herdr; brew install --cask claude-code ghostty; claude "This is my NEW Mac. Log me in to GitHub, clone Wesports-Scandinavia-AB/ws-dev-env to ~/source/repos/ws-dev-env and follow INSTALL-FOR-CLAUDE.md in the repo. I'm not a developer: run everything yourself and never ask me to paste commands."
```

Ghostty is installed as the Mac terminal app. Open Ghostty from Applications
or Spotlight, then run `herdr` there. The first time Claude starts, you log in
to your Claude account.

Bootstrap also installs **Codex CLI**, using the official `@openai/codex` npm
package after Node.js is installed, on both Windows and Mac. Start `codex`
and sign in with your own account when you want to use it. An existing
`codex` command is left alone; bootstrap does not upgrade or replace it.
This installs the terminal tool, not the desktop app. See
[OpenAI's installation guidance](https://learn.chatgpt.com/docs/enterprise/windows-deployment).

## Contents

```
bootstrap.ps1   Windows: new computer, or bring an existing one up to date; safe to re-run
bootstrap.sh    Mac: the same, via Homebrew instead of winget
check.ps1       Windows, before leaving a computer: lists what only exists on it
packages.json   programs: winget/brew ids, or an npm package shared by Windows and Mac
repos.txt       repos everyone clones
AGENTS.WeSports.md  shared instructions for both agents
sync-instructions.py  update shared instructions without installing programs
claude/
  CLAUDE.md     compatibility import for older installations
  skills/       skills everyone gets, linked into ~/.claude/skills
```

Native packages with no `brew` or `winget` id are skipped on that platform
(`windows-terminal` is Windows only). Packages with an `npm` field are
installed globally on both platforms after the native packages; `name` is
the executable checked to avoid reinstalling an existing tool. There's no
`check.sh` for Mac: `check.ps1` is still Windows only.

## Shared instructions for Claude and Codex

`AGENTS.WeSports.md` is the shared source in this repo. Bootstrap copies it
beside each tool's global instruction file and adds a reference once:

| Tool | Copy destination | Reference in global file |
| --- | --- | --- |
| Claude Code | `~/.claude/AGENTS.WeSports.md` | `@AGENTS.WeSports.md` in `CLAUDE.md` |
| Codex | `~/.codex/AGENTS.WeSports.md` | Instruction to read the copy's absolute path in `AGENTS.md` |

`CLAUDE_CONFIG_DIR` and `CODEX_HOME` override the default directories. Personal
instructions are preserved, and changed existing files get a one-time
`.ws-dev-env.bak` backup. Repeated runs do not duplicate the reference.
The exact old shared Claude import for this checkout is removed; personal
layer imports remain. `claude/CLAUDE.md` remains a compatibility wrapper for
older installations. Skills are still installed for Claude only.

After pulling updates, run bootstrap or synchronize just the instructions:

```powershell
python sync-instructions.py --dry-run
python sync-instructions.py
```

On Mac use `python3`. Start a new agent session afterwards. `git pull` alone
does not update the installed copies. Edit shared rules in this repo; local
copies are replaced during synchronization. Project-specific rules belong
in each project's own `AGENTS.md`.

Claude expands its import automatically. Codex receives a plain instruction
to read the shared file; this is not an automatic import. Verify that it
actually reads the file in a fresh session before relying on it. A non-empty
Codex `AGENTS.override.md` masks `AGENTS.md`; the sync warns and leaves the
override untouched. Targets that are symlinks are rejected to protect their
sources. Moved checkouts may leave old Claude imports that need manual cleanup.

References: [Codex instruction discovery](https://learn.chatgpt.com/docs/agent-configuration/agents-md)
and [Claude imports](https://code.claude.com/docs/en/memory).

## Two layers

ws-dev-env is the shared layer. The personal one lives in your own private
repo with the same layout, for example `yourname/dev-env`:

```
packages.json   your own programs
repos.txt       your own repos
claude/
  CLAUDE.md     your own rules
  skills/       your own skills
```

Set it once with `bootstrap.ps1 -Personal yourname/dev-env` (or
`bootstrap.sh --personal yourname/dev-env` on Mac). It's saved in
`~/.ws-dev-env.json` together with `-Root`/`--root`, so a re-run needs no
arguments.

## What never goes here

Secrets, tokens, `.env` files and SSH keys. Every computer logs in on its own
and gets its own SSH key. Passwords and keys are shared with `wsg secret`.

`~/.claude/settings.json` is also personal: that's where the permissions for
this particular computer live.

## Switching computers

1. Old computer: `check.ps1` (Windows only). Yellow is lost if the computer is
   wiped, blue is reminders. Only move on once it says "Nothing lost".
2. New computer: `INSTALL-FOR-CLAUDE.md`, or clone and run `bootstrap.ps1`
   (Windows) or `bootstrap.sh` (Mac).
3. SSH: add the new computer's public key to the servers from the old one,
   then remove the old one's.
