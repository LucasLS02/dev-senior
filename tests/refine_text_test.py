"""Invariantes do texto da skill refine (SKILL.md, modelo.md e exemplo.md).
Rodar com: python3 -m unittest discover -s tests -p '*_test.py'
"""
from __future__ import annotations

import re
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).parents[1]
SKILL = ROOT / "skills/refine"
sys.path.insert(0, str(SKILL / "scripts"))
from check_brief import check  # noqa: E402

TEXTS = {name: (SKILL / path).read_text() for name, path in (
    ("SKILL.md", "SKILL.md"), ("modelo.md", "references/modelo.md"),
    ("exemplo.md", "references/exemplo.md"))}
SKILL_MAX = 200
# respostas plantadas por tests/make-docs-fixture.sh e tests/refine.eval.sh: a skill não pode ensiná-las
FIXTURE_ANSWERS = ("slugify", "slug", "HANDLERS", "dispatch", "sms", "centavos?", "cents",
                   "to_cents", "UTC", "schema_gen", "ValueError", "money")
CITED = re.compile(r"`([^`\s:]+):(\d+)(?:-(\d+))?`")


def write_cited_files(root: Path, text: str) -> None:
    lines: dict[str, int] = {}
    for path, first, last in CITED.findall(text):
        lines[path] = max(lines.get(path, 0), int(last or first))
    for path, count in lines.items():
        (root / path).parent.mkdir(parents=True, exist_ok=True)
        (root / path).write_text("x\n" * count)


class RefineTextTest(unittest.TestCase):
    def test_does_not_leak_fixture_answers(self):
        pattern = re.compile(rf"\b(?:{'|'.join(FIXTURE_ANSWERS)})\b", re.I)
        for name, text in TEXTS.items():
            self.assertEqual(pattern.findall(text), [], name)

    def test_skill_stays_within_line_cap(self):
        self.assertLessEqual(len(TEXTS["SKILL.md"].splitlines()), SKILL_MAX)

    def test_example_brief_passes_validator(self):
        example = TEXTS["exemplo.md"]
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            write_cited_files(root, example)
            brief = root / "brief.md"
            brief.write_text(example)
            self.assertEqual(check(brief, root), [])

    def test_skill_runs_the_validator(self):
        for needle in ("check_brief.py", "[PRECISA DECISÃO"):
            self.assertIn(needle, TEXTS["SKILL.md"])

    def test_spec_eval_brief_is_still_a_valid_brief(self):
        script = (ROOT / "tests/spec.eval.sh").read_text()
        body = re.search(r'cat > ".agent_plans/\$slug/brief.md" <<EOF\n(.*?)\nEOF\n', script, re.S)[1]
        body = body.replace("$title", "Aviso quando a exportação terminar")
        body = body.replace("$rule", "avisando a operação").replace("\\`", "`")
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            brief = root / "brief.md"
            brief.write_text(body + "\n")
            self.assertEqual(check(brief, root), [])


if __name__ == "__main__":
    unittest.main()
