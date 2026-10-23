import contextlib
import importlib.util
import io
from pathlib import Path
import tempfile
import unittest

SPEC = importlib.util.spec_from_file_location(
    "sync_instructions", Path(__file__).resolve().parents[1] / "sync-instructions.py")
syncer = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(syncer)


class InstructionSyncTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix="ws rules ")
        self.addCleanup(self.temp.cleanup)
        root = Path(self.temp.name)
        self.claude = root / "custom claude"
        self.codex = root / "custom codex"

    def run_sync(self, dry=False):
        output = io.StringIO()
        with contextlib.redirect_stdout(output):
            syncer.sync(self.claude, self.codex, dry)
        return output.getvalue()

    def test_clean_install_and_idempotence(self):
        self.run_sync()
        for directory in (self.claude, self.codex):
            self.assertEqual((directory / syncer.NAME).read_bytes(),
                             (syncer.ROOT / syncer.NAME).read_bytes())
        self.assertEqual((self.claude / "CLAUDE.md").read_text(), "@AGENTS.WeSports.md\n")
        self.assertIn((self.codex / syncer.NAME).as_posix(),
                      (self.codex / "AGENTS.md").read_text())
        before = {p: (p.read_bytes(), p.stat().st_mtime_ns)
                  for p in Path(self.temp.name).rglob("*") if p.is_file()}
        self.run_sync()
        after = {p: (p.read_bytes(), p.stat().st_mtime_ns)
                 for p in Path(self.temp.name).rglob("*") if p.is_file()}
        self.assertEqual(before, after)

    def test_migration_preserves_personal_bytes_and_backs_up(self):
        self.claude.mkdir()
        legacy = "@" + (syncer.ROOT / "claude" / "CLAUDE.md").as_posix()
        original = ("Personal: \u00e5\u00e4\u00f6\r\n" + legacy + "\r\n@personal.md\r\n").encode()
        path = self.claude / "CLAUDE.md"
        path.write_bytes(original)
        self.codex.mkdir()
        (self.codex / "AGENTS.md").write_bytes(b"Personal preferences without newline")
        self.run_sync()
        self.assertEqual(path.read_bytes(), "Personal: \u00e5\u00e4\u00f6\r\n@personal.md\r\n@AGENTS.WeSports.md\r\n".encode())
        self.assertEqual(path.with_name(path.name + ".ws-dev-env.bak").read_bytes(), original)
        self.assertTrue((self.codex / "AGENTS.md").read_bytes().startswith(b"Personal preferences without newline\n"))
        (self.claude / syncer.NAME).write_text("Old rules")
        self.run_sync()
        self.assertEqual(path.with_name(path.name + ".ws-dev-env.bak").read_bytes(), original)
        self.assertEqual((self.claude / syncer.NAME).read_bytes(), (syncer.ROOT / syncer.NAME).read_bytes())

    def test_dry_run_creates_nothing(self):
        self.assertIn("would update", self.run_sync(dry=True))
        self.assertEqual(list(Path(self.temp.name).iterdir()), [])

    def test_override_warns_without_modifying_it(self):
        self.codex.mkdir()
        override = self.codex / "AGENTS.override.md"
        override.write_text("My override")
        self.assertIn("WARNING", self.run_sync())
        self.assertEqual(override.read_text(), "My override")

    def test_invalid_target_fails_before_any_writes(self):
        (self.codex / "AGENTS.md").mkdir(parents=True)
        with self.assertRaises(ValueError):
            self.run_sync()
        self.assertFalse(self.claude.exists())


if __name__ == "__main__":
    unittest.main()
