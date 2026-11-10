"""Local-only protocol tests. No network, live repositories, reviews or merges."""
from concurrent.futures import ThreadPoolExecutor
from datetime import timedelta
import importlib.util
import json
import os
from pathlib import Path
import subprocess
import tempfile
import unittest
from unittest.mock import patch

spec = importlib.util.spec_from_file_location('pr_review', Path(__file__).with_name('pr_review.py'))
review = importlib.util.module_from_spec(spec)
spec.loader.exec_module(review)


def git(*args):
    result = subprocess.run(['git', *map(str, args)], capture_output=True, text=True, encoding='utf-8', check=True)
    return result.stdout.strip()


class LeaseTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix='pr-review-test-')
        self.root = Path(self.temp.name)
        self.remote = self.root / 'remote.git'
        git('init', '--bare', self.remote)
        self.a, self.b = self.root / 'a', self.root / 'b'
        git('init', self.a)
        git('-C', self.a, 'config', 'user.name', 'Test')
        git('-C', self.a, 'config', 'user.email', 'test@invalid')
        (self.a / 'app.txt').write_text('original\n', encoding='utf-8')
        git('-C', self.a, 'add', 'app.txt')
        git('-C', self.a, 'commit', '-m', 'seed')
        self.head = git('-C', self.a, 'rev-parse', 'HEAD')
        git('-C', self.a, 'remote', 'add', 'origin', self.remote)
        git('-C', self.a, 'push', 'origin', 'HEAD:refs/heads/main')
        git('clone', '--branch', 'main', self.remote, self.b)
        self.la, self.lb = review.Lease(self.a, 123), review.Lease(self.b, 123)

    def tearDown(self):
        self.temp.cleanup()

    def take(self, lease, session):
        return lease.act('take', session, self.head, 'colleague')

    def test_two_clones_cannot_claim_same_pr(self):
        self.take(self.la, 'session-a')
        with self.assertRaises(review.Busy):
            self.take(self.lb, 'session-b')
        self.la.act('check', 'session-a', self.head)
        self.la.act('renew', 'session-a', self.head)
        with self.assertRaises(review.Busy):
            self.lb.act('free', 'session-b')
        self.la.act('free', 'session-a')
        self.take(self.lb, 'session-b')

    def test_concurrent_creation_has_exactly_one_winner(self):
        def attempt(pair):
            lease, session = pair
            try:
                self.take(lease, session)
                return True
            except review.ReviewError:
                return False
        with ThreadPoolExecutor(max_workers=2) as pool:
            result = list(pool.map(attempt, [(self.la, 'session-a'), (self.lb, 'session-b')]))
        self.assertEqual(sum(result), 1)

    def test_expiration_takeover_and_old_owner_cannot_release(self):
        self.take(self.la, 'session-a')
        future = review.now() + timedelta(hours=2)
        with patch.object(review, 'now', return_value=future):
            with self.assertRaises(review.Busy):
                self.la.act('renew', 'session-a', self.head)
            self.take(self.lb, 'session-b')
            with self.assertRaises(review.Busy):
                self.la.act('free', 'session-a')
            self.lb.act('check', 'session-b', self.head)

    def test_stale_oid_cannot_replace_or_delete_renewed_lease(self):
        self.take(self.la, 'session-a')
        old_oid, record = self.lb.read()
        self.la.act('renew', 'session-a', self.head)
        with self.assertRaises(review.ReviewError):
            self.lb.write(old_oid, {**record, 'session': 'session-b'})
        with self.assertRaises(review.ReviewError):
            self.lb.write(old_oid, None)
        self.la.act('check', 'session-a', self.head)

    def test_claim_does_not_change_working_tree_index_or_head(self):
        (self.a / 'app.txt').write_text('user change\n', encoding='utf-8')
        before = git('-C', self.a, 'status', '--porcelain')
        self.take(self.la, 'session-a')
        self.la.act('free', 'session-a')
        self.assertEqual(git('-C', self.a, 'status', '--porcelain'), before)
        self.assertEqual(git('-C', self.a, 'rev-parse', 'HEAD'), self.head)
        self.assertEqual((self.a / 'app.txt').read_text(encoding='utf-8'), 'user change\n')
        self.assertEqual(git('-C', self.a, 'for-each-ref', '--format=%(refname)', 'refs/pr-review/observed/'), '')

    def test_failure_is_not_treated_as_an_absent_claim(self):
        git('-C', self.a, 'remote', 'set-url', 'origin', self.root / 'missing.git')
        with self.assertRaises(review.ReviewError):
            self.take(self.la, 'session-a')

    def test_head_mismatch_prevents_check(self):
        self.take(self.la, 'session-a')
        with self.assertRaises(review.Busy):
            self.la.act('check', 'session-a', '0' * 40)

    def test_separate_prs_have_separate_leases(self):
        self.take(self.la, 'session-a')
        self.take(review.Lease(self.b, 124), 'session-b')
        self.la.act('check', 'session-a', self.head)

    def test_merge_deploy_lock_serializes_different_prs(self):
        self.take(self.la, 'session-a')
        self.take(review.Lease(self.b, 124), 'session-b')
        merge_a = review.Lease(self.a, 'merge-deploy')
        merge_b = review.Lease(self.b, 'merge-deploy')
        self.take(merge_a, 'session-a')
        with self.assertRaises(review.Busy):
            self.take(merge_b, 'session-b')
        merge_a.act('free', 'session-a')
        self.take(merge_b, 'session-b')

    def test_invalid_remote_claims_fail_closed(self):
        for malformed in ([], None, {'protocol': 1, 'session': '-bad', 'head': self.head},
                          {'protocol': 1, 'session': 'session-a', 'head': 'bad'},
                          *({'protocol': 1, 'session': 'session-a', 'head': self.head, 'expiresAt': expiry}
                            for expiry in ('2026-01-01', None, 123, []))):
            tree = review.git(self.a, 'mktree', stdin='')
            oid = review.git(self.a, '-c', 'user.name=Test', '-c', 'user.email=test@invalid',
                             'commit-tree', tree, stdin=json.dumps(malformed))
            git('-C', self.a, 'push', 'origin', f'{oid}:{self.la.ref}')
            with self.assertRaises(review.ReviewError):
                self.take(self.lb, 'session-b')
            oid = git('-C', self.a, 'ls-remote', 'origin', self.la.ref).split()[0]
            self.la.write(oid, None)


