"""Testes do check_run.py da skill implement. Rodar com:
python3 -m unittest discover -s tests -p '*_test.py'
"""
from __future__ import annotations

import contextlib
import io
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

SCRIPTS = Path(__file__).parents[1] / "skills/implement/scripts"
sys.path.insert(0, str(SCRIPTS))
from check_run import converge, fingerprint, main, progress, quality, triggers  # noqa: E402

SPEC_EXAMPLE = Path(__file__).parents[1] / "skills/spec/references/exemplo.md"

SCOPE = """\
# Spec: escopo de teste
Status: aprovado · Brief: — · Modo: rápido

## Escopo
- Permitido: `app/`, `tests/`
- Proibido: `app/zone.py`
- Exige aprovação: —
- Orçamento: arquivos novos {budget} · abstrações novas 0 · dependências novas 0
"""


def git(root: Path, *args: str) -> None:
    subprocess.run(["git", "-c", "user.name=t", "-c", "user.email=t@example.invalid",
                    "-C", str(root), *args], check=True, capture_output=True)


class RepoCase(unittest.TestCase):
    """Repositório git temporário com um commit, e uma spec de escopo fora do diff."""

    def setUp(self):
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        self.root = Path(tmp.name)
        git(self.root, "init", "-q")
        self.write("app/a.py", "def public():\n    return 1\n\n\ndef _private():\n    return 2\n")
        self.write("app/other.py", "X = 1\n")
        self.write("app/zone.py", "Z = 1\n")
        self.write("app/auth.py", "A = 1\n")
        self.write("docs/x.md", "texto\n")
        self.write("requirements.txt", "pytest\n")
        self.write("tests/test_a.py", "import unittest\n\n\nclass T(unittest.TestCase):\n"
                   "    def test_a(self):\n        self.assertEqual(1, 1)\n")
        git(self.root, "add", "-A")
        git(self.root, "commit", "-q", "-m", "init")
        self.spec = self.write(".agent_plans/x/spec.md", SCOPE.format(budget=0))

    def write(self, rel: str, text: str) -> Path:
        path = self.root / rel
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text, encoding="utf-8")
        return path

    def found(self) -> list[str]:
        return triggers(self.spec, self.root)

    def assertHas(self, items: list[str], gate: str, path: str) -> None:
        self.assertTrue(any(i.startswith(f"{gate} {path}:") for i in items), items)

    def assertLacks(self, items: list[str], gate: str) -> None:
        self.assertFalse(any(i.startswith(f"{gate} ") for i in items), items)


class ScopeTest(RepoCase):
    def test_clean_tree_is_clean(self):
        self.assertEqual(self.found(), [])

    def test_allowed_change_is_clean(self):
        self.write("app/a.py", "def public():\n    return 1\n\n\ndef _private():\n    return 2\n# nota\n")
        self.assertEqual(self.found(), [])

    def test_change_outside_permitted_is_g1(self):
        self.write("docs/x.md", "outro\n")
        self.assertHas(self.found(), "G1", "docs/x.md")

    def test_change_inside_proibido_is_g1(self):
        self.write("app/zone.py", "Z = 2\n")
        items = self.found()
        self.assertHas(items, "G1", "app/zone.py")
        self.assertIn("Proibido", " ".join(items))

    def test_untracked_file_outside_scope_is_g1(self):
        self.write("scripts/new.py", "print(1)\n")
        self.assertHas(self.found(), "G1", "scripts/new.py")

    def test_agent_plans_changes_are_ignored(self):
        self.write(".agent_plans/x/progress.md", "# Progresso\n")
        self.write(".agent_plans/x/findings.md", "# Achados\n")
        self.assertEqual(self.found(), [])


