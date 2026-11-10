"""Preview or explicitly update the tools declared in ws-dev-env's package channels."""
import argparse
import json
import os
from pathlib import Path
import platform
import shutil
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
# Official winget HRESULTs, normalized for signed/unsigned process return codes.
NO_UPGRADE = 0x8A15002B
NOT_INSTALLED = 0x8A150014


def packages(layers):
    result = {}
    for layer in layers:
        manifest = layer / 'packages.json'
        if not manifest.is_file():
            continue
        for item in json.loads(manifest.read_text(encoding='utf-8-sig'))['packages']:
            if item['name'] in result and result[item['name']] != item:
                raise ValueError(f'Conflicting tool declarations: {item["name"]}')
            result[item['name']] = item
    return list(result.values())


def layers(home):
    result = [ROOT]
    file = home / '.ws-dev-env.json'
    if file.is_file():
        config = json.loads(file.read_text(encoding='utf-8-sig'))
        if config.get('personal'):
            personal = Path(config.get('root') or home / 'source' / 'repos') / config['personal'].split('/')[-1]
            if not personal.is_dir():
                raise ValueError('Configured personal layer is missing. Update its clone before continuing.')
            result.append(personal)
    return result


def execute(command, allowed=()):
    result = subprocess.run(command, check=False)
    code = result.returncode & 0xFFFFFFFF
    if code and code not in allowed:
        raise RuntimeError(f'Update command failed ({result.returncode}): {command[0]}')
    return code


def update(items, system, apply=False, runner=execute):
    if system not in ('Windows', 'Darwin'):
        raise ValueError('Tool updates support Windows and Mac only.')
    npm = 'npm.cmd' if system == 'Windows' else 'npm'
    if apply:
        needed = ['winget' if system == 'Windows' else 'brew', npm]
        missing = [tool for tool in needed if shutil.which(tool) is None]
        if missing:
            raise ValueError('Run bootstrap first; missing: ' + ', '.join(missing))
    if system == 'Darwin':
        print('brew update')
        if apply:
            runner(['brew', 'update'])
    for item in items:
        if system == 'Windows' and item.get('winget'):
            flags = ['--id', item['winget'], '--exact', '--accept-source-agreements',
                     '--accept-package-agreements', '--disable-interactivity']
            print('winget upgrade ' + ' '.join(flags))
            if apply:
                code = runner(['winget', 'upgrade', *flags], (NO_UPGRADE, NOT_INSTALLED))
                if code == NOT_INSTALLED:
                    runner(['winget', 'install', *flags], (NO_UPGRADE,))
        if system == 'Darwin' and item.get('brew'):
            kind = '--cask' if item.get('cask') else '--formula'
            print(f'brew upgrade {kind} {item["brew"]} (install if absent)')
            if apply:
                installed = runner(['brew', 'list', '--versions', kind, item['brew']], (1,)) == 0
                runner(['brew', 'upgrade' if installed else 'install', kind, item['brew']])
        if item.get('npm'):
            # npm install resolves the current release in the declared package/channel.
            print(f'{npm} install --global {item["npm"]}')
            if apply:
                runner([npm, 'install', '--global', item['npm']])
    # Keep pnpm's project-compatible major, rather than changing existing lockfile semantics.
    print(f'{npm} install --global pnpm@9')
    print(f'{sys.executable} -m wsg update')
    if apply:
        runner([npm, 'install', '--global', 'pnpm@9'])
        runner([sys.executable, '-m', 'wsg', 'update'])
    print('Tool update completed.' if apply else 'Preview only. Run with --apply to update these tools.')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--apply', action='store_true', help='Update the listed tools; otherwise only preview.')
    args = parser.parse_args()
    try:
        update(packages(layers(Path.home())), platform.system(), args.apply)
    except (OSError, ValueError, RuntimeError) as exc:
        parser.exit(1, f'{exc}\nNo claim that every tool is current can be made. Resolve the failure and rerun.\n')


if __name__ == '__main__':
    main()
