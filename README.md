# ws-dev-env

A WeSports developer computer, described in one repo: which programs, which
repos, and which shared Claude rules and skills Claude should set up. A new
computer becomes a clone and a script, and whatever someone adds reaches
everyone with `git pull`.

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
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"; eval "$([ -x /opt/homebrew/bin/brew ] && /opt/homebrew/bin/brew shellenv || /usr/local/bin/brew shellenv)"; brew install git gh herdr; brew install --cask claude-code; claude "This is my NEW Mac. Log me in to GitHub, clone Wesports-Scandinavia-AB/ws-dev-env to ~/source/repos/ws-dev-env and follow INSTALL-FOR-CLAUDE.md in the repo. I'm not a developer: run everything yourself and never ask me to paste commands."
```

The first time Claude starts, you log in to your Claude account.

## Contents

```
bootstrap.ps1   Windows: new computer, or bring an existing one up to date; safe to re-run
bootstrap.sh    Mac: the same, via Homebrew instead of winget
check.ps1       Windows, before leaving a computer: lists what only exists on it
packages.json   programs, shared between Windows and Mac: one name, one winget id, one brew id
repos.txt       repos everyone clones
claude/
  CLAUDE.md     shared rules, imported into everyone's ~/.claude/CLAUDE.md
  skills/       skills everyone gets, linked into ~/.claude/skills
```

A package in `packages.json` with no `brew` id is skipped on Mac
(`windows-terminal`, Windows only). A package with no `winget` id would be
skipped on Windows the same way, but none exists yet. There's no `check.sh`
for Mac: `check.ps1` is still Windows only.

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
