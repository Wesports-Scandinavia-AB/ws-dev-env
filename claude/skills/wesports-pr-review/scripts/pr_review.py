#!/usr/bin/env python3
"""Portable PR inventory, local receipts and cross-machine Git leases. Python 3.10+."""
from __future__ import annotations

import argparse
from datetime import datetime, timedelta, timezone
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys
import tempfile
import uuid
from urllib.parse import quote

PREFIX = 'refs/pr-review/claims/'
MAX_FIX_ROUNDS = 3


class ReviewError(Exception):
    pass


class Busy(ReviewError):
    pass


def run(args, *, cwd=None, stdin=None, timeout=90):
    environment = os.environ.copy()
    if str(args[0]) == 'git':
        environment.update(GIT_TERMINAL_PROMPT='0', GCM_INTERACTIVE='never',
                           GIT_HTTP_LOW_SPEED_LIMIT='1', GIT_HTTP_LOW_SPEED_TIME='30')
    try:
        result = subprocess.run(
            [str(x) for x in args], cwd=cwd, input=stdin, text=True,
            encoding='utf-8', errors='replace', capture_output=True, timeout=timeout, env=environment,
        )
    except (OSError, subprocess.TimeoutExpired) as exc:
        raise ReviewError(f'Could not run {args[0]}. Check installation and connectivity.') from exc
    if result.returncode:
        # Raw process output may contain credential-bearing URLs. Keep it off stdout.
        raise ReviewError(f'{args[0]} failed (exit {result.returncode}). No action is verified.')
    return result.stdout.strip()


def git(checkout, *args, stdin=None):
    return run(['git', '-c', 'credential.helper=',
                '-c', 'credential.https://github.com.helper=!gh auth git-credential',
                '-C', checkout, *args], stdin=stdin)


def repo_name(value):
    if not re.fullmatch(r'[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+', value):
        raise argparse.ArgumentTypeError('Specify the repository as owner/repo.')
    return value


def sha(value):
    if not re.fullmatch(r'[0-9a-f]{40}|[0-9a-f]{64}', value):
        raise argparse.ArgumentTypeError('A full commit SHA is required.')
    return value


def token(value):
    if not re.fullmatch(r'[a-zA-Z0-9_-]{8,80}', value):
        raise argparse.ArgumentTypeError('Session IDs must contain 8-80 letters, digits, hyphens or underscores.')
    return value


def positive(value):
    number = int(value)
    if number < 1:
        raise argparse.ArgumentTypeError('The PR number must be positive.')
    return number


def now():
    return datetime.now(timezone.utc)


def iso(value):
    return value.isoformat().replace('+00:00', 'Z')


def pages(endpoint):
    raw = json.loads(run(['gh', 'api', '--paginate', '--slurp', endpoint]))
    if not isinstance(raw, list) or any(not isinstance(page, list) for page in raw):
        raise ReviewError('GitHub returned an unexpected response. The queue cannot be verified.')
    return [item for page in raw for item in page]


def inventory(repos):
    rows = []
    for repo in dict.fromkeys(repos):
        items = pages(f'repos/{repo}/pulls?state=open&sort=created&direction=asc&per_page=100')
        for item in items:
            rows.append({
                'repo': repo, 'number': item['number'], 'title': item['title'],
                'url': item['html_url'], 'author': (item.get('user') or {}).get('login'),
                'createdAt': item['created_at'], 'updatedAt': item['updated_at'],
                'isDraft': item.get('draft', False), 'headRefOid': item['head']['sha'],
                'headRefName': item['head']['ref'], 'baseRefName': item['base']['ref'],
                'headRepo': (item['head'].get('repo') or {}).get('full_name'),
                'baseRepo': item['base']['repo']['full_name'],
            })
    return {'fetchedAt': iso(now()), 'pulls': sorted(rows, key=lambda x: (x['createdAt'], x['repo'].lower(), x['number']))}


