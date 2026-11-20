"""Contratos entre a skill de acompanhamento e o fluxo."""
import unittest
from pathlib import Path

ROOT = Path(__file__).parents[1]


class TrackTextTest(unittest.TestCase):
    def test_track_contract(self):
        text = (ROOT / "skills/track/SKILL.md").read_text()
        for phrase in ("## Acompanhamento de projeto", "check_track.py", "findings.md",
                       "marcador", "confirmação", "comentários", "hash", "remoto",
                       "manual", "falha", "converge", "sem fallback"):
            self.assertIn(phrase, text)

    def test_integrations_are_opt_in(self):
        for path in ("skills/refine/SKILL.md", "skills/implement/SKILL.md", "skills/open-pr/SKILL.md"):
            text = (ROOT / path).read_text()
            self.assertIn("## Acompanhamento de projeto", text, path)
            self.assertIn("track", text, path)

    def test_references_exist(self):
        for name in ("modelo-tracker", "github", "jira", "monday", "azure-boards"):
            self.assertTrue((ROOT / "skills/track/references" / f"{name}.md").is_file(), name)

    def test_recovery_and_shared_item_contract(self):
        text = (ROOT / "skills/track/SKILL.md").read_text()
        for phrase in ("marcador e evento", "busca vazia", "card comum", "épico de origem", "marcador no card"):
            self.assertIn(phrase, text.lower())

    def test_absent_configuration_never_calls_cli(self):
        self.assertIn("não execute comandos da ferramenta", (ROOT / "skills/track/SKILL.md").read_text())
