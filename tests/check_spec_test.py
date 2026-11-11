"""Testes do check_spec.py da skill spec. Rodar com:
python3 -m unittest discover -s tests -p '*_test.py'
"""
from __future__ import annotations

import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

SCRIPTS = Path(__file__).parents[1] / "skills/spec/scripts"
sys.path.insert(0, str(SCRIPTS))
from check_spec import check  # noqa: E402

VALID = """\
# Spec: Cancelar reserva de sala
Status: rascunho · Brief: .agent_plans/reservas/brief.md · Modo: padrão

## Objetivo
Permitir cancelar uma reserva futura e liberar o horário.

## Entendimento
Quem reserva precisa desfazer o pedido sem chamar o suporte. Demonstração:
reservar 10h–11h, cancelar e reservar de novo o mesmo horário.

## Padrões aplicáveis
| Regra | Onde está |
| --- | --- |
| Nome de sala sempre em minúsculas | `AGENTS.md:3` |

## Referências no código
| Funcionalidade parecida | Local | O que imitar |
| --- | --- | --- |
| Criar reserva | `app/booking.py:2` | Validar antes de gravar |

## Reuso
| Termos buscados | Encontrado | Decisão |
| --- | --- | --- |
| cancel, remove, free_slot | `app/booking.py:2` | Adaptar: liberar horário já existe em `release` |

## Decisões
| Decisão | Alternativa mais simples | Por que não serve |
| --- | --- | --- |
| Cancelar apaga a reserva | Marcar como cancelada | Nenhum relatório usa o histórico |

## Escopo
- Permitido: `app/booking.py`, `tests/test_booking.py`
- Proibido: `app/db.py`
- Exige aprovação: migração, dependência nova
- Orçamento: arquivos novos 0 · abstrações novas 0 · dependências novas 0

## Matriz de casos
| Caso | Entrada ou estado | Resultado esperado | AC |
| --- | --- | --- | --- |
| Id vazio | `""` | erro de validação | AC-002 |
| Reserva inexistente | id desconhecido | erro "não encontrada" | AC-002 |
| Cancelar duas vezes | reserva já cancelada | segunda chamada falha sem efeito | fora de escopo |

## Critérios de aceite
### AC-001 Cancelar libera o horário
- QUANDO a reserva futura é cancelada ENTÃO o horário volta a ficar livre
- Verificação: `python3 -m unittest tests.test_booking.CancelTest` → OK
- Tipo: teste
### AC-002 Cancelar rejeita id inválido
- QUANDO o id é vazio ou desconhecido ENTÃO `cancel` levanta `ValueError`
- Verificação: `python3 -m unittest tests.test_booking.CancelInvalidTest` → OK
- Tipo: teste
### Critérios de qualidade
- AC-Q01 Usa `release` de `app/booking.py` · Verificação: `git grep -n "def release" app/booking.py`

## Tarefas
### T1 Cancelar reserva · Depende de: — · Cobre: AC-001, AC-002, AC-Q01
- Arquivos: modificar `app/booking.py`; testar `tests/test_booking.py`
- Interfaces: produz `cancel(booking_id: str) -> None`
- Pronto quando: `python3 -m unittest discover -s tests` → OK

## Rastreabilidade
| AC | Tarefas |
| --- | --- |
| AC-001 | T1 |
| AC-002 | T1 |
| AC-Q01 | T1 |
"""

VALID_FAST = """\
# Spec: Ordenar reservas do dia
Status: rascunho · Brief: — · Modo: rápido

## Objetivo
Listar as reservas do dia ordenadas por horário de início.

## Escopo
- Permitido: `app/booking.py`, `tests/test_booking.py`
- Proibido: `app/db.py`
- Exige aprovação: dependência nova
- Orçamento: arquivos novos 0 · abstrações novas 0 · dependências novas 0

## Critérios de aceite
### AC-001 Reservas em ordem
- QUANDO há reservas às 11h e às 9h ENTÃO a lista devolve 9h antes de 11h
- Verificação: `python3 -m unittest tests.test_booking.OrderTest` → OK
- Tipo: teste

## Tarefas
### T1 Ordenar a listagem · Depende de: — · Cobre: AC-001
- Arquivos: modificar `app/booking.py`; testar `tests/test_booking.py`
- Interfaces: —
- Pronto quando: `python3 -m unittest discover -s tests` → OK
"""


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


