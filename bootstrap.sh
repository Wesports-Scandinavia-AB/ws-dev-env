#!/usr/bin/env bash
# Sets up a Mac for WeSports development, or brings one up to date.
# Safe to re-run: personal files are preserved; shared rules are refreshed.
# The Windows version is
# bootstrap.ps1; both read the same packages.json, repos.txt and claude/.
#
#   bash bootstrap.sh
#   bash bootstrap.sh --personal yourname/dev-env
#   bash bootstrap.sh --dry-run
#
# --root and --personal are remembered in ~/.ws-dev-env.json, so a re-run needs
# no arguments. Secrets and SSH keys are never copied: each computer logs in
# and gets a key of its own.

set -uo pipefail

if [ "$(uname -s)" != "Darwin" ]; then
    echo "bootstrap.sh is for Mac. Windows has bootstrap.ps1; Linux isn't set up yet." >&2
    exit 1
fi

HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

PERSONAL=""
ROOT=""
DRY_RUN=0
while [ $# -gt 0 ]; do
    case "$1" in
        --personal) PERSONAL="$2"; shift 2 ;;
        --root) ROOT="$2"; shift 2 ;;
        --dry-run) DRY_RUN=1; shift ;;
        *) echo "unknown argument: $1" >&2; exit 1 ;;
    esac
done

step() { printf '\n=== %s\n' "$1"; }

act() {
    local what="$1"; shift
    if [ "$DRY_RUN" -eq 1 ]; then printf '   would: %s\n' "$what"; return 0; fi
    printf '   %s\n' "$what"
    "$@"
}

has() { command -v "$1" >/dev/null 2>&1; }

# --- 0. Homebrew and jq, needed before packages.json can even be read --------
step 'Homebrew'
install_homebrew() {
    NONINTERACTIVE=1 /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
}
if ! has brew; then act 'install Homebrew' install_homebrew; fi

for bin in /opt/homebrew/bin/brew /usr/local/bin/brew; do
    [ -x "$bin" ] && eval "$("$bin" shellenv)"
done

. "$HERE/lib.sh"

BREW_PROFILE="$HOME/.zprofile"
touch "$BREW_PROFILE"
if has brew && ! grep -q 'brew shellenv' "$BREW_PROFILE" 2>/dev/null; then
    act "add brew shellenv to $BREW_PROFILE" append_line "$BREW_PROFILE" \
        "eval \"\$($(command -v brew) shellenv)\""
fi
if ! has jq; then act 'brew install jq' brew install jq; fi

[ -n "$ROOT" ] || ROOT="$(dev_env_root)"
[ -n "$ROOT" ] || ROOT="$HOME/source/repos"
[ -n "$PERSONAL" ] || PERSONAL="$(dev_env_personal)"

# Layers: this repo, then the personal one once it is cloned.
layers() {
    echo "$HERE"
    if [ -n "$PERSONAL" ]; then
        local p="$ROOT/${PERSONAL##*/}"
        [ -d "$p" ] && echo "$p"
    fi
}

# --- 1. Programs -------------------------------------------------------------
install_packages() {
    local layer="$1"
    local file="$layer/packages.json"
    [ -f "$file" ] || return 0
    while IFS=$'\t' read -r name id cask; do
        if [ "$cask" = "true" ]; then
            act "brew install --cask $name" brew install --cask "$id"
        else
            act "brew install $name" brew install "$id"
        fi
    done < <(jq -r '.packages[] | select(.brew) | [.name, .brew, (.cask // false)] | @tsv' "$file")
    # Node is installed above. npm packages use their name as the command check.
    while IFS=$'\t' read -r name package; do
        if has "$name"; then echo "   exists: $name"; continue; fi
        act "npm install -g $package" npm install -g "$package" || return 1
    done < <(jq -r '.packages[] | select(.npm) | [.name, .npm] | @tsv' "$file")
}

step 'Programs'
install_packages "$HERE" || exit 1
has pnpm || act 'npm install -g pnpm@9' npm install -g pnpm@9

# --- 2. Git and GitHub --------------------------------------------------------
step 'Git and GitHub'
git config --global user.email >/dev/null || \
    echo "git has no user.email. Set it with: git config --global user.email you@wesportsgroup.com" >&2
git config --global user.name >/dev/null || \
    echo "git has no user.name. Set it with: git config --global user.name 'Your Name'" >&2
gh auth status >/dev/null 2>&1 || \
    act 'gh auth login (a browser window opens)' gh auth login --hostname github.com --git-protocol https --web
act 'gh auth setup-git' gh auth setup-git

# --- 3. Repos ------------------------------------------------------------------
clone() {
    local repo="$1"
    local path="$ROOT/${repo##*/}"
    if [ -d "$path" ]; then echo "   exists: $repo"; return; fi
    act "clone $repo" gh repo clone "$repo" "$path"
}

