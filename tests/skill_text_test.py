"""Invariantes do texto da skill codebase-agent-docs (SKILL.md e templates.md).
Rodar com: python3 -m unittest discover -s tests -p '*_test.py'
"""
from __future__ import annotations

import re
import unittest
from pathlib import Path

SKILL = Path(__file__).parents[1] / "skills/codebase-agent-docs"
SKILL_MD = (SKILL / "SKILL.md").read_text()
TEMPLATES = (SKILL / "references/templates.md").read_text()
SKILL_MAX = 200
# respostas plantadas por tests/make-docs-fixture.sh: a skill não pode ensiná-las
FIXTURE_ANSWERS = ("slugify", "slug", "centavos?", "cents", "UTC", "HANDLERS",
                   "schema_gen", "legacy_export", "DATABASE_URL", r"app\.text",
                   "sms", "notify", "csv")


class SkillTextTest(unittest.TestCase):
    def test_does_not_leak_fixture_answers(self):
        pattern = re.compile(rf"\b(?:{'|'.join(FIXTURE_ANSWERS)})\b", re.I)
        for name, text in (("SKILL.md", SKILL_MD), ("templates.md", TEMPLATES)):
            self.assertEqual(pattern.findall(text), [], name)

    def test_skill_stays_within_line_cap(self):
        self.assertLessEqual(len(SKILL_MD.splitlines()), SKILL_MAX)

    def test_sources_are_in_backticks_so_check_docs_can_verify_them(self):
        for name, text in (("SKILL.md", SKILL_MD), ("templates.md", TEMPLATES)):
            self.assertEqual(re.findall(r"\(fonte: (?!`)[^)]*\)", text), [], name)

    def test_always_topics_are_fed_by_approved_candidates(self):
        self.assertTrue("`regra` e `comando`" in SKILL_MD, "SKILL.md sem a frase")

    def test_model_strategy_template_is_optional_and_sourced(self):
        found = re.search(r"## Estratégia de modelo\n\n<Opcional", TEMPLATES)
        self.assertTrue(found, "templates.md: seção de modelo não é opcional")


if __name__ == "__main__":
    unittest.main()
