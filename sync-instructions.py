"""Copy shared guidance and register it without replacing personal instructions."""
import argparse
import os
from pathlib import Path
import shutil
import tempfile

ROOT = Path(__file__).resolve().parent
NAME = "AGENTS.WeSports.md"


def read(path):
    return path.read_bytes().decode("utf-8") if path.exists() else ""


def reference(text, line, obsolete=()):
    # Remove only the exact import previously installed by this checkout.
    text = "".join(part for part in text.splitlines(keepends=True)
                   if part.rstrip("\r\n") not in obsolete)
    if line in text.splitlines():
        return text
    newline = "\r\n" if "\r\n" in text else "\n"
    return text + (newline if text and not text.endswith("\n") else "") + line + newline


def sync(claude_dir, codex_dir, dry_run=False):
    shared = read(ROOT / NAME)
    if not shared.strip():
        raise ValueError("Shared instructions are empty")
    legacy = (ROOT / "claude" / "CLAUDE.md").as_posix()
    aliases = {legacy}
    try:
        aliases.add("~/" + (ROOT / "claude" / "CLAUDE.md").relative_to(Path.home()).as_posix())
    except ValueError:
        pass
    obsolete = {"@" + p for p in aliases} | {"@" + p.replace(" ", "\\ ") for p in aliases}
    codex_ref = ("Before starting any task, read and follow the shared WeSports instructions in "
                 "`" + (codex_dir / NAME).absolute().as_posix() + "`.")
    # Preflight all targets before writing any file. Never write through links.
    paths = [claude_dir / NAME, claude_dir / "CLAUDE.md",
             codex_dir / NAME, codex_dir / "AGENTS.md"]
    for path in paths:
        if path.is_symlink() or (path.exists() and not path.is_file()):
            raise ValueError(f"Cannot synchronize linked or non-file target: {path}")
    updates = [shared, reference(read(paths[1]), "@" + NAME, obsolete),
               shared, reference(read(paths[3]), codex_ref)]
    for path, content in zip(paths, updates):
        if path.exists() and read(path) == content:
            print(f"unchanged: {path}")
            continue
        print(f"{'would update' if dry_run else 'update'}: {path}")
        if dry_run:
            continue
        path.parent.mkdir(parents=True, exist_ok=True)
        if path.exists():
            # Keep the original once, without following or replacing a backup link.
            backup = path.with_name(path.name + ".ws-dev-env.bak")
            try:
                with backup.open("xb") as dest:
                    dest.write(path.read_bytes())
            except FileExistsError:
                pass
        fd, temporary = tempfile.mkstemp(dir=path.parent, prefix=".ws-dev-env-")
        try:
            with os.fdopen(fd, "wb") as dest:
                dest.write(content.encode("utf-8"))
            if path.exists():
                shutil.copymode(path, temporary)
            os.replace(temporary, path)
        finally:
            if os.path.exists(temporary):
                os.unlink(temporary)
    override = codex_dir / "AGENTS.override.md"
    if override.exists() and read(override).strip():
        print(f"WARNING: {override} overrides AGENTS.md; add the WeSports reference there manually.")
    print("Start a new Claude/Codex session to load the updated instructions.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--claude-dir", type=Path,
                        default=Path(os.environ.get("CLAUDE_CONFIG_DIR") or Path.home() / ".claude"))
    parser.add_argument("--codex-dir", type=Path,
                        default=Path(os.environ.get("CODEX_HOME") or Path.home() / ".codex"))
    args = parser.parse_args()
    try:
        sync(args.claude_dir.expanduser().absolute(), args.codex_dir.expanduser().absolute(), args.dry_run)
    except (OSError, ValueError) as error:
        parser.exit(1, f"Instruction sync failed: {error}\n")