def version(repo, pr, expected_head=None, expected_base=None, expected_branch=None):
    pull = json.loads(run(['gh', 'api', f'repos/{repo}/pulls/{pr}']))
    base_repo = repo_name(pull['base']['repo']['full_name'])
    branch = pull['base']['ref']
    current_base = json.loads(run(['gh', 'api', f'repos/{base_repo}/commits/{quote(branch, safe="")}']))
    result = {'repo': repo, 'number': pr, 'head': sha(pull['head']['sha']),
              'base': sha(current_base['sha']), 'baseBranch': branch,
              'state': pull['state'], 'isDraft': pull.get('draft', False)}
    if expected_head is not None or expected_base is not None or expected_branch is not None:
        if expected_head is None or expected_base is None:
            raise ReviewError('Both --expect-head and --expect-base are required for verification.')
        if result['state'] != 'open' or result['isDraft']:
            raise Busy('The PR is no longer open and ready. Do not publish, push or merge.')
        if result['head'] != expected_head or result['base'] != expected_base:
            raise Busy('The PR head or target branch changed. Refresh review, integration checks and CI before proceeding.')
        if expected_branch is not None and result['baseBranch'] != expected_branch:
            raise Busy('The PR target branch was changed. Reassess review scope and deployment consequences before proceeding.')
    return result


def events(repo, pr):
    result = []
    for kind, endpoint in [
        ('comment', f'issues/{pr}/comments'),
        ('review', f'pulls/{pr}/reviews'),
        ('inline', f'pulls/{pr}/comments'),
    ]:
        for item in pages(f'repos/{repo}/{endpoint}?per_page=100'):
            result.append({
                'key': f"{kind}:{item['id']}:{item.get('updated_at') or item.get('submitted_at') or item.get('created_at')}",
                'author': (item.get('user') or {}).get('login'),
                'url': item.get('html_url'),
            })
    return {'events': result}


def remote_slug(url):
    match = re.fullmatch(r'(?:https://github\.com/|ssh://git@github\.com/|git@github\.com:)([^/]+/[^/]+?)(?:\.git)?/?', url)
    return match.group(1).lower() if match else None


def check_checkout(checkout, repo):
    root = git(checkout, 'rev-parse', '--show-toplevel')
    # Reads and pushes must reach the same repository, including a configured pushurl.
    fetch_urls = git(checkout, 'remote', 'get-url', '--all', 'origin').splitlines()
    push_urls = git(checkout, 'remote', 'get-url', '--push', '--all', 'origin').splitlines()
    if len(fetch_urls) != 1 or len(push_urls) != 1 or any(remote_slug(url) != repo.lower() for url in fetch_urls + push_urls):
        raise ReviewError('The clone origin does not unambiguously match the selected GitHub repository. Use a separate clone of the correct repository.')
    return root


def doctor(repo, checkout=None):
    missing = [tool for tool in ('git', 'gh') if shutil.which(tool) is None]
    if missing:
        raise ReviewError('Missing tools: ' + ', '.join(missing) + '. Install them before reviewing.')
    identity = json.loads(run(['gh', 'api', 'user']))['login']
    info = json.loads(run(['gh', 'api', f'repos/{repo}']))
    root = check_checkout(checkout, repo) if checkout else None
    return {'repo': info['full_name'], 'user': identity, 'permissions': info.get('permissions', {}), 'checkout': root}


