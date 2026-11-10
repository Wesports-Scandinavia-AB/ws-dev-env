import contextlib
import importlib.util
import io
import unittest
from pathlib import Path
from unittest.mock import patch

SPEC = importlib.util.spec_from_file_location('update_tools', Path(__file__).resolve().parents[1] / 'scripts/update-tools.py')
updater = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(updater)


class UpdateToolsTests(unittest.TestCase):
    def setUp(self):
        self.items = [{'name': 'git', 'winget': 'Git.Git', 'brew': 'git'},
                      {'name': 'codex', 'npm': '@openai/codex'},
                      {'name': 'terminal', 'winget': 'Microsoft.WindowsTerminal'},
                      {'name': 'ghostty', 'brew': 'ghostty', 'cask': True}]

    def invoke(self, system, apply=False, runner=None):
        with contextlib.redirect_stdout(io.StringIO()), patch.object(updater.shutil, 'which', return_value='found'):
            updater.update(self.items, system, apply, runner)

    def test_preview_never_runs_installers(self):
        def fail(*args):
            self.fail('Preview must not run a command')
        self.invoke('Windows', runner=fail)
        self.invoke('Darwin', runner=fail)

    def test_windows_updates_only_declared_ids_and_refreshes_existing_npm(self):
        calls = []
        def run(command, allowed=()):
            calls.append(command)
            return updater.NO_UPGRADE if command[:2] == ['winget', 'upgrade'] else 0
        self.invoke('Windows', True, run)
        self.assertIn(['npm.cmd', 'install', '--global', '@openai/codex'], calls)
        self.assertIn(['npm.cmd', 'install', '--global', 'pnpm@9'], calls)
        self.assertFalse(any('--all' in call for call in calls))
        self.assertFalse(any('ghostty' in call for call in calls))

    def test_windows_missing_package_is_installed_after_exact_upgrade_miss(self):
        calls = []
        def run(command, allowed=()):
            calls.append(command)
            return updater.NOT_INSTALLED if command[:2] == ['winget', 'upgrade'] else 0
        self.invoke('Windows', True, run)
        self.assertEqual(sum(call[:2] == ['winget', 'install'] for call in calls), 2)

    def test_mac_updates_declared_formulae_and_casks_without_touching_windows_only_tools(self):
        calls = []
        def run(command, allowed=()):
            calls.append(command)
            return 0
        self.invoke('Darwin', True, run)
        self.assertIn(['brew', 'upgrade', '--formula', 'git'], calls)
        self.assertIn(['brew', 'upgrade', '--cask', 'ghostty'], calls)
        self.assertFalse(any('Microsoft.WindowsTerminal' in call for call in calls))
        self.assertIn(['npm', 'install', '--global', '@openai/codex'], calls)

    def test_failure_stops_before_claiming_success_or_updating_more_tools(self):
        calls = []
        def run(command, allowed=()):
            calls.append(command)
            raise RuntimeError('Package manager failed')
        with self.assertRaises(RuntimeError):
            self.invoke('Windows', True, run)
        self.assertEqual(len(calls), 1)


if __name__ == '__main__':
    unittest.main()