class DiffTriggersTest(RepoCase):
    def test_deleted_file_is_g2(self):
        (self.root / "app/other.py").unlink()
        self.assertHas(self.found(), "G2", "app/other.py")

    def test_moved_file_is_g2_for_the_old_path(self):
        (self.root / "app/other.py").unlink()
        self.write("app/moved.py", "X = 1\n")
        self.assertHas(self.found(), "G2", "app/other.py")

    def test_removed_public_def_is_g2(self):
        self.write("app/a.py", "def _private():\n    return 2\n")
        self.assertHas(self.found(), "G2", "app/a.py")

    def test_def_moved_inside_file_is_not_g2(self):
        self.write("app/a.py", "def _private():\n    return 2\n\n\ndef public():\n    return 1\n")
        self.assertLacks(self.found(), "G2")

    def test_private_def_removed_is_not_g2(self):
        self.write("app/a.py", "def public():\n    return 1\n")
        self.assertLacks(self.found(), "G2")

    def test_manifest_change_is_g3(self):
        self.write("requirements.txt", "pytest\nrequests\n")
        self.assertHas(self.found(), "G3", "requirements.txt")

    def test_migration_path_is_g4(self):
        self.write("app/migrations/0001_init.py", "x = 1\n")
        self.write("app/schema.sql", "select 1;\n")
        items = self.found()
        self.assertHas(items, "G4", "app/migrations/0001_init.py")
        self.assertHas(items, "G4", "app/schema.sql")

    def test_sensitive_path_is_g5(self):
        self.write("app/auth.py", "A = 2\n")
        self.assertHas(self.found(), "G5", "app/auth.py")

    def test_author_is_not_sensitive(self):
        self.write("app/author.py", "A = 1\n")
        git(self.root, "add", "-A")
        self.assertLacks(self.found(), "G5")

    def test_removed_line_in_existing_test_is_g6(self):
        self.write("tests/test_a.py", "import unittest\n\n\nclass T(unittest.TestCase):\n"
                   "    def test_a(self):\n        self.assertEqual(1, 2)\n")
        self.assertHas(self.found(), "G6", "tests/test_a.py")

    def test_added_line_in_existing_test_is_clean(self):
        text = (self.root / "tests/test_a.py").read_text()
        self.write("tests/test_a.py", text + "\n    def test_b(self):\n        self.assertTrue(True)\n")
        self.assertLacks(self.found(), "G6")

    def test_deleted_test_is_g6(self):
        (self.root / "tests/test_a.py").unlink()
        self.assertHas(self.found(), "G6", "tests/test_a.py")

    def test_new_test_file_with_skip_is_g6(self):
        self.write("tests/test_new.py", "import unittest\n\n\n@unittest.skip('x')\nclass T(unittest.TestCase):\n    pass\n")
        self.assertHas(self.found(), "G6", "tests/test_new.py")

    def test_expected_failure_added_to_existing_test_is_g6(self):
        text = (self.root / "tests/test_a.py").read_text()
        self.write("tests/test_a.py", text.replace("    def test_a", "    @unittest.expectedFailure\n    def test_a"))
        self.assertHas(self.found(), "G6", "tests/test_a.py")

    def test_unreadable_untracked_files_are_still_changes(self):
        (self.root / "scripts").mkdir()
        (self.root / "scripts/blob.bin").write_bytes(b"\x89PNG\xff\x00")
        (self.root / "scripts/leg.py").write_bytes("x = 'ç'\n".encode("latin-1"))
        items = self.found()
        self.assertHas(items, "G1", "scripts/blob.bin")
        self.assertHas(items, "G1", "scripts/leg.py")
        self.assertIn("arquivos alterados: 2", quality(self.spec, self.root))

    def test_ci_and_auth_variants_are_g5(self):
        for name in ("azure-pipelines.yml", "app/oauth.py", "app/jwt_tokens.py", "Jenkinsfile"):
            self.write(name, "x\n")
        items = self.found()
        for name in ("azure-pipelines.yml", "app/oauth.py", "app/jwt_tokens.py", "Jenkinsfile"):
            self.assertHas(items, "G5", name)

    def test_odd_file_names_do_not_crash(self):
        self.write("app/a b/c.py", "A = 1\n")
        self.write('app/q"x.py', "A = 1\n")
        git(self.root, "add", "-A")
        git(self.root, "commit", "-q", "-m", "odd")
        self.write("app/a b/c.py", "A = 2\n")
        self.write('app/q"x.py', "A = 2\n")
        self.assertEqual(self.found(), [])
        self.assertEqual(quality(self.spec, self.root)[0], "arquivos alterados: 2")

    def test_nested_repo_and_broken_symlink_do_not_crash(self):
        nested = self.root / "vendor/lib"
        nested.mkdir(parents=True)
        subprocess.run(["git", "init", "-q", str(nested)], check=True)
        self.write("vendor/lib/x.py", "x = 1\n")
        (self.root / "app/dead").symlink_to(self.root / "nao-existe")
        self.assertEqual(len(fingerprint(self.root)), 12)
        self.found()

    def test_added_suppression_is_g7(self):
        self.write("app/other.py", "X = 1  # noqa\n")
        self.assertHas(self.found(), "G7", "app/other.py")

    def test_new_files_over_budget_are_g9(self):
        self.write("app/new.py", "N = 1\n")
        self.assertHas(self.found(), "G9", "app/new.py")

    def test_new_files_within_budget_are_clean(self):
        self.spec = self.write(".agent_plans/x/spec.md", SCOPE.format(budget=1))
        self.write("app/new.py", "N = 1\n")
        self.assertLacks(self.found(), "G9")


