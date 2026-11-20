"""O duplo de teste deve persistir as escritas entre processos."""
import json
import os
import subprocess
import tempfile
import unittest
from pathlib import Path

FAKE = Path(__file__).with_name("track_fake_gh.py")


class FakeGitHubTest(unittest.TestCase):
    def test_issue_lifecycle_persists_and_logs_calls(self):
        with tempfile.TemporaryDirectory() as tmp:
            state = Path(tmp) / "state.json"
            env = {**os.environ, "TRACK_GH_STATE": str(state)}
            def run(*args):
                return subprocess.run(["python3", str(FAKE), *args], env=env,
                                      text=True, capture_output=True, check=True).stdout
            run("issue", "create", "--title", "Exemplo", "--body", "corpo")
            run("issue", "comment", "1", "--body", "comentário")
            run("issue", "edit", "1", "--add-label", "em andamento")
            issue = json.loads(run("issue", "view", "1"))
            self.assertEqual(issue["body"], "corpo")
            self.assertEqual(issue["comments"][0]["body"], "comentário")
            self.assertEqual(issue["labels"][0]["name"], "em andamento")
            self.assertEqual(len(json.loads(state.read_text())["calls"]), 4)

    def test_help_and_version_succeed_even_on_subcommands(self):
        with tempfile.TemporaryDirectory() as tmp:
            state = Path(tmp) / "state.json"
            env = {**os.environ, "TRACK_GH_STATE": str(state)}
            def run(*args):
                return subprocess.run(["python3", str(FAKE), *args], env=env,
                                      text=True, capture_output=True, check=True).stdout
            help_out = run("issue", "edit", "--help")
            self.assertIn("--add-blocked-by", help_out)
            ver_out = run("--version")
            self.assertIn("gh version", ver_out)

    def test_item_lookup_with_flags_before_target(self):
        with tempfile.TemporaryDirectory() as tmp:
            state = Path(tmp) / "state.json"
            env = {**os.environ, "TRACK_GH_STATE": str(state)}
            def run(*args):
                return subprocess.run(["python3", str(FAKE), *args], env=env,
                                      text=True, capture_output=True, check=True).stdout
            run("issue", "create", "--title", "Teste", "--body", "corpo 1")
            run("issue", "edit", "-R", "example/project", "1", "--body", "corpo editado")
            issue = json.loads(run("issue", "view", "-R", "example/project", "1"))
            self.assertEqual(issue["body"], "corpo editado")
