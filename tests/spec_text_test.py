"""Invariantes do texto da skill spec (SKILL.md, modelo.md e exemplo.md).
Rodar com: python3 -m unittest discover -s tests -p '*_test.py'
"""
from __future__ import annotations

import re
import sys
import tempfile
import unittest
from pathlib import Path

SKILL = Path(__file__).parents[1] / "skills/spec"
sys.path.insert(0, str(SKILL / "scripts"))
from check_spec import check  # noqa: E402

TEXTS = {name: (SKILL / path).read_text() for name, path in (
    ("SKILL.md", "SKILL.md"), ("modelo.md", "references/modelo.md"),
    ("exemplo.md", "references/exemplo.md"))}
SKILL_MAX = 200
# respostas plantadas por tests/make-docs-fixture.sh e tests/spec.eval.sh: a skill não pode ensiná-las
FIXTURE_ANSWERS = ("slugify", "slug", "HANDLERS", "dispatch", "sms", "centavos?", "cents",
                   "to_cents", "UTC", "schema_gen", "elegíve(?:l|is)", "ponto e vírgula")
CITED = re.compile(r"`([^`\s:]+):(\d+)(?:-(\d+))?`")


class SpecTextTest(unittest.TestCase):
    def test_does_not_leak_fixture_answers(self):
        pattern = re.compile(rf"\b(?:{'|'.join(FIXTURE_ANSWERS)})\b", re.I)
        for name, text in TEXTS.items():
            self.assertEqual(pattern.findall(text), [], name)

    def test_skill_stays_within_line_cap(self):
        self.assertLessEqual(len(TEXTS["SKILL.md"].splitlines()), SKILL_MAX)

    def test_example_spec_passes_validator(self):
        example = TEXTS["exemplo.md"]
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            lines: dict[str, int] = {}
            for path, first, last in CITED.findall(example):
                lines[path] = max(lines.get(path, 0), int(last or first))
            for path, count in lines.items():
                (root / path).parent.mkdir(parents=True, exist_ok=True)
                (root / path).write_text("x\n" * count)
            brief = re.search(r"Brief: (\S+)", example)[1]
            (root / brief).parent.mkdir(parents=True, exist_ok=True)
            (root / brief).write_text("# Brief\n")
            spec = root / "spec.md"
            spec.write_text(example)
            self.assertEqual(check(spec, root), [])

    def test_skill_runs_the_validator(self):
        for needle in ("check_spec.py", "[PRECISA DECISÃO"):
            self.assertIn(needle, TEXTS["SKILL.md"])


if __name__ == "__main__":
    unittest.main()