class FingerprintAndQualityTest(RepoCase):
    def test_fingerprint_is_stable_and_changes_after_an_edit(self):
        self.write("app/other.py", "X = 2\n")
        first = fingerprint(self.root)
        self.assertEqual(first, fingerprint(self.root))
        self.write("app/other.py", "X = 3\n")
        self.assertNotEqual(first, fingerprint(self.root))
        self.write("scripts/new.py", "print(1)\n")
        self.assertNotEqual(fingerprint(self.root), first)

    def test_fingerprint_ignores_agent_plans(self):
        before = fingerprint(self.root)
        self.write(".agent_plans/x/progress.md", "# Progresso\n")
        self.assertEqual(before, fingerprint(self.root))

    def test_fingerprint_and_triggers_ignore_tracked_agent_plans(self):
        self.write(".agent_plans/x/progress.md", "um\n")
        git(self.root, "add", "-A")
        git(self.root, "commit", "-q", "-m", "plans")
        before = fingerprint(self.root)
        self.write(".agent_plans/x/progress.md", "dois\n")
        self.assertEqual(before, fingerprint(self.root))
        self.assertEqual(self.found(), [])

    def test_quality_counts_new_files_and_suppressions(self):
        self.write("app/new.py", "N = 1  # noqa\n")
        self.write("app/other.py", "X = 2\n")
        items = quality(self.spec, self.root)
        self.assertIn("arquivos alterados: 2", items)
        self.assertIn("arquivos novos (orçamento 0): 1", items)
        self.assertIn("supressões novas: 1", items)
        self.assertIn("linhas adicionadas: 2", items)
        self.assertIn("linhas removidas: 1", items)


class ProgressCase(RepoCase):
    """Spec de exemplo da skill spec: AC-001..003, AC-Q01 e T1."""

    def setUp(self):
        super().setUp()
        self.spec = self.write(".agent_plans/reservas/spec.md", SPEC_EXAMPLE.read_text())
        self.write("app/booking.py", "def release():\n    return 1\n")
        git(self.root, "add", "-A")
        git(self.root, "commit", "-q", "-m", "booking")
        self.write("app/booking.py", "def release():\n    return 1\n\n\ndef cancel():\n    return 2\n")
        self.path = self.root / ".agent_plans/reservas/progress.md"

    def text(self, tree: str, *, ac: str = "passou", task: str = "concluída",
             found: str = "| RV-001 | alto | confirmado | — | corrigir | corrigido |",
             ready: str = "ok", extra: str = "") -> str:
        rows = "".join(f"| {i} | {ac} | `cmd` → OK | {tree} |\n"
                       for i in ("AC-001", "AC-002", "AC-003", "AC-Q01"))
        return (
            "# Progresso · spec: .agent_plans/reservas/spec.md\n\n"
            f"## Prontidão\n| Checagem | Resultado |\n| --- | --- |\n| check_spec.py | {ready} |\n\n"
            f"## Critérios de aceite\n| AC | Status | Evidência | Estado da árvore |\n| --- | --- | --- | --- |\n{rows}\n"
            f"## Tarefas\n| T | Status | Arquivos alterados | Verificação |\n| --- | --- | --- | --- |\n"
            f"| T1 | {task} | app/booking.py | `cmd` → OK |\n\n"
            "## Qualidade\n| Indicador | Antes | Depois | Limite | Origem |\n| --- | --- | --- | --- | --- |\n"
            "| arquivos novos | 0 | 0 | 0 | diff |\n\n"
            f"## Achados\n| ID | Severidade | Veredito | Gatilho | Ação | Resultado |\n| --- | --- | --- | --- | --- | --- |\n{found}\n\n"
            f"## Escaladas e decisões\nNenhuma.\n{extra}\n## Log\n- início\n")

    def run_check(self, text: str, fn=progress) -> list[str]:
        self.path.write_text(text, encoding="utf-8")
        return fn(self.path, self.spec, self.root)

    def assertError(self, errors: list[str], *words: str) -> None:
        self.assertTrue(any(all(w in e for w in words) for e in errors), errors)


