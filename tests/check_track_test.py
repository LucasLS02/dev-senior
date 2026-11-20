"""Contratos determinísticos da reconciliação de acompanhamento."""
import importlib.util
import unittest
from pathlib import Path

SCRIPT = Path(__file__).parents[1] / "skills/track/scripts/check_track.py"
spec = importlib.util.spec_from_file_location("check_track", SCRIPT)
track = importlib.util.module_from_spec(spec)
spec.loader.exec_module(track)


class TrackTest(unittest.TestCase):
    def test_publication_requires_approved_spec_and_ready_progress(self):
        self.assertEqual(track.local_events("Status: rascunho", ""), [])
        self.assertEqual(track.local_events("Status: aprovado", ""), [])
        self.assertEqual(track.local_events("Status: aprovado", PROGRESS), ["início"])

    def test_escalations_only_block_on_external_dependency(self):
        progress = PROGRESS + "\n## Escaladas e decisões\n" + ESCALATION
        self.assertEqual(track.local_events("Status: aprovado", progress),
                         ["início", "impedimento 1"])
        self.assertEqual(track.local_events("Status: aprovado", progress.replace("S1", "S2")),
                         ["início"])
        self.assertEqual(track.local_events("Status: aprovado", progress.replace("Decisão: pendente", "Decisão: manter")),
                         ["início", "impedimento 1", "decisão 1"])

    def test_delivery_requires_convergence_and_no_pending_escalation(self):
        done = PROGRESS.replace("| T1 | pendente |", "| T1 | concluída |")
        spec = "Status: aprovado\n## Tarefas\n### T1 Fazer\n"
        self.assertNotIn("entrega", track.local_events(spec, done))
        self.assertIn("entrega", track.local_events(spec, done, converged=True))
        self.assertNotIn("entrega", track.local_events(spec, done + "\n## Escaladas e decisões\n" + ESCALATION, converged=True))

    def test_missing_tasks_and_incomplete_readiness_do_not_publish_delivery(self):
        spec = "Status: aprovado\n## Tarefas\n### T1 Fazer\n### T2 Rever\n"
        done = PROGRESS.replace("| T1 | pendente |", "| T1 | concluída |")
        self.assertNotIn("entrega", track.local_events(spec, done, converged=True))
        self.assertEqual(track.local_events(spec, done.replace("| Árvore limpa | ok |\n", "")), [])

    def test_tracker_format_requires_context_and_authorization_scope(self):
        self.assertTrue(track.validate_tracker("# Acompanhamento\n"))
        self.assertEqual(track.validate_tracker(TRACKER), [])
        self.assertTrue(track.validate_tracker(TRACKER.replace("Rotina: não concedida", "Rotina: concedida")))

    def test_remote_events_prevent_repeated_comments_without_cache(self):
        comments = ["Começamos.\n\n— fluxo: fluxo-abc início"]
        self.assertEqual(track.missing_events(["início", "entrega"], comments, "fluxo-abc"), ["entrega"])
        self.assertEqual(track.missing_events(["início"], comments, "fluxo-def"), ["início"])
        self.assertEqual(track.missing_events(["início"], ["— fluxo: fluxo-abc início extra"], "fluxo-abc"), ["início"])

    def test_section_conflict_and_leak(self):
        self.assertTrue(track.section_conflict("manual", "nova", None))
        self.assertFalse(track.section_conflict("igual", "igual", None))
        self.assertFalse(track.section_conflict("antiga", "nova", track.section_hash("antiga")))
        self.assertTrue(track.section_conflict("", "nova", track.section_hash("antiga")))
        self.assertTrue(track.has_leak("/Users/pessoa/arquivo"))
        self.assertTrue(track.has_leak("veja app/foo.py:42"))
        self.assertTrue(track.has_leak("veja app/foo.py"))
        self.assertFalse(track.has_leak("AC-001 foi verificado"))
        self.assertFalse(track.has_leak("PR https://github.com/owner/repo/pull/1"))

    def test_multiple_gates_recognize_external_block(self):
        progress = PROGRESS + "\n## Escaladas e decisões\n" + ESCALATION.replace("S1", "G6, S1")
        self.assertIn("impedimento 1", track.local_events("Status: aprovado", progress))

    def test_duplicate_escalation_ids_are_rejected(self):
        progress = PROGRESS + "\n## Escaladas e decisões\n" + ESCALATION + ESCALATION
        with self.assertRaises(ValueError):
            track.local_events("Status: aprovado", progress)

    def test_diff_compares_remote_and_preserves_conflicting_description(self):
        desired = {"section": "nova", "status": "em andamento", "blocked": True,
                   "events": ["início"], "marker": "fluxo-abc"}
        remote = {"section": "editada", "status": "em review", "blocked": False,
                  "comments": []}
        result = track.reconcile(desired, remote, track.section_hash("antiga"))
        self.assertEqual(result, {"section": "conflito", "status": True,
                                  "blocked": True, "events": ["início"]})
        desired["section"] = "editada"
        remote.update({"status": "em andamento", "blocked": True,
                       "comments": ["— fluxo: fluxo-abc início"]})
        self.assertEqual(track.reconcile(desired, remote, None),
                         {"section": "igual", "status": False, "blocked": False, "events": []})


PROGRESS = """## Prontidão
| Checagem | Resultado |
| --- | --- |
| check_spec.py limpo | ok |
| Status aprovado | ok |
| Sem marcador pendente | ok |
| Árvore limpa | ok |
## Tarefas
| T | Status | Arquivos alterados | Verificação |
| --- | --- | --- | --- |
| T1 | pendente | — | — |
"""
ESCALATION = """### Escalada 1
Gatilho: S1 · Tarefa ou achado: T1
Motivo: conflito
Arquivos: app/foo.py
Efeito: indisponível
Alternativas: manter
Recomendação: manter
Decisão: pendente
"""
TRACKER = """# Acompanhamento
## Contexto
- Ferramenta: GitHub
- Projeto: owner/repo
- Repositório: github.com/owner/repo
- Pasta: exemplo
- Marcador: fluxo-123
## Vínculos
- Story: —
## Autorização
- Rotina: não concedida
- Escopo: —
- Evidência: —
## Estado observado
- Hash da seção: —
## Log
"""

if __name__ == "__main__":
    unittest.main()
