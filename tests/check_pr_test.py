"""Testes do check_pr.py da skill open-pr. Rodar com:
python3 -m unittest discover -s tests -p '*_test.py'
"""
from __future__ import annotations

import contextlib
import io
import sys
import tempfile
import unittest
from pathlib import Path

SCRIPTS = Path(__file__).parents[1] / "skills/open-pr/scripts"
sys.path.insert(0, str(SCRIPTS))
from check_pr import check, main  # noqa: E402

SPEC_EXAMPLE = Path(__file__).parents[1] / "skills/spec/references/exemplo.md"

VALID = """\
Título: Cancelar reserva de sala

## Resumo
Permite cancelar uma reserva futura e liberar o horário.

## Critérios de aceite
| AC | Status | Evidência |
| --- | --- | --- |
| AC-001 | passou | `python3 -m unittest tests.test_booking.CancelTest` → OK |
| AC-002 | passou | `python3 -m unittest tests.test_booking.CancelInvalidTest` → OK |
| AC-003 | passou | `python3 -m unittest tests.test_booking.CancelTwiceTest` → OK |
| AC-Q01 | passou | `git grep -n "def release" app/booking.py` → app/booking.py:2 |

## Achados do review
Nenhum achado confirmado.

## Riscos e decisões
Nenhum.
"""


class PrCase(unittest.TestCase):
    def setUp(self):
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        self.root = Path(tmp.name)
        self.spec = self.root / "spec.md"
        self.spec.write_text(SPEC_EXAMPLE.read_text(encoding="utf-8"), encoding="utf-8")
        self.pr = self.root / "pr.md"

    def errors(self, text: str) -> list[str]:
        self.pr.write_text(text, encoding="utf-8")
        return check(self.pr, self.spec, self.root)

    def assertError(self, errors: list[str], *words: str) -> None:
        self.assertTrue(any(all(w in e for w in words) for e in errors), errors)


