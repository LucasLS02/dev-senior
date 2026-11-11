"""Testes do check_brief.py da skill refine. Rodar com:
python3 -m unittest discover -s tests -p '*_test.py'
"""
from __future__ import annotations

import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

SCRIPTS = Path(__file__).parents[1] / "skills/refine/scripts"
sys.path.insert(0, str(SCRIPTS))
from check_brief import check  # noqa: E402

VALID = """\
# Brief: Cancelar reserva de sala
Status: rascunho · Origem: card-7 · Modo: padrão

## Problema
Quem reserva uma sala e desiste precisa chamar o suporte para liberar o horário;
o suporte registrou 14 pedidos assim no mês. Hoje só `app/booking.py:2` cria
reservas.

## Pedido vs. necessidade
Pedido: um botão de cancelar. Necessidade: o horário voltar a ficar livre sem
depender de uma pessoa do suporte.

## Apetite
Modo padrão: mexe em dado de reserva, mas em um arquivo só.
Pequeno: um dia.

## Referências de mercado
| Fonte | Como resolve | O que aproveitar |
| --- | --- | --- |
| — | — | — |

## Opções consideradas
| Opção | Prós | Contras | Veredito |
| --- | --- | --- | --- |
| Não fazer | Sem custo | O suporte segue cancelando à mão | Descartada |
| Resolver sem código | O suporte cancela por formulário | Não elimina a espera | Descartada |
| Cancelar pela própria pessoa | Libera na hora, sem suporte | Precisa tratar cancelamento repetido | Recomendada |

## Recomendação
Permitir que quem reservou cancele uma reserva futura, liberando o horário.

## Fora de escopo
Reembolso, aviso aos demais participantes, histórico de cancelamentos.

## Riscos e armadilhas
Cancelar duas vezes a mesma reserva não pode liberar o horário de outra pessoa.

## Perguntas em aberto
Nenhuma.
"""

DIAGNOSTIC = """\
## Diagnóstico
- Reprodução: `python3 -c "from app.booking import reserve; reserve('', 10)"` → `KeyError`
- Causa raiz: `app/booking.py:2` indexa o dicionário antes de validar o id
- Comportamento atual: id vazio derruba a chamada com `KeyError`
- Comportamento esperado: erro de validação com mensagem legível
- Deve permanecer igual: reservas com id válido

"""
VALID_BUG = VALID.replace("## Apetite\n", DIAGNOSTIC + "## Apetite\n")

SECTIONS = ("Problema", "Pedido vs. necessidade", "Apetite", "Referências de mercado",
            "Opções consideradas", "Recomendação", "Fora de escopo", "Riscos e armadilhas",
            "Perguntas em aberto")
NOT_DOING = "| Não fazer | Sem custo | O suporte segue cancelando à mão | Descartada |"
WITHOUT_CODE = "| Resolver sem código | O suporte cancela por formulário | Não elimina a espera | Descartada |"
RECOMMENDED = ("| Cancelar pela própria pessoa | Libera na hora, sem suporte | "
               "Precisa tratar cancelamento repetido | Recomendada |")


def swap(text: str, old: str, new: str) -> str:
    """Troca `old` por `new`, falhando alto se `old` não existir (teste sem efeito)."""
    assert old in text, old
    return text.replace(old, new)


def drop(text: str, heading: str) -> str:
    """Remove a seção `## heading` inteira."""
    head, _, rest = text.partition(f"## {heading}\n")
    assert rest, heading
    _, sep, tail = rest.partition("\n## ")
    return head + (sep[1:] + tail if sep else "")