step "Repos in $ROOT"
act "mkdir $ROOT" mkdir -p "$ROOT"
[ -n "$PERSONAL" ] && clone "$PERSONAL"
while read -r layer; do
    [ "$layer" = "$HERE" ] || install_packages "$layer" || exit 1
    list="$layer/repos.txt"
    if [ -f "$list" ]; then
        while read -r repo; do clone "$repo"; done < <(grep -E '^\s*[^#[:space:]]' "$list")
    fi
done < <(layers)

# --- 4. Shared instructions and Claude skills ---------------------------------
step 'Claude and Codex instructions'
SYNC_ARGS=()
[ "$DRY_RUN" -eq 0 ] || SYNC_ARGS+=(--dry-run)
python3 "$HERE/sync-instructions.py" "${SYNC_ARGS[@]}" || exit 1
CLAUDE_DIR="${CLAUDE_CONFIG_DIR:-$HOME/.claude}"
SKILLS_DIR="$CLAUDE_DIR/skills"
act "mkdir $SKILLS_DIR" mkdir -p "$SKILLS_DIR"

# Personal layers keep their existing Claude-specific imports.
MEMORY="$CLAUDE_DIR/CLAUDE.md"
[ "$DRY_RUN" -eq 1 ] || touch "$MEMORY"
while read -r layer; do
    [ "$layer" != "$HERE" ] || continue
    file="$layer/claude/CLAUDE.md"
    [ -f "$file" ] || continue
    line="@$(import_path "$file")"
    if grep -qF "$line" "$MEMORY" 2>/dev/null; then echo "   imported: $line"; continue; fi
    act "add $line to $MEMORY" append_line "$MEMORY" "$line"
done < <(layers)

# Skills are linked as symlinks. A skill that is already there is left alone.
while read -r layer; do
    dir="$layer/claude/skills"
    [ -d "$dir" ] || continue
    for s in "$dir"/*/; do
        [ -d "$s" ] || continue
        name="$(basename "$s")"
        target="$SKILLS_DIR/$name"
        if [ -e "$target" ]; then echo "   exists: skills/$name"; continue; fi
        act "link skills/$name" ln -s "${s%/}" "$target"
    done
done < <(layers)

# wsg: Microsoft 365, Teams, Arena and one-time secret links, with its own skill.
step 'wsg-cli'
if ! has python3; then
    echo "python3 is missing, so wsg-cli was skipped. Run this script again once it's installed." >&2
else
    if ! python3 -m wsg --version >/dev/null 2>&1; then
        act 'pip install wsg-cli' python3 -m pip install --user --upgrade \
            git+https://github.com/Wesports-Scandinavia-AB/wsg-cli
    else
        echo '   exists: wsg-cli (update it with: wsg update)'
    fi
    # pip --user puts wsg on a Scripts path Homebrew's python does not add to
    # PATH by itself, so the bare 'wsg' the rules and the skill use would not run.
    USER_BIN="$(python3 -c 'import sysconfig; print(sysconfig.get_path("scripts", "posix_user"))')"
    if ! has wsg && [ -d "$USER_BIN" ]; then
        grep -qF "$USER_BIN" "$BREW_PROFILE" 2>/dev/null || \
            act "add $USER_BIN to PATH" append_line "$BREW_PROFILE" "export PATH=\"$USER_BIN:\$PATH\""
        export PATH="$USER_BIN:$PATH"
    fi
    [ -d "$SKILLS_DIR/wsg" ] || act 'wsg skill install' python3 -m wsg skill install
fi

# --- 5. SSH key for this computer ----------------------------------------------
step 'SSH key'
KEY="$HOME/.ssh/id_ed25519"
make_ssh_key() {
    mkdir -p "$HOME/.ssh"
    ssh-keygen -t ed25519 -f "$KEY" -N '' -C "$(whoami)@$(scutil --get LocalHostName 2>/dev/null || hostname)"
}
if [ -f "$KEY" ]; then
    echo "   exists: $KEY"
else
    act "ssh-keygen $KEY" make_ssh_key
fi
if [ -f "$KEY.pub" ]; then
    echo "   public key, safe to send to whoever adds it on a server:"
    echo "   $(cat "$KEY.pub")"
fi

# --- 6. Done ---------------------------------------------------------------------
[ "$DRY_RUN" -eq 1 ] || save_dev_env_config "$ROOT" "$PERSONAL"

step 'Installed'
for cmd in git gh node pnpm python3 wsg code claude codex herdr; do
    if has "$cmd"; then echo "   OK       $cmd"; else echo "   MISSING  $cmd  (open a new terminal and run again)"; fi
done
printf "\nNext: run 'claude' or 'codex' and log in to the corresponding account, then 'wsg graph login'.\n"