class InventoryTests(unittest.TestCase):
    def item(self, number, created, repo='org/a'):
        return {'number': number, 'created_at': created, 'updated_at': created,
                'title': f'PR {number}', 'html_url': 'https://example.invalid',
                'user': {'login': 'author'}, 'draft': number == 3,
                'head': {'sha': 'a' * 40, 'ref': 'feature', 'repo': {'full_name': repo}},
                'base': {'ref': 'main', 'repo': {'full_name': repo}}}

    def test_all_pages_and_global_creation_order(self):
        responses = [json.dumps([[self.item(10, '2026-01-01')], [self.item(3, '2026-01-03')]]),
                     json.dumps([[self.item(99, '2026-01-02', 'org/b')]])]
        with patch.object(review, 'run', side_effect=responses) as command:
            result = review.inventory(['org/a', 'org/b'])
        self.assertEqual([x['number'] for x in result['pulls']], [10, 99, 3])
        self.assertTrue(result['pulls'][-1]['isDraft'])
        self.assertIn('--paginate', command.call_args_list[0].args[0])
        self.assertIn('--slurp', command.call_args_list[0].args[0])

    def test_each_refresh_fetches_again_and_sees_new_and_closed_prs(self):
        with patch.object(review, 'pages', side_effect=[
            [self.item(1, '2026-01-01')], [self.item(2, '2026-01-02')],
        ]) as fetch:
            first = review.inventory(['org/a'])
            second = review.inventory(['org/a'])
        self.assertEqual([x['number'] for x in first['pulls']], [1])
        self.assertEqual([x['number'] for x in second['pulls']], [2])
        self.assertEqual(fetch.call_count, 2)

    def test_one_repo_failure_never_returns_a_partial_inventory(self):
        with patch.object(review, 'pages', side_effect=[[self.item(1, '2026-01-01')], review.ReviewError('offline')]):
            with self.assertRaises(review.ReviewError):
                review.inventory(['org/a', 'org/b'])

    def test_edited_events_have_new_keys_including_same_account(self):
        item = {'id': 12, 'updated_at': '2026-01-01', 'user': {'login': 'same-user'}}
        with patch.object(review, 'pages', side_effect=[[item], [], []]):
            first = review.events('org/a', 1)
        with patch.object(review, 'pages', side_effect=[[{**item, 'updated_at': '2026-01-02'}], [], []]):
            second = review.events('org/a', 1)
        self.assertNotEqual(first['events'][0]['key'], second['events'][0]['key'])
        self.assertEqual(second['events'][0]['author'], 'same-user')