class Lease:
    """Cooperative lease, stored in a custom remote ref; every mutation uses exact-OID CAS."""
    def __init__(self, checkout, pr):
        self.checkout = str(checkout)
        if str(pr) != 'merge-deploy' and not re.fullmatch(r'[1-9][0-9]*', str(pr)):
            raise ReviewError('Claims must target a PR number or merge-deploy.')
        self.ref = PREFIX + str(pr)

    def read(self):
        line = git(self.checkout, 'ls-remote', 'origin', self.ref)
        if not line:
            return None, None
        observed = 'refs/pr-review/observed/' + uuid.uuid4().hex
        try:
            git(self.checkout, 'fetch', '--no-write-fetch-head', 'origin', f'+{self.ref}:{observed}')
            oid = git(self.checkout, 'rev-parse', observed)
            message = git(self.checkout, 'show', '-s', '--format=%B', oid)
            record = json.loads(message)
            if not isinstance(record, dict) or record.get('protocol') != 1:
                raise ValueError('Unknown lease protocol')
            token(record['session'])
            sha(record['head'])
            if not isinstance(record['expiresAt'], str):
                raise ValueError('Invalid expiration type')
            expires = datetime.fromisoformat(record['expiresAt'].replace('Z', '+00:00'))
            if expires.tzinfo is None:
                raise ValueError('Missing time zone')
            return oid, record
        except (ValueError, KeyError, TypeError, argparse.ArgumentTypeError) as exc:
            raise ReviewError('The shared claim cannot be read. Do not take it over automatically.') from exc
        finally:
            git(self.checkout, 'update-ref', '-d', observed)

    def write(self, expected, record):
        if record is None:
            source = ''
        else:
            tree = git(self.checkout, 'mktree', stdin='')
            source = git(self.checkout, '-c', 'user.name=PR Review', '-c', 'user.email=pr-review@invalid',
                         'commit-tree', tree, stdin=json.dumps(record, ensure_ascii=False))
        # Empty expected means create only if absent. Explicit OID prevents stealing a renewed lease.
        git(self.checkout, 'push', '--porcelain', f'--force-with-lease={self.ref}:{expected or ""}',
            'origin', f'{source}:{self.ref}')
        return source

    def act(self, action, session, head=None, owner=None, ttl=3600):
        oid, record = self.read()
        active = record is not None and datetime.fromisoformat(record['expiresAt'].replace('Z', '+00:00')) > now()
        mine = record is not None and record['session'] == session
        if action == 'take':
            if active and not mine:
                raise Busy(f"The resource is held by {record.get('owner', 'another session')} until {record['expiresAt']}.")
        elif action in ('check', 'renew'):
            if not mine or not active:
                raise Busy('The claim is no longer yours or has expired. Do not publish, push or merge.')
        elif action == 'free':
            if record is None:
                return {'status': 'already-free'}
            if not mine:
                raise Busy('The claim belongs to another session and is left unchanged.')
            self.write(oid, None)
            return {'status': 'released'}
        if action == 'check':
            if head is not None and record['head'] != head:
                raise Busy('The claim refers to another commit. Refresh the review and claim first.')
            return {'status': 'owned', **record}
        if not head:
            raise ReviewError('take and renew require --head identifying the commit being handled.')
        record = {'protocol': 1, 'session': session, 'owner': owner or session,
                  'head': head, 'expiresAt': iso(now() + timedelta(seconds=ttl))}
        self.write(oid, record)
        return {'status': 'owned', **record}


def state_root():
    if os.environ.get('PR_REVIEW_STATE_DIR'):
        return Path(os.environ['PR_REVIEW_STATE_DIR']).expanduser()
    if os.name == 'nt':
        return Path(os.environ.get('LOCALAPPDATA', Path.home() / 'AppData' / 'Local')) / 'pr-review'
    return Path(os.environ.get('XDG_STATE_HOME', Path.home() / '.local' / 'state')) / 'pr-review'


def receipt_path(repo, pr):
    key = hashlib.sha256(repo.lower().encode('utf-8')).hexdigest()
    return state_root() / 'receipts' / key / f'{pr}.json'


