# Instructions for Claude: set up a development computer with ws-dev-env

This file is written for you, Claude, rather than the person you are helping.
Someone has shared this link to set up their computer for development at
WeSports or to move from an old computer.

Follow the steps in order and briefly explain what is happening. The person
may not be a developer: use plain language and ask before committing,
pushing or deleting anything.

**Run every command yourself.** Never ask the person to paste anything into
PowerShell or a terminal, or to open a new terminal. They should only need
to read, sign in through their browser and answer questions. If a newly
installed program is not found, refresh PATH in your own command session:

```
$env:Path = [Environment]::GetEnvironmentVariable('Path','Machine') + ';' + [Environment]::GetEnvironmentVariable('Path','User')
```

## 0. Prerequisites

You must be able to run commands on the person's computer, for example through
Claude Code. If you cannot, explain that and stop.

**Never ask for passwords, codes or tokens in chat.** Sign-in happens in the
person's own browser.

This setup supports Windows and Mac. On Linux, explain that and stop.

## 1. Which platform, and is this the old or new computer?

Run `uname` (Mac/Linux returns `Darwin`/`Linux`) or check `$env:OS` on Windows
if the platform is not already clear. On Linux, explain that and stop.

Then ask whether this is the computer the person is **leaving** or the **new**
one. Steps 2 and 3 apply to both. For the old computer, skip step 4 and go to
"The old computer" below. That section currently only has an automated
Windows check (`check.ps1`); see its note about Mac.

## 2. git and GitHub

**Windows:**

```
winget install --id Git.Git -e --accept-package-agreements --accept-source-agreements
winget install --id GitHub.cli -e --accept-package-agreements --accept-source-agreements
```

The initial command in the README usually already installed these; winget
will skip them in that case. Refresh PATH again (see above).

**Mac:**

```
brew install git gh
```

If Homebrew is missing, install it first:
`NONINTERACTIVE=1 /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"`,
then load it into your own session with
`eval "$([ -x /opt/homebrew/bin/brew ] && /opt/homebrew/bin/brew shellenv || /usr/local/bin/brew shellenv)"`.

**Both:** run `gh auth login --hostname github.com --git-protocol https --web`
in the background, give the person the one-time code and URL as text, and
wait until they have signed in. They need access to the
`Wesports-Scandinavia-AB` organization.

## 3. Clone ws-dev-env

**Windows:**

```
gh repo clone Wesports-Scandinavia-AB/ws-dev-env "$HOME\source\repos\ws-dev-env"
```

**Mac:**

```
gh repo clone Wesports-Scandinavia-AB/ws-dev-env "$HOME/source/repos/ws-dev-env"
```

If the person wants repositories elsewhere, clone there and pass
`-Root`/`--root` in the next step.

## 4. Run bootstrap

First show what will happen:

**Windows:**

```
powershell -ExecutionPolicy Bypass -File "$HOME\source\repos\ws-dev-env\bootstrap.ps1" -DryRun
```

**Mac:**

```
bash "$HOME/source/repos/ws-dev-env/bootstrap.sh" --dry-run
```

If the person has a personal layer (a private repository with the same layout:
`packages.json`, `repos.txt`, `claude/CLAUDE.md`, `claude/skills/`), add
`-Personal owner/repo` (Windows) or `--personal owner/repo` (Mac). Then run
without `-DryRun`/`--dry-run`.

The script installs programs, clones repositories, distributes shared
instructions through `AGENTS.WeSports.md` for Claude and Codex, links Claude
skills, installs `wsg`, and creates an SSH key for the computer if missing.
Personal instructions are preserved; the shared instruction copy is refreshed.
The script can be run again. On Mac, Homebrew and `jq` are installed as part
of this step if missing; `bootstrap.sh` itself needs them, rather than the
list in `packages.json`.

If git has no name or email configured, the script warns. Ask the person and
set those values.

## 5. Sign-ins

Each computer signs in separately; nothing is copied:

- **Codex CLI** is also installed by bootstrap. When the person wants to use
  Codex, start `codex` and let them sign in with their own account. This is
  the terminal tool, not the desktop app. Bootstrap copies AGENTS.WeSports.md
  to both tools' configuration directories and adds a reference in their
  global instruction files. Skills are still installed for Claude only.
- **wsg**: run `python -m wsg graph login` (Windows) or `python3 -m wsg graph login`
  (Mac) in the background and give the person the URL. The script added `wsg`
  to PATH, but your session started before that, so the full form works
  immediately. In the person's new terminal, the command is simply `wsg`.
- **SSH**: the script printed the public key. It is only needed to deploy
  `wesports-data`. Unless the person asks about that, say the key is available
  and leave it there. If they need to deploy `wesports-data`, add the key to
  that server, preferably from the old computer (see the `ws-dev-env` skill).
- **Cloudflare**, when needed: run `npx wrangler login` in the repository that
  uses it.

## 6. Done

Run `pnpm install` in repositories containing `package.json`. Then explain
what was installed, what remains (sign-ins, and the SSH key on the server if
the person needs to deploy `wesports-data`), and that asking to "update the
development environment" is enough to get additions made by others.

## The old computer

Do not install anything in this section. The goal is to avoid losing anything
when the computer is handed over.

1. Run the check. If repositories are not under `~/source/repos`, pass `-Root`:

   ```
   powershell -ExecutionPolicy Bypass -File "$HOME\source\repos\ws-dev-env\check.ps1"
   ```

   This automated check is Windows-only (`check.ps1`). If the old computer is
   a Mac, perform the same checks manually: run `git status` and
   `git log --branches --not --remotes` in each repository under `~/source/repos`,
   look for `.env`/`.pem`/`.key` files ignored by git, and note the SSH key
   in `~/.ssh`.

2. Review the **yellow** items with the person, one at a time, explaining each:
   - **Not committed / not pushed**: show the changes and ask whether to save
     them. If yes, commit and push on a separate branch and name the branch.
   - **Files that look like secrets** (`.env`, `.dev.vars`): do not transfer them
     through git, OneDrive or email. Send them to the person using
     `python -m wsg secret`, a one-time link, and ask them to open it on the new
     computer. If wsg is missing, install it following
     https://github.com/Wesports-Scandinavia-AB/wsg-cli/blob/main/INSTALL-FOR-CLAUDE.md
   - **Folders without git or a remote**: ask whether they are needed. If so,
     put them in a private GitHub repository, or in OneDrive if they contain
     no secrets.
3. Run the check again until it reports **"Nothing lost"**. Only then say the
   computer can be handed over.
4. The **blue** items are reminders. Per-project Claude memory can be copied to
   `~/.claude/projects` on the new computer if the person wants. Do not transfer
   SSH keys; see the next step.
5. **SSH**: once the new computer has a key (bootstrap prints the public part)
   and the person provides that line, add it to the servers from the old
   computer using the old key:

   ```
   ssh <user>@<server> "echo '<public key>' >> ~/.ssh/authorized_keys"
   ```

   Find the user and server in `~/.ssh/config` or `~/.ssh/known_hosts`, or ask
   if necessary. Have the person test access from the new computer, then remove
   the old computer's entry from `authorized_keys` on the server.
