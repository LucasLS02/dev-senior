"""Invariantes da skill implement: specs da avaliação e texto da skill.
Rodar com: python3 -m unittest discover -s tests -p '*_test.py'
"""
from __future__ import annotations

import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

REPO = Path(__file__).parents[1]
sys.path.insert(0, str(REPO / "skills/spec/scripts"))
from check_spec import check  # noqa: E402

SPECS = REPO / "tests/implement-specs"


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


if __name__ == "__main__":
    unittest.main()