class StateTests(unittest.TestCase):
    def test_same_pr_number_in_two_repos_and_atomic_receipts(self):
        with tempfile.TemporaryDirectory() as directory, patch.dict(os.environ, {'PR_REVIEW_STATE_DIR': directory}):
            payload = {'head': 'a' * 40, 'base': 'b' * 40, 'result': 'waiting', 'handledEvents': ['comment:1:date'],
                       'note': 'needs decision', 'waiting': {'kind': 'decision', 'reason': 'Unclear behavior',
                       'owner': 'unknown', 'question': 'Which role can edit?', 'nextStep': 'Clarify intended permissions'}}
            review.save_receipt('org/a', 1, payload)
            review.save_receipt('other/a', 1, {**payload, 'result': 'merged', 'waiting': None})
            self.assertEqual(json.loads(review.receipt_path('org/a', 1).read_text(encoding='utf-8'))['result'], 'waiting')
            self.assertEqual(json.loads(review.receipt_path('other/a', 1).read_text(encoding='utf-8'))['result'], 'merged')
            self.assertEqual(list(Path(directory).rglob('*.tmp')), [])

    def test_failed_replace_preserves_previous_receipt(self):
        with tempfile.TemporaryDirectory() as directory, patch.dict(os.environ, {'PR_REVIEW_STATE_DIR': directory}):
            payload = {'head': 'a' * 40, 'base': 'b' * 40, 'result': 'reviewed'}
            review.save_receipt('org/a', 1, payload)
            with patch.object(review.os, 'replace', side_effect=OSError('failed')):
                with self.assertRaises(OSError):
                    review.save_receipt('org/a', 1, {**payload, 'result': 'merged'})
            self.assertEqual(json.loads(review.receipt_path('org/a', 1).read_text(encoding='utf-8'))['result'], 'reviewed')

    def test_origin_matching_handles_ssh_https_and_rejects_wrong_hosts(self):
        for url in ['git@github.com:Org/repo.git', 'https://github.com/Org/repo.git', 'ssh://git@github.com/Org/repo.git']:
            self.assertEqual(review.remote_slug(url), 'org/repo')
        self.assertIsNone(review.remote_slug('https://github.com.evil.invalid/Org/repo'))
        self.assertIsNone(review.remote_slug('https://token@github.com/Org/repo'))


