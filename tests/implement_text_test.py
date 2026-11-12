"""Invariantes da skill implement: specs da avaliação e texto da skill.
Rodar com: python3 -m unittest discover -s tests -p '*_test.py'
"""
from __future__ import annotations

import re
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

REPO = Path(__file__).parents[1]
sys.path.insert(0, str(REPO / "skills/spec/scripts"))
from check_spec import check  # noqa: E402

sys.path.insert(0, str(REPO / "skills/implement/scripts"))
from check_run import progress  # noqa: E402

SPECS = REPO / "tests/implement-specs"
SKILL = REPO / "skills/implement"
SKILL_MAX = 200
# respostas plantadas por tests/make-docs-fixture.sh e pelas specs da avaliação
FIXTURE_ANSWERS = ("slugify", "slug", "HANDLERS", "dispatch", "sms", "centavos?", "cents",
                   "to_cents", "UTC", "money", "export_row", "notify_export_done")
GATES = [f"{k}{n}" for k, top in (("G", 9), ("S", 7), ("P", 4)) for n in range(1, top + 1)]


def read(*parts: str) -> str:
    return (SKILL.joinpath(*parts)).read_text(encoding="utf-8")


class EvalSpecsTest(unittest.TestCase):
    def test_eval_specs_pass_check_spec(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp) / "repo"
            subprocess.run([str(REPO / "tests/make-docs-fixture.sh"), str(root), "spec"],
                           check=True, capture_output=True)
            for mode, markers in (("feliz", 0), ("gatilho", 0), ("prontidao", 1)):
                target = root / f".agent_plans/{mode}/spec.md"
                target.parent.mkdir(parents=True)
                target.write_text((SPECS / f"{mode}.md").read_text(encoding="utf-8"), encoding="utf-8")
                errors = check(target, root)
                pending = [e for e in errors if "marcador pendente" in e]
                self.assertEqual(len(pending), markers, (mode, errors))
                self.assertEqual(errors, pending, (mode, errors))


class SkillTextTest(unittest.TestCase):
    def setUp(self):
        self.skill = read("SKILL.md")
        self.texts = {name: read(*name.split("/")) for name in (
            "SKILL.md", "references/pacote.md", "references/gatilhos.md",
            "references/modelo-progress.md")}

    def test_skill_stays_within_line_cap(self):
        self.assertLessEqual(len(self.skill.splitlines()), SKILL_MAX)

    def test_does_not_leak_fixture_answers(self):
        pattern = re.compile(rf"\b(?:{'|'.join(FIXTURE_ANSWERS)})\b", re.I)
        for name, text in self.texts.items():
            self.assertEqual(pattern.findall(text), [], name)

    def test_gatilhos_has_every_id_exactly_once(self):
        rows = re.findall(r"^\| (?:G|S|P)\d \|", self.texts["references/gatilhos.md"], re.M)
        self.assertEqual(sorted(r.strip("| ") for r in rows), sorted(GATES))

    def test_skill_uses_the_checker(self):
        for word in ("check_run.py", "triggers", "converge", "tree", "quality", "check_spec.py"):
            self.assertIn(word, self.skill)

    def test_skill_calls_the_other_skills(self):
        for name in ("review-diff", "pr-feedback", "smart-commit"):
            self.assertIn(name, self.skill)

    def test_skill_never_commits_or_pushes(self):
        self.assertIn("não commita", self.skill)
        self.assertIn("nunca faz push", self.skill)

    def test_progress_model_example_passes_the_checker(self):
        example = re.search(r"## Exemplo.*?```markdown\n(.*?)```", self.texts["references/modelo-progress.md"], re.S)
        self.assertIsNotNone(example, "modelo-progress.md sem bloco de exemplo")
        with tempfile.TemporaryDirectory() as tmp:
            prog = Path(tmp) / "progress.md"
            prog.write_text(example.group(1), encoding="utf-8")
            spec = REPO / "skills/spec/references/exemplo.md"
            self.assertEqual(progress(prog, spec, Path(tmp)), [])


if __name__ == "__main__":
    unittest.main()