def save_receipt(repo, pr, payload, run_id=None):
    sha(payload['head'])
    sha(payload['base'])
    if 'baseBranch' in payload and (not isinstance(payload['baseBranch'], str) or not payload['baseBranch'].strip()):
        raise ReviewError('baseBranch must identify the reviewed target branch.')
    if payload.get('result') not in ('reviewed', 'fixed', 'merged', 'waiting'):
        raise ReviewError('Result must be reviewed, fixed, merged or waiting.')
    if not isinstance(payload.get('handledEvents', []), list) or any(not isinstance(x, str) for x in payload.get('handledEvents', [])):
        raise ReviewError('handledEvents must be a list of event keys.')
    # Receipts contain only identifiers, outcomes and short plain notes, never PR bodies or secrets.
    if payload['result'] == 'waiting':
        waiting = payload.get('waiting')
        if not isinstance(waiting, dict) or any(
            not isinstance(waiting.get(key), str) or not waiting[key].strip()
            for key in ('kind', 'reason', 'owner', 'nextStep')
        ) or (waiting.get('question') is not None and not isinstance(waiting['question'], str)):
            raise ReviewError('Waiting requires kind, reason, owner, nextStep and an optional question. Use unknown for an unidentified owner.')
        if waiting['kind'] == 'decision' and (not isinstance(waiting.get('question'), str) or not waiting['question'].strip()):
            raise ReviewError('A pending decision requires a concrete non-empty question.')
    elif payload.get('waiting') is not None:
        raise ReviewError('Only waiting receipts may carry an unresolved waiting item.')
    verification = payload.get('verification', [])
    if not isinstance(verification, list):
        raise ReviewError('verification must be a list of journey checks.')
    for check in verification:
        if not isinstance(check, dict) or check.get('status') not in ('passed', 'failed', 'not-run', 'not-applicable'):
            raise ReviewError('Journey checks require a supported status.')
        if any(not isinstance(check.get(key), str) or not check[key].strip()
               for key in ('flow', 'environment', 'detail')):
            raise ReviewError('Journey checks require flow, environment and detail.')
        if check.get('head') != payload['head'] or check.get('base') != payload['base']:
            raise ReviewError('Journey evidence must match the receipt head and base.')
    if run_id is not None:
        manifest = load_run(run_id)
        run_id = manifest['runId']
        ensure_in_scope(manifest, repo, pr)
    record = {key: payload[key] for key in ('head', 'base', 'baseBranch', 'result', 'handledEvents', 'note', 'waiting', 'verification') if key in payload}
    record.update(repo=repo, number=pr, seen=iso(now()))
    if run_id is not None:
        record['runId'] = run_id
    target = receipt_path(repo, pr)
    atomic_json(target, record)
    if run_id is not None:
        atomic_json(run_path(run_id) / 'progress' / target.parent.name / target.name, record)
    return record


def atomic_json(target, record):
    target.parent.mkdir(parents=True, exist_ok=True)
    fd, temporary = tempfile.mkstemp(prefix='receipt-', suffix='.tmp', dir=target.parent)
    try:
        with os.fdopen(fd, 'w', encoding='utf-8') as handle:
            json.dump(record, handle, ensure_ascii=False, indent=2)
        os.replace(temporary, target)
    finally:
        Path(temporary).unlink(missing_ok=True)


def run_path(run_id):
    return state_root() / 'runs' / token(run_id)


def load_run(run_id):
    if run_id == 'latest':
        manifests = list((state_root() / 'runs').glob('*/run.json'))
        if not manifests:
            raise ReviewError('No saved run was found. Choose repositories and a mode to start one.')
        # Files contain a validated timestamp and immutable run id, not a global latest pointer.
        candidates = [json.loads(path.read_text(encoding='utf-8')) for path in manifests]
        manifest = max(candidates, key=lambda item: (item['createdAt'], item['runId']))
    else:
        manifest = json.loads((run_path(run_id) / 'run.json').read_text(encoding='utf-8'))
    token(manifest['runId'])
    if run_id != 'latest' and manifest['runId'] != run_id:
        raise ReviewError('The saved run identity does not match its location.')
    if manifest.get('schema') != 1 or manifest.get('mode') not in ('comments', 'fix'):
        raise ReviewError('The saved run format is not supported. Do not guess its scope or permissions.')
    if not isinstance(manifest.get('repos'), list) or not manifest['repos']:
        raise ReviewError('The saved run has no valid repository selection.')
    for repo in manifest['repos']:
        repo_name(repo)
    if manifest.get('status') not in ('active', 'paused', 'waiting', 'complete'):
        raise ReviewError('The saved run status is not supported.')
    if not isinstance(manifest.get('only'), list):
        raise ReviewError('The saved PR restriction is not supported.')
    for key in manifest['only']:
        if not isinstance(key, str):
            raise ReviewError('A saved PR restriction has an invalid format.')
        repo, number = key.rsplit('#', 1)
        repo_name(repo)
        positive(number)
        if repo.lower() not in [name.lower() for name in manifest['repos']]:
            raise ReviewError('A saved PR restriction is outside its repositories.')
    return manifest


