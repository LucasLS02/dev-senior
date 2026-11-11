"""Testes do pontuador de findings.md. Rodar com:
python3 -m unittest discover -s tests -p '*_test.py'
"""
import tempfile
import unittest
from pathlib import Path

from score_findings import check_format, parse_expected, parse_findings, score

CONTRACT = Path(__file__).parents[1] / "skills/review-diff/references/achados.md"

EXPECTED = (
    "P1\tplantado\ta.py:10-12\t-\n"
    "P2\tplantado\tb.py:5-5|t.py:1-9\t-\n"
    "B1\tisca\ta.py:30-32\t-\n"
)


def block(id="RV-001", severidade="alto", arquivo="a.py", linhas="10-12",
          evidencia="a.py:11 divide por zero", veredito="confirmado"):
    return f"""```yaml
id: {id}
lente: correção
severidade: {severidade}
local: {{arquivo: {arquivo}, linhas: {linhas}}}
problema: divide por zero
viola: —
evidência: {evidencia}
impacto: lista vazia derruba a exportação
verificação: {{veredito: {veredito}, método: inspeção}}
correção: {{escopo: local, arquivos_esperados: [{arquivo}]}}
gatilho: —
status: aberto
```"""


def doc(*blocks, cobertura=True):
    text = "# Achados · teste\n\n" + "\n\n".join(blocks)
    return text + ("\n\n## Cobertura\n- Alvo: HEAD~1..HEAD\n" if cobertura else "\n")


def errors(text, root=None):
    return check_format(text, parse_findings(text), root)


class FormatTest(unittest.TestCase):
    def test_contract_example_is_valid(self):
        text = CONTRACT.read_text()
        self.assertEqual(check_format(text, parse_findings(text), None), [])

    def test_evidence_without_location_is_error(self):
        errs = errors(doc(block(evidencia="olhei o código")))
        self.assertTrue(any("RV-001" in e and "evidência" in e for e in errs), errs)

    def test_value_outside_contract_is_error(self):
        errs = errors(doc(block(severidade="urgente")))
        self.assertTrue(any("RV-001" in e and "severidade" in e for e in errs), errs)

    def test_duplicate_id_is_error(self):
        errs = errors(doc(block(), block(linhas="20-21", evidencia="a.py:20 x")))
        self.assertTrue(any("RV-001" in e and "repetido" in e for e in errs), errs)

    def test_missing_coverage_is_error(self):
        errs = errors(doc(block(), cobertura=False))
        self.assertTrue(any("Cobertura" in e for e in errs), errs)

    def test_line_beyond_file_is_error(self):
        with tempfile.TemporaryDirectory() as root:
            Path(root, "a.py").write_text("1\n2\n3\n4\n5\n")
            errs = errors(doc(block(linhas="4-9", evidencia="a.py:4 x")), Path(root))
        self.assertTrue(any("RV-001" in e and "linhas" in e for e in errs), errs)


class ScoreTest(unittest.TestCase):
    def test_score_counts_only_confirmed(self):
        findings = parse_findings(doc(
            block(id="RV-001", arquivo="a.py", linhas="11-11"),
            block(id="RV-002", arquivo="t.py", linhas="3-4", evidencia="t.py:3 x"),
            block(id="RV-003", arquivo="a.py", linhas="31-31", veredito="refutado"),
        ))
        r = score(findings, parse_expected(EXPECTED))
        self.assertEqual(r["recall"], 1.0)
        self.assertEqual(r["bait_hits"], [])

    def test_confirmed_bait_and_duplicates(self):
        findings = parse_findings(doc(
            block(id="RV-001", linhas="10-10"),
            block(id="RV-002", linhas="12-12", evidencia="a.py:12 x"),
            block(id="RV-003", linhas="31-31", evidencia="a.py:31 x"),
        ))
        r = score(findings, parse_expected(EXPECTED))
        self.assertEqual(r["bait_hits"], ["B1"])
        self.assertEqual(r["duplicates"], {"P1": 2})
        self.assertEqual(r["recall"], 0.5)
        self.assertEqual(r["missed"], ["P2"])


if __name__ == "__main__":
    unittest.main()
