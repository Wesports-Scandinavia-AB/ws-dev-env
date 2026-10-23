"""Install every shared/personal skill for every configured local coding agent."""
import argparse
import json
import os
from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parent


def targets(layers, home):
    result = set()
    for layer in layers:
        manifest = layer / "packages.json"
        if not manifest.is_file():
            continue
        for package in json.loads(manifest.read_text(encoding="utf-8-sig"))["packages"]:
            location = package.get("skill_dir")
            if not location:
                continue
            override = os.environ.get(package.get("skill_config_env", ""))
            result.add((Path(override).expanduser() / "skills" if override
                        else home / location).absolute())
    return sorted(result)


def sources(layers):
    result = {}
    for layer in layers:
        # Keep the established source layout compatible with personal repos.
        directory = layer / "claude" / "skills"
        if not directory.is_dir():
            continue
        for skill in sorted(directory.iterdir()):
            if skill.name.startswith(".") or not skill.is_dir():
                continue
            if not (skill / "SKILL.md").is_file():
                raise ValueError(f"Skill is missing SKILL.md: {skill}")
            key = skill.name.casefold()
            if key in result and result[key] != skill.resolve():
                raise ValueError(f"Duplicate skill name in environment layers: {skill.name}")
            result[key] = skill.resolve()
    return list(result.values())


def linked(path):
    return path.is_symlink() or path.is_junction()


def link_directory(source, target):
    if os.name == "nt":
        # CPython 3.12 (installed by bootstrap): junctions need no admin rights.
        import _winapi
        _winapi.CreateJunction(str(source), str(target))
    else:
        target.symlink_to(source, target_is_directory=True)


def sync(layers, home, dry_run=False, with_wsg=False):
    destinations = targets(layers, home)
    if not destinations:
        raise ValueError("No skill_dir targets configured in packages.json")
    skills = sources(layers)
    if with_wsg and any(skill.name.casefold() == "wsg" for skill in skills):
        raise ValueError("wsg is provided by wsg-cli; remove the duplicate from the environment layer")
    pending = []
    # Preflight every target to avoid silently leaving agents with different skills.
    for directory in destinations:
        for skill in skills:
            target = directory / skill.name
            if linked(target) and target.resolve() == skill:
                print(f"linked: {target}")
            elif os.path.lexists(target):
                raise ValueError(f"Skill conflict at {target}; expected a link to {skill}. "
                                 "Move or rename the existing skill, then rerun; it was not overwritten.")
            else:
                pending.append((skill, target))
        if with_wsg:
            target = directory / "wsg"
            skill_file = target / "SKILL.md"
            if linked(target) or linked(skill_file) or (target.exists() and not target.is_dir()):
                raise ValueError(f"Cannot update wsg skill through linked or non-directory target: {target}")
    for source, target in pending:
        print(f"{'would link' if dry_run else 'link'}: {target} -> {source}")
        if not dry_run:
            target.parent.mkdir(parents=True, exist_ok=True)
            link_directory(source, target)
    if with_wsg:
        for directory in destinations:
            print(f"{'would refresh' if dry_run else 'refresh'}: {directory / 'wsg'}")
            if not dry_run:
                subprocess.run([sys.executable, "-m", "wsg", "skill", "install",
                                "--dir", str(directory / "wsg")], check=True)
    print(f"Skills synchronized for {len(destinations)} agent locations. Start a new agent session.")


def configured_layers(root, home, extra_layers):
    result = [root]
    config_file = home / ".ws-dev-env.json"
    if not extra_layers and config_file.is_file():
        config = json.loads(config_file.read_text(encoding="utf-8-sig"))
        if config.get("personal"):
            extra_layers = [Path(config.get("root") or home / "source" / "repos") /
                            config["personal"].split("/")[-1]]
    for layer in extra_layers:
        layer = layer.expanduser().resolve()
        if not layer.is_dir():
            raise ValueError(f"Personal environment layer is missing: {layer}")
        if layer not in result:
            result.append(layer)
    return result


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--layer", action="append", type=Path, default=[],
                        help="Additional environment layer (otherwise read ~/.ws-dev-env.json)")
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--with-wsg", action="store_true", help="Refresh wsg-cli's skill for every agent")
    args = parser.parse_args()
    try:
        sync(configured_layers(ROOT, Path.home(), args.layer), Path.home(), args.dry_run, args.with_wsg)
    except (OSError, ValueError, subprocess.CalledProcessError) as error:
        parser.exit(1, f"Skill synchronization failed: {error}\n")
