# ws-dev-env

<!-- latest-version:start -->
## Latest version: 0.1.0 (Unreleased)

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

[Full changelog](CHANGELOG.md)
<!-- latest-version:end -->

A WeSports developer computer, described in one repo: which programs, which
repos, shared Claude/Codex instructions and skills to set up. A new
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
sync-skills.py  install shared/personal skills for every configured coding agent
claude/
  CLAUDE.md     compatibility import for older installations
  skills/       shared source bundles, linked into every coding agent's skill directory
```

## Maintaining version history

Record each change in `CHANGELOG.md` under the current unreleased version,
then run `python scripts/update-readme.py` (`python3` on Mac). This generates
the latest-version section above. Before publishing a version, replace
`Unreleased` with its release date; begin a new version for subsequent work.
Use PATCH for fixes, MINOR for compatible additions and MAJOR for breaking
changes. Publishing tags is a separate release action.

The repository's `AGENTS.md` and `CLAUDE.md` require this workflow. GitHub
Actions checks that each push or pull request changes the changelog and that
the README matches it. These checks report failures; enforcing them before
merge also requires branch protection. Run the consistency check locally with
`python scripts/update-readme.py --check`.

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
older installations. Skills are shared across local coding agents as described below.

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

## Shared skills for local coding agents

Use `make-change` when you want help changing an app or tool without needing
to know how it is built. Ask the agent to use the skill and describe what you
want to do. It inspects the project, asks focused questions when needed,
implements the change and explains how to try it. It then pushes a feature
branch, opens a PR, starts review and addresses review and CI feedback until
the PR is ready to merge or needs external input. Merging is a separate
authorized action. Clear, small requests do not require an interview. The
skill works in both Claude Code and Codex.

Bootstrap installs every bundle under `claude/skills/` in both the shared and
personal environment layers for every package with a `skill_dir` entry.
The source directory retains its old name for compatibility; it is shared
by all agents. Supporting scripts and reference files are included.

| Package | User skill directory |
| --- | --- |
| Claude Code | `~/.claude/skills` (or `$CLAUDE_CONFIG_DIR/skills`) |
| Codex | `~/.agents/skills` |

Codex's user skill directory is separate from `CODEX_HOME`, which controls
its configuration and instruction files. See [OpenAI's skill locations](https://learn.chatgpt.com/docs/build-skills)
and [Claude's skill locations](https://code.claude.com/docs/en/skills).

On Windows, skills use directory junctions without requiring Administrator
or Developer Mode. On Mac, they use symlinks. Existing links to the correct
source are reused, and source updates become available through those links.
New skills are linked on the next sync. A duplicate name across layers, an
existing unrelated skill or an outdated link causes an explicit error;
resolve the conflict and rerun. Personal files are never silently replaced.
Removing a source bundle does not automatically remove its installed link.

Bootstrap also refreshes the `wsg` skill from the installed wsg-cli package
in every agent directory, including on repeat runs. These generated `wsg/SKILL.md`
files are overwritten with the package version; edit the source package to
change them. Other files in those directories are preserved.

To synchronize skills only (after installing wsg-cli):

```powershell
python sync-skills.py --with-wsg --dry-run
python sync-skills.py --with-wsg
```

Use `python3` on Mac. The personal layer is read from `~/.ws-dev-env.json`,
or supplied explicitly with `--layer <path>`. Restart the agent to pick up
new skills. To add another local coding agent, add `skill_dir` (relative to
the user's home) to its package entry. Optionally set `skill_config_env` to
an environment variable whose directory contains `skills/`.

This installs local coding-agent skills. Claude Desktop's Cowork and cloud
sessions use account-managed skills and do not load these local folders;
they need separate account configuration. Terminals such as Herdr and
Ghostty use the skills of the coding agent running inside them.

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

Secrets, tokens, real `.env`/`.dev.vars` files and SSH private keys. In project
repositories, keep required variable names and setup steps in documentation
and placeholder values in `.env.example` or `.dev.vars.example`. Ignore the
real local files in that project's `.gitignore`; this repository's `.gitignore`
shows the pattern. Bootstrap also adds these patterns to Git's global excludes
file so they are ignored across repositories; `.hidden` is globally ignored as
well. If `core.excludesFile` is already configured, bootstrap appends a marked
block without replacing its contents; otherwise it configures
`~/.ws-dev-env-gitignore`. Each computer logs in on its own and gets its own SSH
key. Transfer secrets between computers with `wsg secret` when needed.

`~/.claude/settings.json` is also personal: that's where the permissions for
this particular computer live.

## Switching computers

1. Old computer: `check.ps1` (Windows only). Yellow is lost if the computer is
   wiped, blue is reminders. Only move on once it says "Nothing lost".
2. New computer: `INSTALL-FOR-CLAUDE.md`, or clone and run `bootstrap.ps1`
   (Windows) or `bootstrap.sh` (Mac).
3. SSH: add the new computer's public key to the servers from the old one,
   then remove the old one's.
