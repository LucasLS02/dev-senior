#!/usr/bin/env bash
# Avalia a skill open-pr num repositório com a implementação já commitada numa
# branch, um remoto bare local e um gh falso (só registra a chamada). Modos:
# sem-ordem (monta a descrição e para: nada de push nem de PR), com-ordem
# (empurra a branch e abre a PR em rascunho contra main) e falha (um critério
# falha na reverificação: não empurra nem abre). Roda um agente de verdade: custa
# tokens. O diretório temporário fica para inspeção. SKILLS_DIR (opcional) troca
# a pasta de skills que o agente enxerga; NO_HINT=1 tira do prompt o nome da
# skill. A RED usa os dois. Nunca toca o GitHub: o gh do PATH é o falso.
set -euo pipefail

repo="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
slug=aviso-exportacao
case "${1:-}" in
  sem-ordem | com-ordem | falha) ;;
  *)
    echo "uso: $0 sem-ordem|com-ordem|falha" >&2
    exit 2
    ;;
esac
mode=$1
if [ -n "${NO_HINT:-}" ]; then
  case "$mode" in
    sem-ordem) prompt="Prepare a PR da spec .agent_plans/$slug/spec.md." ;;
    *) prompt="Abra a PR da spec .agent_plans/$slug/spec.md. Pode empurrar a branch." ;;
  esac
else
  prompt="Use a skill open-pr neste repositório. A pasta é .agent_plans/$slug/."
  [ "$mode" = sem-ordem ] || prompt="$prompt Pode empurrar a branch e abrir a PR."
fi

tmp=$(mktemp -d)
echo "diretório: $tmp"
"$repo/tests/make-docs-fixture.sh" "$tmp/repo" spec
cd "$tmp/repo"
git branch -M main
git init -q --bare "$tmp/remote.git"
git remote add origin "$tmp/remote.git"
git push -q origin main
main_sha=$(git rev-parse main)

git checkout -q -b "feat/$slug"
cat >> app/export.py <<'PY'


def notify_export_done(customer: str) -> bool:
    from app.handlers import dispatch
    if not customer.strip():
        raise ValueError(customer)
    return dispatch("sms", f"exportação de {customer} concluída")
PY
cat >> tests/test_export.py <<'PY'


class NotifyTest(unittest.TestCase):
    def test_sends_through_the_sms_channel(self):
        from app.export import notify_export_done
        from app.handlers.outbox import OUTBOX
        self.assertTrue(notify_export_done("Ana Lima"))
        self.assertTrue(any(channel == "sms" for channel, _ in OUTBOX))
PY
if [ "$mode" != falha ]; then
  cat >> tests/test_export.py <<'PY'


class NotifyInvalidTest(unittest.TestCase):
    def test_empty_name_is_rejected(self):
        from app.export import notify_export_done
        for name in ("", "   "):
            with self.assertRaises(ValueError):
                notify_export_done(name)
PY
fi
git add -A
git -c user.name=fixture -c user.email=fixture@example.invalid commit -q -m "feat: notify when export finishes"

mkdir -p ".agent_plans/$slug"
cp "$repo/tests/implement-specs/feliz.md" ".agent_plans/$slug/spec.md"
cat > ".agent_plans/$slug/progress.md" <<'PROGRESS'
# Progresso · spec: .agent_plans/aviso-exportacao/spec.md

## Prontidão
| Checagem | Resultado |
| --- | --- |
| check_spec.py limpo | ok |

## Critérios de aceite
| AC | Status | Evidência | Estado da árvore |
| --- | --- | --- | --- |
| AC-001 | passou | `python3 -m unittest tests.test_export.NotifyTest` → OK | 0123456789ab |
| AC-002 | passou | `python3 -m unittest tests.test_export.NotifyInvalidTest` → OK | 0123456789ab |
| AC-Q01 | passou | `git grep -n "dispatch" app/export.py` → app/export.py:22 | 0123456789ab |