class CheckBriefTest(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self._tmp.cleanup)
        self.root = Path(self._tmp.name)
        # arquivos que VALID cita: app/booking.py:2 (e o AGENTS.md)
        for name in ("AGENTS.md", "app/booking.py"):
            path = self.root / name
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text("a\nb\nc\n")

    def errors(self, text: str | bytes) -> list[str]:
        brief = self.root / ".agent_plans/reservas/brief.md"
        brief.parent.mkdir(parents=True, exist_ok=True)
        brief.write_bytes(text if isinstance(text, bytes) else text.encode())
        return check(brief, self.root)

    def assertError(self, errs: list[str], *words: str):
        self.assertTrue(any(all(w in e for w in words) for e in errs), errs)

    def test_valid_brief_is_clean(self):
        self.assertEqual(self.errors(VALID), [])

    def test_valid_bug_brief_is_clean(self):
        self.assertEqual(self.errors(VALID_BUG), [])

    def test_discarded_brief_is_clean(self):
        text = swap(VALID, "Status: rascunho", "Status: descartado")
        text = swap(text, NOT_DOING, NOT_DOING.replace("Descartada", "Recomendada"))
        text = swap(text, RECOMMENDED, RECOMMENDED.replace("Recomendada", "Descartada"))
        self.assertEqual(self.errors(text), [])

    def test_header_and_title_are_required_and_valid(self):
        self.assertError(self.errors(drop_line(VALID, "Status:")), "cabeçalho")
        self.assertError(self.errors(drop_line(VALID, "# Brief:")), "cabeçalho")
        self.assertError(self.errors(swap(VALID, "Status: rascunho", "Status: pronto")),
                         "cabeçalho", "Status")
        self.assertError(self.errors(swap(VALID, "Modo: padrão", "Modo: lento")),
                         "cabeçalho", "Modo")
        self.assertError(self.errors(swap(VALID, " · Origem: card-7", "")), "cabeçalho")

    def test_every_section_is_required(self):
        for name in SECTIONS:
            with self.subTest(section=name):
                self.assertError(self.errors(drop(VALID, name)), f"seção ausente: {name}")

    def test_appetite_records_the_mode_and_the_reason(self):
        self.assertError(self.errors(drop_line(VALID, "Modo padrão:")), "Apetite")
        self.assertError(self.errors(swap(VALID, "Modo padrão:", "Modo profundo:")), "Apetite")
        self.assertError(self.errors(swap(VALID, "Modo padrão: mexe em dado de reserva, mas em um arquivo só.",
                                          "Modo padrão:")), "Apetite")

    def test_request_and_need_are_both_stated(self):
        self.assertError(self.errors(swap(VALID, "Necessidade:", "Resultado:")),
                         "Pedido vs. necessidade")
        self.assertError(self.errors(swap(VALID, "Pedido:", "Ideia:")), "Pedido vs. necessidade")

    def test_market_table_needs_a_row_with_a_checkable_source(self):
        table = "| — | — | — |"
        self.assertError(self.errors(drop_line(VALID, table)), "Referências")
        self.assertError(self.errors(swap(VALID, table, "| Blog de um amigo | Cancela | Tudo |")),
                         "Referências")
        self.assertEqual(self.errors(swap(VALID, table, "| https://example.com/x | a | b |")), [])
        self.assertEqual(self.errors(swap(VALID, table, "| `docs/agents/reuse.md` | a | b |")), [])

    def test_options_need_three_rows_including_the_two_mandatory_ones(self):
        self.assertError(self.errors(drop_line(VALID, WITHOUT_CODE)), "Opções")
        self.assertError(self.errors(swap(VALID, "Não fazer", "Adiar")), "Opções", "não fazer")
        self.assertError(self.errors(swap(VALID, "Resolver sem código", "Resolver à mão")),
                         "Opções", "sem código")

    def test_options_verdicts_and_single_recommendation(self):
        self.assertError(self.errors(swap(VALID, "| Recomendada |", "| Talvez |")), "Opções", "Veredito")
        self.assertError(self.errors(swap(VALID, NOT_DOING, NOT_DOING.replace("Descartada", "Recomendada"))),
                         "Opções", "uma")
        self.assertError(self.errors(swap(VALID, "| Recomendada |", "| Descartada |")), "Opções", "uma")

    def test_discarded_status_requires_not_doing_as_the_recommendation(self):
        self.assertError(self.errors(swap(VALID, "Status: rascunho", "Status: descartado")),
                         "descartado")

    def test_more_than_five_open_questions_is_an_error(self):
        questions = "\n".join(f"- [PRECISA DECISÃO: pergunta {i}?]" for i in range(6))
        text = swap(VALID, "## Perguntas em aberto\nNenhuma.", "## Perguntas em aberto\n" + questions)
        errs = self.errors(text)
        self.assertError(errs, "mais de cinco")
        self.assertEqual(sum("marcador pendente" in e for e in errs), 6)

    def test_open_questions_section_must_not_be_empty(self):
        text = swap(VALID, "## Perguntas em aberto\nNenhuma.\n", "## Perguntas em aberto\n")
        self.assertError(self.errors(text), "Perguntas em aberto")

    def test_pending_marker_is_reported_with_its_line(self):
        text = swap(VALID, "Nenhuma.\n", "- [PRECISA DECISÃO: quem cancela?]\n")
        errs = self.errors(text)
        self.assertEqual(len(errs), 1, errs)
        self.assertError(errs, "brief.md:", "marcador pendente", "quem cancela")

    def test_marker_inside_code_fence_is_ignored(self):
        text = swap(VALID, "Nenhuma.\n", "Nenhuma.\n\n```\n[PRECISA DECISÃO: exemplo]\n```\n")
        self.assertEqual(self.errors(text), [])

    def test_diagnostic_needs_the_five_lines(self):
        for label in ("Reprodução", "Causa raiz", "Comportamento atual", "Comportamento esperado",
                      "Deve permanecer igual"):
            with self.subTest(label=label):
                self.assertError(self.errors(drop_line(VALID_BUG, f"- {label}:")), "Diagnóstico", label)

    def test_diagnostic_reproduction_has_a_command_and_the_cause_a_citation(self):
        no_command = swap(VALID_BUG, "`python3 -c \"from app.booking import reserve; reserve('', 10)\"` → `KeyError`",
                          "rodar a reserva com id vazio")
        self.assertError(self.errors(no_command), "Diagnóstico", "Reprodução")
        no_cite = swap(VALID_BUG, "`app/booking.py:2` indexa", "o módulo de reservas indexa")
        self.assertError(self.errors(no_cite), "Diagnóstico", "Causa raiz")

    def test_citation_to_missing_file_or_line(self):
        self.assertError(self.errors(swap(VALID, "`app/booking.py:2`", "`app/nada.py:2`")),
                         "cita", "não existe")
        self.assertError(self.errors(swap(VALID, "`app/booking.py:2`", "`app/booking.py:9`")),
                         "cita", "além do fim")

    def test_citation_must_be_a_real_line_range_inside_the_root(self):
        for token, word in (("app/booking.py:0", "linha inválida"),
                            ("app/booking.py:3-1", "linha inválida"),
                            ("app:3", "diretório"),
                            ("app/../../fora.txt:1", "fora da raiz"),
                            ("./app/booking.py:99", "além do fim")):
            with self.subTest(token=token):
                text = swap(VALID, "`app/booking.py:2`", f"`{token}`")
                self.assertError(self.errors(text), token, word)

    def test_citation_to_unknown_root_is_skipped(self):
        text = swap(VALID, "14 pedidos", "14 pedidos (`example.com:443` e `0.0.0.0:8000`)")
        self.assertEqual(self.errors(text), [])

    def test_pipe_inside_backticks_is_not_a_cell_break(self):
        text = swap(VALID, "| Sem custo |", "| Sem custo, nem `a|b` |")
        self.assertEqual(self.errors(text), [])

    def test_non_utf8_file_gets_a_single_encoding_error(self):
        errs = self.errors(VALID.encode("latin-1", errors="replace"))
        self.assertEqual(len(errs), 1, errs)
        self.assertError(errs, "não é UTF-8")

    def test_unclosed_fence_is_reported(self):
        text = VALID + "\n```\n[PRECISA DECISÃO: qual regra?]\n"
        self.assertError(self.errors(text), "cerca de código aberta")

    def run_cli(self, text: str, *extra: str) -> subprocess.CompletedProcess:
        brief = self.root / ".agent_plans/reservas/brief.md"
        brief.parent.mkdir(parents=True, exist_ok=True)
        brief.write_text(text)
        return subprocess.run([sys.executable, str(SCRIPTS / "check_brief.py"), str(brief), *extra],
                              capture_output=True, text=True, check=False)

    def test_cli_exit_codes(self):
        clean = self.run_cli(VALID, str(self.root))
        self.assertEqual((clean.returncode, clean.stdout.strip()), (0, "limpo"))
        broken = self.run_cli(drop(VALID, "Problema"), str(self.root))
        self.assertEqual(broken.returncode, 1)
        self.assertIn("seção ausente: Problema", broken.stdout)
        missing = subprocess.run([sys.executable, str(SCRIPTS / "check_brief.py"),
                                  str(self.root / "nada.md")],
                                 capture_output=True, text=True, check=False)
        self.assertEqual(missing.returncode, 2)
        self.assertIn("não encontrado", missing.stderr)


def drop_line(text: str, needle: str) -> str:
    """Remove a primeira linha que contém `needle`, falhando alto se não houver."""
    lines = text.splitlines(keepends=True)
    hit = next((i for i, line in enumerate(lines) if needle in line), None)
    assert hit is not None, needle
    return "".join(lines[:hit] + lines[hit + 1:])


if __name__ == "__main__":
    unittest.main()