class ProgressTest(ProgressCase):
    def test_valid_progress_is_clean(self):
        self.assertEqual(self.run_check(self.text("abc")), [])

    def test_missing_section_is_reported(self):
        text = self.text("abc").replace("## Log\n- início\n", "")
        self.assertError(self.run_check(text), "seção ausente", "Log")

    def test_missing_ac_and_task_are_reported(self):
        text = self.text("abc").replace("| AC-003 | passou | `cmd` → OK | abc |\n", "")
        text = text.replace("| T1 | concluída | app/booking.py | `cmd` → OK |\n", "")
        errors = self.run_check(text)
        self.assertError(errors, "AC faltando", "AC-003")
        self.assertError(errors, "tarefa faltando", "T1")

    def test_unknown_id_is_reported(self):
        text = self.text("abc").replace("| AC-Q01 |", "| AC-009 |")
        self.assertError(self.run_check(text), "desconhecido", "AC-009")

    def test_invalid_status_and_trigger_are_reported(self):
        self.assertError(self.run_check(self.text("abc", ac="ok")), "status inválido")
        found = "| RV-001 | alto | confirmado | G12 | corrigir | corrigido |"
        self.assertError(self.run_check(self.text("abc", found=found)), "gatilho inválido")

    def test_valid_triggers_list_is_accepted(self):
        found = "| RV-001 | alto | confirmado | G6, S1 | escalar | escalado |"
        self.assertEqual(self.run_check(self.text("abc", found=found)), [])

    def test_open_fence_and_non_utf8(self):
        self.assertError(self.run_check(self.text("abc") + "\n```\nabre\n"), "cerca de código aberta")
        self.path.write_bytes(b"# Progresso \xff\xfe\n")
        self.assertError(progress(self.path, self.spec, self.root), "não é UTF-8")


