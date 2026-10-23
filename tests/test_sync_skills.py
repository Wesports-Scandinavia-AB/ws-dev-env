import contextlib
import importlib.util
import io
import json
import os
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

SPEC = importlib.util.spec_from_file_location(
    "sync_skills", Path(__file__).resolve().parents[1] / "sync-skills.py")
syncer = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(syncer)


class SkillSyncTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix="ws skills ")
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name).resolve()
        self.home = self.root / "home"
        self.layer = self.root / "shared"
        self.personal = self.root / "personal"
        self.layer.mkdir()
        self.personal.mkdir()
        self.packages = [
            {"name": "claude", "skill_dir": ".claude/skills", "skill_config_env": "CLAUDE_CONFIG_DIR"},
            {"name": "codex", "skill_dir": ".agents/skills"},
        ]
        self.manifest()
        self.source = self.skill(self.layer, "example")
        self.environment = patch.dict(os.environ, {"CLAUDE_CONFIG_DIR": "", "CODEX_HOME": ""})
        self.environment.start()
        self.addCleanup(self.environment.stop)

    def manifest(self):
        (self.layer / "packages.json").write_text(json.dumps({"packages": self.packages}))

    def skill(self, layer, name):
        source = layer / "claude" / "skills" / name
        source.mkdir(parents=True)
        (source / "SKILL.md").write_text(f"---\nname: {name}\ndescription: Test skill\n---\nVersion one")
        (source / "references").mkdir()
        (source / "references" / "guide.md").write_text("Reference content")
        return source

    def run_sync(self, dry=False, wsg=False):
        with contextlib.redirect_stdout(io.StringIO()):
            syncer.sync([self.layer, self.personal], self.home, dry, wsg)

    def test_all_skills_and_supporting_files_reach_every_agent(self):
        self.skill(self.personal, "personal")
        self.packages.append({"name": "future-agent", "skill_dir": ".future/skills"})
        self.manifest()
        self.run_sync()
        for destination in syncer.targets([self.layer], self.home):
            for name in ("example", "personal"):
                self.assertTrue(syncer.linked(destination / name))
                self.assertEqual((destination / name / "references" / "guide.md").read_text(), "Reference content")
        (self.source / "SKILL.md").write_text("Version two")
        self.run_sync()
        for destination in syncer.targets([self.layer], self.home):
            self.assertEqual((destination / "example" / "SKILL.md").read_text(), "Version two")

    def test_existing_claude_link_is_reused_and_codex_added(self):
        target = self.home / ".claude" / "skills" / "example"
        target.parent.mkdir(parents=True)
        syncer.link_directory(self.source, target)
        self.run_sync()
        self.assertEqual(target.resolve(), self.source)
        self.assertEqual((self.home / ".agents" / "skills" / "example").resolve(), self.source)

    def test_custom_claude_home_and_codex_home_does_not_change_skills(self):
        custom = self.home / "custom claude"
        with patch.dict(os.environ, {"CLAUDE_CONFIG_DIR": str(custom), "CODEX_HOME": str(self.home / "codex-config")}):
            self.run_sync()
        self.assertTrue((custom / "skills" / "example" / "SKILL.md").is_file())
        self.assertTrue((self.home / ".agents" / "skills" / "example" / "SKILL.md").is_file())

    def test_conflicts_preserve_existing_files_and_prevent_partial_install(self):
        existing = self.home / ".claude" / "skills" / "example"
        existing.mkdir(parents=True)
        (existing / "SKILL.md").write_text("My own skill")
        with self.assertRaisesRegex(ValueError, "Skill conflict"):
            self.run_sync()
        self.assertEqual((existing / "SKILL.md").read_text(), "My own skill")
        self.assertFalse((self.home / ".agents").exists())

    def test_duplicate_source_names_fail(self):
        self.skill(self.personal, "example")
        with self.assertRaisesRegex(ValueError, "Duplicate skill"):
            self.run_sync()
        self.assertFalse(self.home.exists())

    def test_dry_run_does_not_write_or_install_wsg(self):
        with patch.object(syncer.subprocess, "run") as runner:
            self.run_sync(dry=True, wsg=True)
        runner.assert_not_called()
        self.assertFalse(self.home.exists())

    def test_wsg_is_refreshed_for_every_agent_on_every_run(self):
        with patch.object(syncer.subprocess, "run") as runner:
            self.run_sync(wsg=True)
            self.run_sync(wsg=True)
        self.assertEqual(runner.call_count, 4)
        expected = {str(p / "wsg") for p in syncer.targets([self.layer], self.home)}
        self.assertEqual({call.args[0][-1] for call in runner.call_args_list}, expected)
        for call in runner.call_args_list:
            self.assertEqual(call.args[0][1:6], ["-m", "wsg", "skill", "install", "--dir"])
            self.assertTrue(call.kwargs["check"])

    def test_saved_personal_layer_is_used(self):
        self.home.mkdir()
        (self.home / ".ws-dev-env.json").write_text(json.dumps({
            "root": str(self.root), "personal": "owner/personal"}))
        self.assertEqual(syncer.configured_layers(self.layer, self.home, []), [self.layer, self.personal])

    def test_repository_agents_have_skill_targets(self):
        packages = json.loads((Path(SPEC.origin).parent / "packages.json").read_text())["packages"]
        for name in ("claude-code", "codex"):
            self.assertTrue(next(p for p in packages if p["name"] == name)["skill_dir"])


if __name__ == "__main__":
    unittest.main()
