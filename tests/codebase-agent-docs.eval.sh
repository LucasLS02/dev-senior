#!/usr/bin/env bash
# Avalia a skill codebase-agent-docs na fixture com histórico. Modos:
# aprovacao (para na tabela de candidatos), escrita (aprovação prévia: gera a
# documentação) e auditoria (AGENTS.md à mão: só propõe). Roda um agente de
# verdade: custa tokens. O diretório temporário fica para inspeção.
set -euo pipefail

repo="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
case "${1:-}" in
  aprovacao)
    fixture=criar commits=7
    prompt="Use a skill codebase-agent-docs neste repositório."
    ;;
  escrita)
    fixture=criar commits=7
    prompt="Use a skill codebase-agent-docs neste repositório. Aprovação prévia: escreva todos os candidatos que tiverem evidência; não pare para perguntar."
    ;;
  auditoria)
    fixture=auditar commits=8
    prompt="Use a skill codebase-agent-docs neste repositório."
    ;;
  *)
    echo "uso: $0 aprovacao|escrita|auditoria" >&2
    exit 2
    ;;
esac

tmp=$(mktemp -d)
echo "diretório: $tmp"
"$repo/tests/make-docs-fixture.sh" "$tmp/repo" "$fixture"
rc=0
"$repo/tests/run-agent.sh" "$tmp/repo" "$prompt" > "$tmp/agent.log" 2>&1 || rc=$?
if [ "$rc" != 0 ]; then
  echo "resultado: falhou (o agente saiu com código $rc; veja $tmp/agent.log)"
  exit 1
fi

cd "$tmp/repo"
fail=0
check() {  # check <descrição> <comando...>
  local what=$1
  shift
  if "$@" >/dev/null 2>&1; then echo "ok: $what"; else echo "FALHOU: $what"; fail=1; fi
}
sha() { git log --format=%h --abbrev=7 --grep="$1"; }
traps() {  # traps <arquivo>: A1, A2 e A3 por hash curto ou palavra-chave
  local f=$1
  grep -qiE "$(sha 'UTC timestamps')|UTC" "$f" &&
    grep -qE "$(sha 'register sms')|HANDLERS" "$f" &&
    grep -qiE "$(sha 'integer cents')|centavo|cents" "$f"
}
cand=.agent_plans/agent-docs/candidatos.md

check "nenhum commit novo" test "$(git rev-list --count HEAD)" = "$commits"
# guia AGENTS.md dentro de app/ é saída legítima da skill, não código
check "nenhum código alterado" test -z "$(git status --porcelain -- app tests scripts ':!*AGENTS.md')"
case "$1" in
  aprovacao)
    check "só .agent_plans/ novo" test "$(git status --porcelain)" = "?? .agent_plans/"
    check "candidatos.md com C-01" grep -q "C-01" "$cand"
    check "candidatos traz A1, A2 e A3" traps "$cand"
    check "candidatos traz slugify" grep -q "slugify" "$cand"
    ;;
  escrita)
    check "check_docs.py limpo" python3 "$repo/skills/codebase-agent-docs/scripts/check_docs.py" .
    check "AGENTS.md, REVIEW.md e reuse.md existem" test -f AGENTS.md -a -f REVIEW.md -a -f docs/agents/reuse.md
    check "gotchas traz A1, A2 e A3" traps docs/agents/gotchas.md
    check "gotchas com 3 fontes" test "$(grep -c 'fonte:' docs/agents/gotchas.md)" -ge 3
    check "reuse.md traz slugify" grep -q "slugify" docs/agents/reuse.md
    check "dont-touch traz app/schema_gen.py" grep -q "app/schema_gen.py" docs/agents/dont-touch.md
    check "AGENTS.md traz python3 -m unittest" grep -q "python3 -m unittest" AGENTS.md
    check "AGENTS.md traz DATABASE_URL" grep -q "DATABASE_URL" AGENTS.md
    ;;
  auditoria)
    check "AGENTS.md intocado" git diff --quiet HEAD -- AGENTS.md
    check "candidatos cita app/legacy_export.py" grep -q "app/legacy_export.py" "$cand"
    ;;
esac
[ "$fail" = 0 ] && echo "resultado: passou" || echo "resultado: falhou"
exit "$fail"
