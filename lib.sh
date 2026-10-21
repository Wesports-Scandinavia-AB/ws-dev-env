# Shared by bootstrap.sh. Mirrors lib.ps1 for the Windows side; same
# ~/.ws-dev-env.json file and schema, read here with jq instead of
# ConvertFrom-Json.

DEV_ENV_CONFIG_PATH="$HOME/.ws-dev-env.json"

dev_env_root() {
    [ -f "$DEV_ENV_CONFIG_PATH" ] && jq -r '.root // empty' "$DEV_ENV_CONFIG_PATH"
}

dev_env_personal() {
    [ -f "$DEV_ENV_CONFIG_PATH" ] && jq -r '.personal // empty' "$DEV_ENV_CONFIG_PATH"
}

save_dev_env_config() {
    local root="$1" personal="$2"
    jq -n --arg root "$root" --arg personal "$personal" '{root: $root, personal: $personal}' \
        > "$DEV_ENV_CONFIG_PATH"
}

append_line() { printf '%s\n' "$2" >> "$1"; }

# Claude's @import takes ~/... or an absolute path with forward slashes, which
# a POSIX path already is; only the $HOME prefix needs folding to ~.
import_path() {
    local full
    full="$(cd "$(dirname "$1")" && pwd)/$(basename "$1")"
    case "$full" in
        "$HOME"/*) echo "~${full#"$HOME"}" ;;
        *) echo "$full" ;;
    esac
}
