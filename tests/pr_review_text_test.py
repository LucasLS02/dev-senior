"""Invariantes do texto da skill pr-review (SKILL.md).
Rodar com: python3 -m unittest discover -s tests -p '*_test.py'
"""
from __future__ import annotations

import re
import unittest
from pathlib import Path

SKILL = Path(__file__).parents[1] / "skills/pr-review/SKILL.md"
SKILL_MAX = 200


class PrReviewTextTest(unittest.TestCase):
    def setUp(self):
        self.skill = SKILL.read_text(encoding="utf-8")

    def section(self, title: str) -> str:
        found = re.search(rf"^### {title}\n(.*?)(?=^##+ |\Z)", self.skill, re.M | re.S)
        self.assertIsNotNone(found, f"SKILL.md sem a seção {title}")
        return found.group(1)

    def test_stays_within_line_cap(self):
        self.assertLessEqual(len(self.skill.splitlines()), SKILL_MAX)

    def test_filter_drops_points_already_fixed_in_an_earlier_round(self):
        text = self.section(r"4\. Filtro")
        for word in ("outra rodada", "isResolved", "código atual", "corrigido"):
            self.assertIn(word, text)

    def test_filter_keeps_points_raised_but_still_unresolved(self):
        text = self.section(r"4\. Filtro")
        self.assertIn("ainda aberto", text)
        self.assertIn("mantém", text.lower())

    def test_gate_lists_fixed_and_still_open_points(self):
        text = self.section(r"5\. GATE: aprovação")
        self.assertIn("Já corrigidos", text)
        self.assertIn("Ainda abertos", text)

    def test_every_comment_is_anchored_on_a_diff_line(self):
        gate = self.section(r"5\. GATE: aprovação")
        posting = self.section(r"6\. Postagem")
        self.assertIn("ancorado", posting)
        self.assertIn("linha alterada", posting)
        for text in (gate, posting):
            self.assertNotIn("agrupados", text)
            self.assertNotIn("entra no `body`", text)

    def test_review_diff_colleague_profile_does_not_group_findings(self):
        review_diff = (SKILL.parents[1] / "review-diff/SKILL.md").read_text(encoding="utf-8")
        row = next(l for l in review_diff.splitlines() if l.startswith("| `colega`"))
        self.assertNotIn("agrupados", row)


if __name__ == "__main__":
    unittest.main()