class VersionTests(unittest.TestCase):
    def pull(self, head='a', state='open', draft=False):
        return json.dumps({'head': {'sha': head * 40}, 'base': {'repo': {'full_name': 'org/a'}, 'ref': 'release/reports'},
                           'state': state, 'draft': draft})

    def test_current_target_is_resolved_and_pinned(self):
        with patch.object(review, 'run', side_effect=[self.pull(), json.dumps({'sha': 'b' * 40})]) as command:
            result = review.version('org/a', 1, 'a' * 40, 'b' * 40)
        self.assertEqual(result['head'], 'a' * 40)
        self.assertEqual(result['base'], 'b' * 40)
        self.assertIn('release%2Freports', command.call_args_list[1].args[0][-1])

    def test_unchanged_head_does_not_allow_new_base(self):
        with patch.object(review, 'run', side_effect=[self.pull(), json.dumps({'sha': 'c' * 40})]):
            with self.assertRaises(review.Busy):
                review.version('org/a', 1, 'a' * 40, 'b' * 40)

    def test_retargeted_branch_is_detected_even_at_the_same_commit(self):
        with patch.object(review, 'run', side_effect=[self.pull(), json.dumps({'sha': 'b' * 40})]):
            with self.assertRaises(review.Busy):
                review.version('org/a', 1, 'a' * 40, 'b' * 40, 'main')

    def test_changed_head_does_not_allow_old_review(self):
        with patch.object(review, 'run', side_effect=[self.pull(head='c'), json.dumps({'sha': 'b' * 40})]):
            with self.assertRaises(review.Busy):
                review.version('org/a', 1, 'a' * 40, 'b' * 40)

    def test_closed_or_draft_pr_cannot_pass_final_verification(self):
        for state, draft in [('closed', False), ('open', True)]:
            with patch.object(review, 'run', side_effect=[self.pull(state=state, draft=draft), json.dumps({'sha': 'b' * 40})]):
                with self.assertRaises(review.Busy):
                    review.version('org/a', 1, 'a' * 40, 'b' * 40)


class RunTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix='wesports-pr-review-state-')
        self.environment = patch.dict(os.environ, {'PR_REVIEW_STATE_DIR': self.temp.name})
        self.environment.start()

    def tearDown(self):
        self.environment.stop()
        self.temp.cleanup()

    def start(self, mode='fix', only=None):
        return review.start_run(['org/a', 'org/b'], mode, only)

    def receipt(self, **changes):
        return {'head': 'a' * 40, 'base': 'b' * 40, 'result': 'reviewed', 'handledEvents': [], **changes}

    def test_resume_restores_scope_mode_and_waiting_owner(self):
        run = self.start(only=['org/a#1'])
        waiting = {'kind': 'decision', 'reason': 'Role visibility is unclear', 'owner': 'author',
                   'question': 'Team or company?', 'nextStep': 'Choose the intended visibility'}
        review.save_receipt('org/a', 1, self.receipt(result='waiting', waiting=waiting), run['runId'])
        restored = review.show_run(run['runId'])
        self.assertEqual(restored['run']['repos'], ['org/a', 'org/b'])
        self.assertEqual(restored['run']['only'], ['org/a#1'])
        self.assertEqual(restored['run']['mode'], 'fix')
        self.assertEqual(restored['progress'][0]['waiting'], waiting)
        self.assertIn('Refresh GitHub', restored['notice'])

    def test_three_round_budget_survives_heads_and_resume(self):
        run = self.start()
        for number, letter in enumerate('abc', 1):
            self.assertEqual(review.reserve_fix_round(run['runId'], 'org/a', 1)['round'], number)
            review.save_receipt('org/a', 1, self.receipt(head=letter * 40), run['runId'])
            self.assertEqual(review.show_run(run['runId'])['fixRounds']['org/a#1'], number)
        with self.assertRaises(review.Busy):
            review.reserve_fix_round(run['runId'], 'org/a', 1)

    def test_two_resumers_cannot_overallocate_rounds(self):
        run = self.start()
        def reserve(_):
            try:
                return review.reserve_fix_round(run['runId'], 'org/a', 1)['round']
            except review.Busy:
                return None
        with ThreadPoolExecutor(max_workers=6) as pool:
            result = list(pool.map(reserve, range(6)))
        self.assertEqual(sorted(x for x in result if x is not None), [1, 2, 3])

    def test_crashed_reservation_is_still_counted_and_resume_is_readable(self):
        run = self.start()
        review.reserve_fix_round(run['runId'], 'org/a', 1)
        path = next((review.run_path(run['runId']) / 'rounds').glob('*/*/1.json'))
        path.write_text('', encoding='utf-8')
        self.assertEqual(review.show_run(run['runId'])['fixRounds']['org/a#1'], 1)
        self.assertEqual(review.reserve_fix_round(run['runId'], 'org/a', 1)['round'], 2)

    def test_mode_changes_keep_the_same_budget(self):
        run = self.start()
        review.reserve_fix_round(run['runId'], 'org/a', 1)
        review.configure_run(run['runId'], mode='comments')
        with self.assertRaises(review.ReviewError):
            review.reserve_fix_round(run['runId'], 'org/a', 1)
        review.configure_run(run['runId'], mode='fix')
        self.assertEqual(review.reserve_fix_round(run['runId'], 'org/a', 1)['round'], 2)

    def test_named_scope_prevents_new_prs_or_other_repo_work(self):
        run = self.start(only=['org/a#1'])
        for repo, pr in [('org/a', 2), ('org/c', 1)]:
            with self.assertRaises(review.ReviewError):
                review.reserve_fix_round(run['runId'], repo, pr)
            with self.assertRaises(review.ReviewError):
                review.save_receipt(repo, pr, self.receipt(), run['runId'])

    def test_invalid_scope_change_does_not_modify_saved_run(self):
        run = self.start(only=['org/a#1'])
        with self.assertRaises(review.ReviewError):
            review.configure_run(run['runId'], repos=['org/b'])
        self.assertEqual(review.load_run(run['runId'])['repos'], ['org/a', 'org/b'])

    def test_waiting_requires_actionable_details(self):
        for waiting in [None, {'reason': 'Need something'}, {'kind': 'ci', 'reason': 'Pending', 'owner': '', 'nextStep': 'Wait'}]:
            with self.assertRaises(review.ReviewError):
                review.save_receipt('org/a', 1, self.receipt(result='waiting', waiting=waiting))

    def test_business_decisions_require_a_real_question_but_ci_does_not(self):
        waiting = {'kind': 'decision', 'reason': 'Role visibility unclear', 'owner': 'author', 'nextStep': 'Clarify role visibility'}
        for question in (None, '', '   '):
            with self.assertRaises(review.ReviewError):
                review.save_receipt('org/a', 1, self.receipt(result='waiting', waiting={**waiting, 'question': question}))
        result = review.save_receipt('org/a', 1, self.receipt(result='waiting', waiting={**waiting, 'kind': 'ci', 'question': None}))
        self.assertIsNone(result['waiting']['question'])

    def test_receipt_retains_target_branch_for_resume(self):
        run = self.start()
        review.save_receipt('org/a', 1, self.receipt(baseBranch='release/reports'), run['runId'])
        self.assertEqual(review.show_run(run['runId'])['progress'][0]['baseBranch'], 'release/reports')

    def test_journey_evidence_must_match_both_commits(self):
        flow = {'flow': 'Employee enters absence', 'status': 'passed', 'environment': 'local fixture',
                'head': 'a' * 40, 'base': 'c' * 40, 'detail': 'Total verified'}
        with self.assertRaises(review.ReviewError):
            review.save_receipt('org/a', 1, self.receipt(verification=[flow]))
        flow.update(base='b' * 40, status='not-run', detail='No authorized test login')
        result = review.save_receipt('org/a', 1, self.receipt(verification=[flow]))
        self.assertEqual(result['verification'][0]['status'], 'not-run')

    def test_paused_run_needs_resume_before_more_edits(self):
        run = self.start()
        run['status'] = 'paused'
        review.atomic_json(review.run_path(run['runId']) / 'run.json', run)
        with self.assertRaises(review.ReviewError):
            review.reserve_fix_round(run['runId'], 'org/a', 1)

    def test_latest_run_returns_saved_context_without_network(self):
        first = self.start('comments')
        second = self.start('fix')
        with patch.object(review, 'run', side_effect=AssertionError('No remote operation expected')):
            self.assertEqual(review.show_run('latest')['run']['runId'], second['runId'])
        self.assertNotEqual(first['runId'], second['runId'])


if __name__ == '__main__':
    unittest.main(verbosity=2)