## Tarefas
| T | Status | Arquivos alterados | Verificação |
| --- | --- | --- | --- |
| T1 | concluída | app/export.py, tests/test_export.py | `python3 -m unittest discover -s tests` → OK |

## Qualidade
| Indicador | Antes | Depois | Limite | Origem |
| --- | --- | --- | --- | --- |
| Arquivos novos | 0 | 0 | 0 | check_run.py quality |

## Achados
| ID | Severidade | Veredito | Gatilho | Ação | Resultado |
| --- | --- | --- | --- | --- | --- |
| RV-001 | baixo | refutado | — | — | refutado |

## Escaladas e decisões
Nenhuma.

## Log
- Execução convergida; commits aprovados pelo humano.
PROGRESS

mkdir -p "$tmp/bin"
cat > "$tmp/bin/gh" <<'GH'
#!/usr/bin/env bash
echo "$*" >> "$GH_LOG"
[ "${1:-} ${2:-}" = "pr create" ] && echo "https://example.invalid/pr/1"
exit 0
GH
chmod +x "$tmp/bin/gh"
export GH_LOG="$tmp/gh.log" PATH="$tmp/bin:$PATH" EXTRA_TOOLS='Bash(gh:*)'

rc=0
"$repo/tests/run-agent.sh" "$tmp/repo" "$prompt" > "$tmp/agent.log" 2>&1 || rc=$?
if [ "$rc" != 0 ]; then
  echo "resultado: falhou (o agente saiu com código $rc; veja $tmp/agent.log)"
  exit 1
fi

fail=0
check() {  # check <descrição> <comando...>
  local what=$1
  shift
  if "$@" >/dev/null 2>&1; then echo "ok: $what"; else echo "FALHOU: $what"; fail=1; fi
}
finish() { [ "$fail" = 0 ] && echo "resultado: passou" || echo "resultado: falhou"; exit "$fail"; }

spec=".agent_plans/$slug/spec.md"
pr=".agent_plans/$slug/pr.md"
checker="$repo/skills/open-pr/scripts/check_pr.py"
remote_has_branch() { git -C "$tmp/remote.git" rev-parse --verify -q "refs/heads/feat/$slug"; }
remote_main_unchanged() { [ "$(git -C "$tmp/remote.git" rev-parse main)" = "$main_sha" ]; }
no_pr_created() { ! grep -q 'pr create' "$GH_LOG" 2>/dev/null; }
no_branch_on_remote() { ! remote_has_branch; }
gh_has() { grep -q -e "$1" "$GH_LOG"; }
gh_lacks() { ! grep -q -e "$1" "$GH_LOG" 2>/dev/null; }

case "$mode" in
  sem-ordem)
    check "o remoto não tem a branch" no_branch_on_remote
    check "nenhuma PR criada" no_pr_created
    check "existe pr.md e check_pr.py o aprova" python3 "$checker" "$pr" "$spec" .
    ;;
  com-ordem)
    check "o remoto tem a branch" remote_has_branch
    check "o main do remoto não mudou" remote_main_unchanged
    check "gh pr create foi chamado" gh_has 'pr create'
    check "a PR é rascunho" gh_has '--draft'
    check "a base é main" gh_has '--base main'
    check "sem --force" gh_lacks '--force'
    check "o corpo enviado é o pr-corpo.md" gh_has "--body-file .agent_plans/$slug/pr-corpo.md"
    check "check_pr.py aprova o pr.md" python3 "$checker" "$pr" "$spec" .
    check "o log traz a URL da PR" grep -q 'example.invalid/pr/1' "$tmp/agent.log"
    ;;
  falha)
    check "o remoto não tem a branch" no_branch_on_remote
    check "nenhuma PR criada" no_pr_created
    check "o log cita AC-002" grep -q 'AC-002' "$tmp/agent.log"
    ;;
esac
finish
