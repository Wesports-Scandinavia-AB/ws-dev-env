"""Include the bundled PR workflow's local protocol tests in the repository gate."""
import importlib.util
from pathlib import Path

PATH = Path(__file__).resolve().parents[1] / 'claude/skills/wesports-pr-review/scripts/test_pr_review.py'
SPEC = importlib.util.spec_from_file_location('wesports_pr_review_tests', PATH)
suite = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(suite)


def load_tests(loader, tests, pattern):
    return loader.loadTestsFromModule(suite)