def pr_key(repo, pr):
    return f'{repo.lower()}#{pr}'


def ensure_in_scope(manifest, repo, pr):
    if repo.lower() not in [name.lower() for name in manifest['repos']]:
        raise ReviewError('The repository is outside this run.')
    if manifest.get('only') and pr_key(repo, pr) not in manifest['only']:
        raise ReviewError('The PR is outside this run.')


def start_run(repos, mode, only=None, start=None):
    if mode not in ('comments', 'fix'):
        raise ReviewError('Run mode must be comments or fix.')
    for repo in repos:
        repo_name(repo)
    if not repos:
        raise ReviewError('Select at least one repository.')
    repos = list(dict.fromkeys(name.lower() for name in repos))
    manifest = {'schema': 1, 'runId': uuid.uuid4().hex, 'createdAt': iso(now()),
                'mode': mode, 'repos': repos, 'only': [], 'start': start, 'status': 'active'}
    for item in only or []:
        try:
            repo, number = item.rsplit('#', 1)
            key = pr_key(repo_name(repo), positive(number))
        except (ValueError, argparse.ArgumentTypeError) as exc:
            raise ReviewError('PR selections must use owner/repo#number.') from exc
        if repo.lower() not in repos:
            raise ReviewError('The selected PR belongs to a repository outside this run.')
        manifest['only'].append(key)
    if start:
        try:
            repo, number = start.rsplit('#', 1)
            repo_name(repo)
            number = positive(number)
        except (ValueError, argparse.ArgumentTypeError) as exc:
            raise ReviewError('The starting PR must use owner/repo#number.') from exc
        ensure_in_scope(manifest, repo, number)
        manifest['start'] = pr_key(repo, number)
    atomic_json(run_path(manifest['runId']) / 'run.json', manifest)
    return manifest


def configure_run(run_id, repos=None, mode=None, only=None, all_prs=False):
    manifest = load_run(run_id)
    if repos is not None:
        if not repos:
            raise ReviewError('Select at least one repository.')
        manifest['repos'] = list(dict.fromkeys(repo_name(name).lower() for name in repos))
    if mode is not None:
        if mode not in ('comments', 'fix'):
            raise ReviewError('Run mode must be comments or fix.')
        manifest['mode'] = mode
    if only is not None and all_prs:
        raise ReviewError('Choose named PRs or all PRs, not both.')
    if all_prs:
        manifest['only'] = []
    elif only is not None:
        manifest['only'] = []
        for item in only:
            repo, number = item.rsplit('#', 1)
            key = pr_key(repo_name(repo), positive(number))
            if repo.lower() not in manifest['repos']:
                raise ReviewError('The selected PR belongs to a repository outside this run.')
            manifest['only'].append(key)
    for key in manifest['only']:
        repo, number = key.rsplit('#', 1)
        ensure_in_scope(manifest, repo, int(number))
    # The starting preference is already consumed, never use it to expand a changed scope.
    manifest['start'] = None
    atomic_json(run_path(manifest['runId']) / 'run.json', manifest)
    return manifest