class PrTest(PrCase):
    def test_valid_pr_is_clean(self):
        self.assertEqual(self.errors(VALID), [])

    def test_title_rules(self):
        self.assertError(self.errors(VALID.replace("Título: Cancelar reserva de sala\n", "")), "título")
        self.assertError(self.errors(VALID.replace("Cancelar reserva de sala", "x" * 73, 1)), "título")
        self.assertError(self.errors(VALID.replace("de sala\n", "de sala.\n", 1)), "título", "ponto final")
        self.assertError(self.errors(VALID.replace("Título: Cancelar reserva de sala", "Título:")), "título")

    def test_missing_sections_are_reported(self):
        self.assertError(self.errors(VALID.replace("## Resumo\n", "## Outro\n")), "seção ausente", "Resumo")
        self.assertError(self.errors(VALID.replace("## Critérios de aceite", "## Critérios")),
                         "seção ausente", "Critérios de aceite")

    def test_empty_summary_is_an_error(self):
        text = VALID.replace("Permite cancelar uma reserva futura e liberar o horário.\n", "")
        self.assertError(self.errors(text), "Resumo")

    def test_ac_without_evidence_row_is_an_error(self):
        text = VALID.replace("| AC-003 | passou | `python3 -m unittest tests.test_booking.CancelTwiceTest` → OK |\n", "")
        self.assertError(self.errors(text), "AC sem evidência", "AC-003")

    def test_ac_with_dash_evidence_is_an_error(self):
        text = VALID.replace("`git grep -n \"def release\" app/booking.py` → app/booking.py:2", "—")
        self.assertError(self.errors(text), "AC sem evidência", "AC-Q01")

    def test_unknown_ac_is_an_error(self):
        self.assertError(self.errors(VALID.replace("| AC-Q01 |", "| AC-009 |")), "desconhecido", "AC-009")

    def test_pending_marker_is_an_error(self):
        text = VALID.replace("Nenhum.\n", "[PRECISA DECISÃO: qual?]\n")
        self.assertError(self.errors(text), "marcador pendente")

    def test_marker_inside_code_fence_is_ignored(self):
        text = VALID.replace("Nenhum.\n", "```\n[PRECISA DECISÃO: qual?]\n```\n")
        self.assertEqual(self.errors(text), [])

    def test_local_agent_plans_path_is_an_error(self):
        text = VALID.replace("Nenhum achado confirmado.", "Veja .agent_plans/reservas/findings.md")
        self.assertError(self.errors(text), "caminho local")

    def test_pending_only_for_manual_ac(self):
        text = VALID.replace("| AC-003 | passou |", "| AC-003 | pendente |")
        self.assertError(self.errors(text), "pendente", "AC-003")
        spec = SPEC_EXAMPLE.read_text(encoding="utf-8")
        head, tail = spec.split("### AC-003", 1)
        self.spec.write_text(head + "### AC-003" + tail.replace("- Tipo: teste", "- Tipo: manual", 1),
                             encoding="utf-8")
        self.assertEqual(self.errors(text), [])

    def test_placeholder_evidence_is_an_error(self):
        real = "`git grep -n \"def release\" app/booking.py` → app/booking.py:2"
        for fake in ("-", "--", "`—`", "…"):
            self.assertError(self.errors(VALID.replace(real, fake)), "AC sem evidência", "AC-Q01")

    def test_machine_path_and_secret_are_errors(self):
        for leak in ("/Users/lucas/Dev/x.py", "/home/ci/x.py", "ghp_" + "A" * 36,
                     "AKIAIOSFODNN7EXAMPLE", "-----BEGIN PRIVATE KEY-----"):
            text = VALID.replace("Nenhum achado confirmado.", f"saída: {leak}")
            self.assertError(self.errors(text), "vazamento")

    def test_ai_attribution_is_an_error(self):
        for line in ("🤖 Generated with [Claude Code](https://claude.com/claude-code)",
                     "Co-Authored-By: Claude <noreply@anthropic.com>"):
            self.assertError(self.errors(VALID.replace("Nenhum.\n", line + "\n")), "atribuição de IA")

    def test_body_file_must_match_the_pr_body(self):
        corpo = self.root / "pr-corpo.md"
        self.pr.write_text(VALID, encoding="utf-8")
        corpo.write_text(VALID.split("\n", 2)[2], encoding="utf-8")
        self.assertEqual(check(self.pr, self.spec, self.root), [])
        corpo.write_text("outro corpo\n", encoding="utf-8")
        self.assertError(check(self.pr, self.spec, self.root), "pr-corpo.md", "difere")

    def test_body_over_80_lines_is_an_error(self):
        text = VALID + "linha\n" * 80
        self.assertError(self.errors(text), "maior que 80 linhas")

    def test_open_fence_and_non_utf8(self):
        self.assertError(self.errors(VALID + "\n```\nabre\n"), "cerca de código aberta")
        self.pr.write_bytes(b"T\xc3\xadtulo: \xff\xfe\n")
        self.assertError(check(self.pr, self.spec, self.root), "não é UTF-8")


class CliTest(PrCase):
    def run_main(self, *argv: str) -> tuple[int, str]:
        out = io.StringIO()
        with contextlib.redirect_stdout(out), contextlib.redirect_stderr(io.StringIO()):
            code = main(list(argv))
        return code, out.getvalue()

    def test_exit_codes(self):
        self.pr.write_text(VALID, encoding="utf-8")
        self.assertEqual(self.run_main(str(self.pr), str(self.spec), str(self.root)), (0, "limpo\n"))
        self.pr.write_text(VALID.replace("| AC-Q01 |", "| AC-009 |"), encoding="utf-8")
        code, out = self.run_main(str(self.pr), str(self.spec), str(self.root))
        self.assertEqual(code, 1)
        self.assertIn("desconhecido", out)
        self.assertEqual(self.run_main("nao-existe.md", str(self.spec))[0], 2)
        self.assertEqual(self.run_main(str(self.pr), "nao-existe.md")[0], 2)
        self.assertEqual(self.run_main()[0], 2)


if __name__ == "__main__":
    unittest.main()