class ConvergeTest(ProgressCase):
    def converged(self, **kw) -> list[str]:
        return self.run_check(self.text(fingerprint(self.root), **kw), converge)

    def test_converged_run_is_clean(self):
        self.assertEqual(self.converged(), [])

    def test_evidence_from_an_older_tree_blocks_convergence(self):
        text = self.text(fingerprint(self.root))
        self.write("app/booking.py", "def release():\n    return 9\n")
        self.path.write_text(text, encoding="utf-8")
        self.assertError(converge(self.path, self.spec, self.root), "evidência anterior")

    def test_failing_or_unfilled_ac_blocks_convergence(self):
        self.assertError(self.converged(ac="falhou"), "AC sem evidência")
        self.assertError(self.converged(ac="pendente"), "AC sem evidência")

    def test_unfinished_task_and_unready_spec_block_convergence(self):
        self.assertError(self.converged(task="em andamento"), "tarefa não concluída")
        self.assertError(self.converged(ready="falhou"), "prontidão")

    def test_open_or_escalated_confirmed_finding_blocks_convergence(self):
        for result in ("aberto", "escalado"):
            found = f"| RV-001 | alto | confirmado | G6 | escalar | {result} |"
            self.assertError(self.converged(found=found), "achado sem resolução", "RV-001")

    def test_any_open_or_escalated_finding_blocks_convergence(self):
        for verdict in ("plausível", "confirmado"):
            for result in ("aberto", "escalado"):
                found = f"| RV-001 | alto | {verdict} | S7 | — | {result} |"
                self.assertError(self.converged(found=found), "achado sem resolução", "RV-001")

    def test_finding_with_a_trigger_cannot_end_corrected(self):
        found = "| RV-001 | alto | confirmado | G6 | editei o teste | corrigido |"
        self.assertError(self.converged(found=found), "gatilho", "RV-001")

    def test_refuted_result_needs_a_refuted_verdict(self):
        found = "| RV-001 | crítico | confirmado | — | — | refutado |"
        self.assertError(self.converged(found=found), "refutado", "RV-001")

    def test_blank_line_inside_findings_table_does_not_hide_a_row(self):
        found = ("| RV-001 | baixo | refutado | — | — | refutado |\n\n"
                 "| RV-002 | crítico | confirmado | — | — | aberto |")
        self.assertError(self.converged(found=found), "achado sem resolução", "RV-002")

    def test_manual_ac_may_stay_pending_but_not_failed(self):
        spec = SPEC_EXAMPLE.read_text()
        head, tail = spec.split("### AC-003", 1)
        self.spec.write_text(head + "### AC-003" + tail.replace("- Tipo: teste", "- Tipo: manual", 1), encoding="utf-8")
        text = self.text(fingerprint(self.root)).replace("| AC-003 | passou | `cmd` → OK |", "| AC-003 | pendente | — |")
        self.assertEqual(self.run_check(text, converge), [])
        text = text.replace("| AC-003 | pendente | — |", "| AC-003 | falhou | — |")
        self.assertError(self.run_check(text, converge), "AC sem evidência", "AC-003")

    def test_refuted_finding_does_not_block(self):
        found = "| RV-001 | alto | refutado | — | — | refutado |"
        self.assertEqual(self.converged(found=found), [])

    def test_pending_marker_blocks_but_not_inside_a_fence(self):
        self.assertError(self.converged(extra="\n[PRECISA DECISÃO: qual?]\n"), "marcador pendente")
        self.assertEqual(self.converged(extra="\n```\n[PRECISA DECISÃO: qual?]\n```\n"), [])

    def test_change_outside_scope_blocks_convergence(self):
        self.write("docs/x.md", "outro\n")
        self.assertError(self.converged(), "escopo", "docs/x.md")


class CliTest(ProgressCase):
    def run_main(self, *argv: str) -> tuple[int, str]:
        out = io.StringIO()
        with contextlib.redirect_stdout(out), contextlib.redirect_stderr(io.StringIO()):
            code = main(list(argv))
        return code, out.getvalue()

    def test_exit_codes(self):
        self.assertEqual(self.run_main("triggers", str(self.spec), str(self.root)), (0, "limpo\n"))
        self.write("docs/x.md", "outro\n")
        code, out = self.run_main("triggers", str(self.spec), str(self.root))
        self.assertEqual(code, 1)
        self.assertIn("G1 docs/x.md", out)
        self.assertEqual(self.run_main("triggers", "nao-existe.md", str(self.root))[0], 2)
        self.assertEqual(self.run_main("progress", "nao-existe.md", str(self.spec))[0], 2)
        self.assertEqual(self.run_main()[0], 2)

    def test_not_a_git_repository_exits_2(self):
        with tempfile.TemporaryDirectory() as tmp:
            self.assertEqual(self.run_main("tree", tmp)[0], 2)
            self.assertEqual(self.run_main("triggers", str(self.spec), tmp)[0], 2)

    def test_tree_and_quality_print(self):
        code, out = self.run_main("tree", str(self.root))
        self.assertEqual((code, len(out.strip())), (0, 12))
        code, out = self.run_main("quality", str(self.spec), str(self.root))
        self.assertEqual(code, 0)
        self.assertIn("arquivos alterados:", out)

    def test_progress_and_converge_commands(self):
        self.path.write_text(self.text(fingerprint(self.root)), encoding="utf-8")
        for command in ("progress", "converge"):
            self.assertEqual(self.run_main(command, str(self.path), str(self.spec), str(self.root)),
                             (0, "limpo\n"))


if __name__ == "__main__":
    unittest.main()