def show_run(run_id):
    manifest = load_run(run_id)
    directory = run_path(manifest['runId'])
    progress = [json.loads(path.read_text(encoding='utf-8')) for path in sorted((directory / 'progress').glob('*/*.json'))]
    rounds = {}
    for repo in manifest['repos']:
        repo_rounds = directory / 'rounds' / receipt_path(repo, 1).parent.name
        for pr_directory in repo_rounds.glob('*'):
            if not pr_directory.name.isdigit():
                continue
            reserved = [number for number in range(1, MAX_FIX_ROUNDS + 1)
                        if (pr_directory / f'{number}.json').exists()]
            if reserved:
                # A crash may leave an empty reservation. Its existence still consumes a round.
                rounds[pr_key(repo, int(pr_directory.name))] = max(reserved)
    return {'run': manifest, 'progress': progress, 'fixRounds': rounds,
            'notice': 'Saved context only. Refresh GitHub, claims, head, base, CI and deployments before continuing.'}


def reserve_fix_round(run_id, repo, pr):
    manifest = load_run(run_id)
    if manifest['mode'] != 'fix' or manifest['status'] != 'active':
        raise ReviewError('This run does not permit another fix round.')
    ensure_in_scope(manifest, repo, pr)
    directory = run_path(manifest['runId']) / 'rounds' / receipt_path(repo, pr).parent.name / str(pr)
    directory.mkdir(parents=True, exist_ok=True)
    # Reserve before editing. Exclusive creation also handles two local resumers racing.
    for number in range(1, MAX_FIX_ROUNDS + 1):
        path = directory / f'{number}.json'
        try:
            with path.open('x', encoding='utf-8') as handle:
                record = {'repo': repo, 'number': pr, 'round': number, 'reservedAt': iso(now())}
                json.dump(record, handle, ensure_ascii=False)
            return record
        except FileExistsError:
            continue
    raise Busy('Three fix rounds have already been used for this PR in this run. Leave it open and report the remaining issue.')


def parser():
    root = argparse.ArgumentParser(description=__doc__)
    commands = root.add_subparsers(dest='command', required=True)
    commands.add_parser('session')
    cmd = commands.add_parser('doctor')
    cmd.add_argument('--repo', required=True, type=repo_name)
    cmd.add_argument('--checkout')
    cmd = commands.add_parser('list')
    cmd.add_argument('--repo', required=True, action='append', type=repo_name)
    cmd = commands.add_parser('version')
    cmd.add_argument('--repo', required=True, type=repo_name)
    cmd.add_argument('--pr', required=True, type=positive)
    cmd.add_argument('--expect-head', type=sha)
    cmd.add_argument('--expect-base', type=sha)
    cmd.add_argument('--expect-base-branch')
    cmd = commands.add_parser('run-start')
    cmd.add_argument('--repo', required=True, action='append', type=repo_name)
    cmd.add_argument('--mode', required=True, choices=('comments', 'fix'))
    cmd.add_argument('--only', action='append', default=[])
    cmd.add_argument('--start')
    cmd = commands.add_parser('run-configure')
    cmd.add_argument('--run', default='latest')
    cmd.add_argument('--repo', action='append', type=repo_name)
    cmd.add_argument('--mode', choices=('comments', 'fix'))
    scope = cmd.add_mutually_exclusive_group()
    scope.add_argument('--only', action='append')
    scope.add_argument('--all-prs', action='store_true')
    for name in ('run-show', 'run-status', 'fix-round'):
        cmd = commands.add_parser(name)
        cmd.add_argument('--run', default='latest', type=str)
        if name == 'run-status':
            cmd.add_argument('--status', required=True, choices=('active', 'paused', 'waiting', 'complete'))
        if name == 'fix-round':
            cmd.add_argument('--repo', required=True, type=repo_name)
            cmd.add_argument('--pr', required=True, type=positive)
    for name in ('events', 'history', 'record'):
        cmd = commands.add_parser(name)
        cmd.add_argument('--repo', required=True, type=repo_name)
        cmd.add_argument('--pr', required=True, type=positive)
        if name == 'record':
            cmd.add_argument('--input', required=True)
            cmd.add_argument('--run')
    cmd = commands.add_parser('claim')
    cmd.add_argument('action', choices=('list', 'take', 'check', 'renew', 'free'))
    cmd.add_argument('--repo', required=True, type=repo_name)
    cmd.add_argument('--checkout', required=True)
    target = cmd.add_mutually_exclusive_group()
    target.add_argument('--pr', type=positive)
    target.add_argument('--resource', choices=('merge-deploy',))
    cmd.add_argument('--session', type=token)
    cmd.add_argument('--head', type=sha)
    cmd.add_argument('--owner')
    cmd.add_argument('--ttl', type=int, default=3600)
    return root


