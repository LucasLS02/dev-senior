"""Invariantes do texto da skill open-pr (SKILL.md e modelo-pr.md).
Rodar com: python3 -m unittest discover -s tests -p '*_test.py'
"""
from __future__ import annotations

import re
import sys
import tempfile
import unittest
from pathlib import Path

REPO = Path(__file__).parents[1]
sys.path.insert(0, str(REPO / "skills/open-pr/scripts"))
from check_pr import check  # noqa: E402

SKILL = REPO / "skills/open-pr"
SKILL_MAX = 200
# respostas plantadas por tests/make-docs-fixture.sh e pelas specs da avaliação
FIXTURE_ANSWERS = ("slugify", "slug", "HANDLERS", "dispatch", "sms", "centavos?", "cents",
                   "to_cents", "UTC", "money", "export_row", "notify_export_done",
                   "aviso-exportacao")


class OpenPrTextTest(unittest.TestCase):
    def setUp(self):
        self.skill = (SKILL / "SKILL.md").read_text(encoding="utf-8")
        self.model = (SKILL / "references/modelo-pr.md").read_text(encoding="utf-8")

    def never_section(self) -> str:
        found = re.search(r"^## Nunca\n(.*?)(?=^## |\Z)", self.skill, re.M | re.S)
        self.assertIsNotNone(found, "SKILL.md sem a seção Nunca")
        return found.group(1)

    def test_skill_stays_within_line_cap(self):
        self.assertLessEqual(len(self.skill.splitlines()), SKILL_MAX)

    def test_does_not_leak_fixture_answers(self):
        pattern = re.compile(rf"\b(?:{'|'.join(FIXTURE_ANSWERS)})\b", re.I)
        for name, text in (("SKILL.md", self.skill), ("modelo-pr.md", self.model)):
            self.assertEqual(pattern.findall(text), [], name)

    def test_skill_uses_the_checker(self):
        self.assertIn("check_pr.py", self.skill)

    def test_skill_never_pushes_without_an_order(self):
        self.assertIn("sem ordem", self.skill)
        self.assertIn("não é ordem de push", self.skill)

    def test_skill_forbids_force_and_default_branch(self):
        never = self.never_section()
        self.assertIn("--force", never)
        self.assertIn("branch padrão", never)

    def test_skill_defaults_to_draft(self):
        self.assertIn("--draft", self.skill)

    def test_pr_model_example_passes_the_checker(self):
        example = re.search(r"## Exemplo.*?```markdown\n(.*?)```", self.model, re.S)
        self.assertIsNotNone(example, "modelo-pr.md sem bloco de exemplo")
        with tempfile.TemporaryDirectory() as tmp:
            pr = Path(tmp) / "pr.md"
            pr.write_text(example.group(1), encoding="utf-8")
            spec = REPO / "skills/spec/references/exemplo.md"
            self.assertEqual(check(pr, spec, Path(tmp)), [])


if __name__ == "__main__":
    unittest.main()