class CheckSpecTest(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self._tmp.cleanup)
        self.root = Path(self._tmp.name)
        # arquivos que VALID cita: AGENTS.md:3, app/booking.py:2 e o brief
        for name in ("AGENTS.md", "app/booking.py", ".agent_plans/reservas/brief.md"):
            path = self.root / name
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text("a\nb\nc\n")

    def errors(self, text: str | bytes) -> list[str]:
        spec = self.root / ".agent_plans/reservas/spec.md"
        spec.parent.mkdir(parents=True, exist_ok=True)
        spec.write_bytes(text if isinstance(text, bytes) else text.encode())
        return check(spec, self.root)

    def assertError(self, errs: list[str], *words: str):
        self.assertTrue(any(all(w in e for w in words) for e in errs), errs)

    def test_valid_standard_spec_is_clean(self):
        self.assertEqual(self.errors(VALID), [])

    def test_missing_section_is_error(self):
        self.assertError(self.errors(drop(VALID, "Matriz de casos")),
                         "seção ausente: Matriz de casos")

    def test_fast_mode_needs_only_four_sections(self):
        self.assertEqual(self.errors(VALID_FAST), [])

    def test_invalid_mode_or_status(self):
        self.assertError(self.errors(swap(VALID, "Modo: padrão", "Modo: lento")),
                         "Modo inválido: lento")
        self.assertError(self.errors(swap(VALID, "Status: rascunho", "Status: pronto")),
                         "Status inválido: pronto")
        header = "Status: rascunho · Brief: .agent_plans/reservas/brief.md · Modo: padrão\n"
        self.assertError(self.errors(swap(VALID, header, "")), "cabeçalho")

    def test_scope_needs_four_lines_and_numeric_budget(self):
        self.assertError(self.errors(swap(VALID, "- Proibido: `app/db.py`\n", "")),
                         'Escopo: falta "Proibido"')
        budget = "- Orçamento: arquivos novos 0 · abstrações novas 0 · dependências novas 0"
        self.assertError(self.errors(swap(VALID, budget, "- Orçamento: arquivos novos 1")),
                         "Escopo: Orçamento precisa dos três números")
        self.assertError(self.errors(swap(VALID, budget + "\n", "")),
                         'Escopo: falta "Orçamento"')

    def test_empty_investigation_table_is_error(self):
        rows = {
            "Padrões aplicáveis": "| Nome de sala sempre em minúsculas | `AGENTS.md:3` |\n",
            "Referências no código": "| Criar reserva | `app/booking.py:2` | Validar antes de gravar |\n",
            "Reuso": "| cancel, remove, free_slot | `app/booking.py:2` | "
                     "Adaptar: liberar horário já existe em `release` |\n",
        }
        for name, row in rows.items():
            self.assertError(self.errors(swap(VALID, row, "")), f"seção sem linhas: {name}")

    def test_reuse_row_needs_decision(self):
        text = swap(VALID, "Adaptar: liberar horário já existe em `release`", "talvez")
        self.assertError(self.errors(text),
                         "Reuso: linha sem decisão (Reusar, Adaptar ou Criar)")

    def test_decision_row_needs_simpler_alternative(self):
        text = swap(VALID, "| Cancelar apaga a reserva | Marcar como cancelada |",
                    "| Cancelar apaga a reserva |  |")
        self.assertError(self.errors(text), "Decisões: linha sem alternativa mais simples")

    def test_pipe_inside_backticks_does_not_split_cells(self):
        decision = "Adaptar: liberar horário já existe em `release`"
        for cell in ("Adaptar: veja `grep -E 'a|b'`", "Adaptar: veja `a\\|b`"):
            self.assertEqual(self.errors(swap(VALID, decision, cell)), [], cell)

    def test_ids_inside_code_fence_are_ignored(self):
        fenced = "\n```markdown\n## Matriz de casos\n| Caso | AC |\n```\n"
        text = drop(VALID, "Matriz de casos") + fenced
        self.assertError(self.errors(text), "seção ausente: Matriz de casos")

    def test_non_utf8_spec_does_not_crash(self):
        self.assertError(self.errors(VALID.encode() + b"\n<!-- caf\xe9 -->\n"), "não é UTF-8")

    AC1 = "- Verificação: `python3 -m unittest tests.test_booking.CancelTest` → OK\n"
    QUALITY = ("- AC-Q01 Usa `release` de `app/booking.py` · "
               'Verificação: `git grep -n "def release" app/booking.py`')
    COBRE = "Cobre: AC-001, AC-002, AC-Q01"

    def test_ac_without_verification_or_type(self):
        self.assertError(self.errors(swap(VALID, self.AC1, "")), 'AC-001: falta "Verificação"')
        self.assertError(self.errors(swap(VALID, self.AC1 + "- Tipo: teste\n", self.AC1)),
                         'AC-001: falta "Tipo"')
        self.assertError(self.errors(swap(VALID, self.AC1 + "- Tipo: teste",
                                          self.AC1 + "- Tipo: adivinhar")),
                         "AC-001: Tipo inválido: adivinhar")
        when = "- QUANDO a reserva futura é cancelada ENTÃO o horário volta a ficar livre\n"
        self.assertError(self.errors(swap(VALID, when, "")),
                         'AC-001: falta "QUANDO … ENTÃO …"')

    def test_test_or_command_ac_needs_backticked_command(self):
        manual = "- Verificação: rodar os testes\n"
        self.assertError(self.errors(swap(VALID, self.AC1, manual)),
                         "AC-001: Verificação sem comando entre crases")
        inspection = swap(VALID, self.AC1 + "- Tipo: teste\n", manual + "- Tipo: inspeção\n")
        self.assertEqual(self.errors(inspection), [])

    def test_duplicate_ac_id(self):
        text = swap(VALID, "### AC-002 Cancelar rejeita", "### AC-001 Cancelar rejeita")
        self.assertError(self.errors(text), "AC-001 duplicado")

    def test_spec_without_acs_is_error(self):
        block = "### AC-001 Reservas em ordem\n"
        start = VALID_FAST.index(block)
        end = VALID_FAST.index("## Tarefas")
        self.assertError(self.errors(VALID_FAST[:start] + "(nada)\n\n" + VALID_FAST[end:]),
                         "nenhum critério de aceite")

    def test_quality_criterion_must_name_file_or_command(self):
        text = swap(VALID, self.QUALITY, "- AC-Q01 Código limpo · Verificação: olhar")
        self.assertError(self.errors(text), "AC-Q01: não nomeia arquivo ou comando")
        text = swap(VALID, self.QUALITY, "- AC-Q01 Usa `release` de `app/booking.py`")
        self.assertError(self.errors(text), 'AC-Q01: falta "Verificação"')

    def test_task_must_cover_an_existing_ac(self):
        self.assertError(self.errors(swap(VALID, self.COBRE, "Cobre:")),
                         "T1: não cobre nenhum AC")
        self.assertError(self.errors(swap(VALID, self.COBRE, self.COBRE + ", AC-009")),
                         "T1: cobre AC-009, que não existe")

    def test_ac_without_task_is_error(self):
        text = swap(VALID, self.COBRE, "Cobre: AC-001, AC-Q01")
        self.assertError(self.errors(text), "AC-002: nenhuma tarefa o cobre")

    def test_task_dependency_must_exist(self):
        self.assertError(self.errors(swap(VALID, "Depende de: —", "Depende de: T9")),
                         "T1: depende de T9, que não existe")
        parallel = swap(VALID, "### T1 Cancelar reserva · Depende",
                        "### T1 Cancelar reserva · [P] · Depende")
        self.assertEqual(self.errors(parallel), [])

    def test_task_needs_files_and_ready_when(self):
        files = "- Arquivos: modificar `app/booking.py`; testar `tests/test_booking.py`\n"
        self.assertError(self.errors(swap(VALID, files, "")), 'T1: falta "Arquivos"')
        ready = "`python3 -m unittest discover -s tests` → OK"
        self.assertError(self.errors(swap(VALID, ready, "rodar tudo")),
                         'T1: falta "Pronto quando" com comando entre crases')

    def test_traceability_must_match_tasks(self):
        self.assertError(self.errors(swap(VALID, "| AC-001 | T1 |", "| AC-001 | T2 |")),
                         "Rastreabilidade: AC-001 lista T2, as tarefas dizem T1")
        self.assertError(self.errors(swap(VALID, "| AC-002 | T1 |\n", "")),
                         "Rastreabilidade: falta AC-002")

    def test_matrix_row_must_point_to_ac_or_out_of_scope(self):
        row = '| Id vazio | `""` | erro de validação | AC-002 |'
        head = '| Id vazio | `""` | erro de validação |'
        self.assertError(self.errors(swap(VALID, row, head + "  |")),
                         'Matriz de casos: "Id vazio" não aponta para um AC '
                         'nem para "fora de escopo"')
        self.assertError(self.errors(swap(VALID, row, head + " AC-009 |")),
                         'Matriz de casos: "Id vazio" aponta para AC-009, que não existe')
        self.assertEqual(self.errors(swap(VALID, row, head + " AC-001, AC-002 |")), [])

    def test_fast_mode_still_checks_ac_verification(self):
        self.assertError(self.errors(swap(VALID_FAST, "- Tipo: teste\n", "")),
                         'AC-001: falta "Tipo"')

    def test_pending_marker_fails(self):
        marker = "[PRECISA DECISÃO: quem é elegível]"
        text = swap(VALID, "Permitir cancelar uma reserva futura e liberar o horário.",
                    f"Permitir cancelar uma reserva futura. {marker}")
        line = text.splitlines().index(f"Permitir cancelar uma reserva futura. {marker}") + 1
        self.assertError(self.errors(text), f"spec.md:{line}:", "marcador pendente", marker)

    def test_marker_inside_fence_is_ignored(self):
        fenced = "\n```text\n[PRECISA DECISÃO: exemplo citado]\n```\n"
        self.assertEqual(self.errors(VALID + fenced), [])

    def test_citation_to_missing_file_or_line(self):
        cited = "| Criar reserva | `app/booking.py:2` |"
        self.assertError(self.errors(swap(VALID, cited, "| Criar reserva | `app/nada.py:4` |")),
                         "cita `app/nada.py:4`, que não existe")
        self.assertError(self.errors(swap(VALID, cited, "| Criar reserva | `app/booking.py:99` |")),
                         "cita `app/booking.py:99`, além do fim do arquivo")
        self.assertEqual(self.errors(swap(VALID, cited, "| Criar reserva | `app/booking.py:1-3` |")),
                         [])

    def test_plain_path_to_new_file_is_not_checked(self):
        text = swap(VALID, "- Permitido: `app/booking.py`", "- Permitido: `app/novo.py`, `app/booking.py`")
        self.assertEqual(self.errors(text), [])

    def test_citation_to_unknown_root_is_skipped(self):
        text = swap(VALID, "reservar 10h–11h", "reservar 10h–11h em `example.com:443` e `0.0.0.0:8000`")
        self.assertEqual(self.errors(text), [])

    def test_brief_must_exist_and_only_fast_mode_may_skip_it(self):
        brief = ".agent_plans/reservas/brief.md"
        self.assertError(self.errors(swap(VALID, brief, ".agent_plans/reservas/nada.md")),
                         "Brief inexistente: .agent_plans/reservas/nada.md")
        self.assertEqual(self.errors(swap(VALID, "Brief: " + brief, "Brief: —")), [])
        deep = swap(swap(VALID, "Brief: " + brief, "Brief: —"), "Modo: padrão", "Modo: profundo")
        self.assertError(self.errors(deep), "Modo profundo exige Brief")
        self.assertEqual(self.errors(VALID_FAST), [])

    def test_unclosed_fence_is_reported(self):
        text = VALID + "\n```\n[PRECISA DECISÃO: qual regra?]\n"
        self.assertError(self.errors(text), "cerca de código aberta")

    def test_citation_must_be_a_real_line_range_inside_the_root(self):
        for token, word in (("app/booking.py:0", "linha inválida"),
                            ("app/booking.py:3-1", "linha inválida"),
                            ("app:3", "diretório"),
                            ("app/../../fora.txt:1", "fora da raiz"),
                            ("./app/booking.py:99", "além do fim")):
            with self.subTest(token=token):
                text = swap(VALID, "reservar 10h–11h", f"reservar 10h–11h em `{token}`")
                self.assertError(self.errors(text), token, word)

    def test_non_utf8_file_gets_a_single_encoding_error(self):
        errs = self.errors(VALID.encode("latin-1", errors="replace"))
        self.assertEqual(len(errs), 1, errs)
        self.assertError(errs, "não é UTF-8")

    def run_cli(self, text: str, *extra: str) -> subprocess.CompletedProcess:
        spec = self.root / ".agent_plans/reservas/spec.md"
        spec.write_text(text)
        return subprocess.run([sys.executable, str(SCRIPTS / "check_spec.py"), str(spec), *extra],
                              capture_output=True, text=True)

    def test_cli_prints_limpo_and_exits_zero(self):
        result = self.run_cli(VALID, str(self.root))
        self.assertEqual((result.returncode, result.stdout.strip()), (0, "limpo"))

    def test_cli_prints_errors_and_exits_one(self):
        result = self.run_cli(swap(VALID, "Modo: padrão", "Modo: lento"), str(self.root))
        self.assertEqual(result.returncode, 1)
        self.assertRegex(result.stdout, r"spec\.md:\d+: Modo inválido: lento")

    def test_cli_missing_spec_exits_two(self):
        missing = self.root / "nada.md"
        result = subprocess.run([sys.executable, str(SCRIPTS / "check_spec.py"), str(missing)],
                                capture_output=True, text=True)
        self.assertEqual(result.returncode, 2)
        self.assertIn(f"spec não encontrada: {missing}", result.stderr)

    def test_ac_inside_code_fence_is_ignored(self):
        fenced = "```markdown\n### AC-009 Fantasma\n- QUANDO x ENTÃO y\n```\n"
        text = swap(VALID, "### Critérios de qualidade", fenced + "### Critérios de qualidade")
        self.assertEqual(self.errors(text), [])


if __name__ == "__main__":
    unittest.main()