def main(argv=None):
    args = parser().parse_args(argv)
    try:
        if args.command == 'session':
            result = {'session': uuid.uuid4().hex}
        elif args.command == 'doctor':
            result = doctor(args.repo, args.checkout)
        elif args.command == 'list':
            result = inventory(args.repo)
        elif args.command == 'version':
            result = version(args.repo, args.pr, args.expect_head, args.expect_base, args.expect_base_branch)
        elif args.command == 'run-start':
            result = start_run(args.repo, args.mode, args.only, args.start)
        elif args.command == 'run-show':
            result = show_run(args.run)
        elif args.command == 'run-configure':
            result = configure_run(args.run, args.repo, args.mode, args.only, args.all_prs)
        elif args.command == 'run-status':
            result = load_run(args.run)
            result['status'] = args.status
            atomic_json(run_path(result['runId']) / 'run.json', result)
        elif args.command == 'fix-round':
            result = reserve_fix_round(args.run, args.repo, args.pr)
        elif args.command == 'events':
            result = events(args.repo, args.pr)
        elif args.command == 'history':
            path = receipt_path(args.repo, args.pr)
            result = json.loads(path.read_text(encoding='utf-8')) if path.exists() else None
        elif args.command == 'record':
            result = save_receipt(args.repo, args.pr, json.loads(Path(args.input).read_text(encoding='utf-8')), args.run)
        else:
            check_checkout(args.checkout, args.repo)
            if args.action == 'list':
                refs = git(args.checkout, 'ls-remote', 'origin', PREFIX + '*')
                result = []
                for line in refs.splitlines():
                    _, ref = line.split('\t')
                    number = ref.removeprefix(PREFIX)
                    if number.isdigit() or number == 'merge-deploy':
                        _, record = Lease(args.checkout, number).read()
                        if record:
                            target = {'number': int(number)} if number.isdigit() else {'resource': number}
                            result.append({**target, **record})
            else:
                resource = args.pr if args.pr is not None else args.resource
                if resource is None or args.session is None:
                    raise ReviewError('--pr or --resource, and --session are required.')
                if not 300 <= args.ttl <= 7200:
                    raise ReviewError('Claim lifetime must be 300-7200 seconds.')
                result = Lease(args.checkout, resource).act(args.action, args.session, args.head, args.owner, args.ttl)
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return 0
    except Busy as exc:
        print(json.dumps({'status': 'busy', 'message': str(exc)}, ensure_ascii=False))
        return 1
    except (ReviewError, OSError, ValueError, KeyError, TypeError, argparse.ArgumentTypeError) as exc:
        # JSON/OS errors should not dump PR content, paths with credentials or a traceback.
        message = str(exc) if isinstance(exc, ReviewError) else 'Input could not be read or saved. No success is verified.'
        print(json.dumps({'status': 'error', 'message': message}, ensure_ascii=False))
        return 2


if __name__ == '__main__':
    if hasattr(sys.stdout, 'reconfigure'):
        sys.stdout.reconfigure(encoding='utf-8')
    raise SystemExit(main())
