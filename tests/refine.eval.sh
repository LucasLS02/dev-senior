#!/usr/bin/env bash
# Avalia a skill refine na fixture com histórico (modo spec). Modos: funcionalidade
# (pedido de SMS: separar pedido de necessidade e achar o canal que já existe),
# vaga (cartão sem critério nenhum: gravar o rascunho com marcadores), bug (achar
# a causa raiz e preencher o diagnóstico) e descartada (o que se pede já existe:
# recomendar não fazer). Roda um agente de verdade: custa tokens. O diretório
# temporário fica para inspeção. SKILLS_DIR (opcional) troca a pasta de skills
# que o agente enxerga: a RED roda com uma pasta sem o refine.
set -euo pipefail

repo="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
case "${1:-}" in
  funcionalidade) card="card-101: avisar a operação por SMS quando a exportação CSV de um cliente terminar" ;;
  vaga) card="card-102: melhorar a exportação" ;;
  bug) card="card-103: a exportação de um cliente quebra com ValueError: invalid literal for int() quando o total é 1.234,50" ;;
  descartada) card="card-104: criar uma função que normalize o nome do cliente: sem acento, minúsculo, com hífens" ;;
  *)
    echo "uso: $0 funcionalidade|vaga|bug|descartada" >&2
    exit 2
    ;;
esac
prompt="Use a skill refine neste repositório. $card. Grave o brief em .agent_plans/<pasta>/brief.md, com uma pasta em kebab-case de sua escolha."

tmp=$(mktemp -d)
echo "diretório: $tmp"
"$repo/tests/make-docs-fixture.sh" "$tmp/repo" spec
cd "$tmp/repo"

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
has() { grep -qiE "$2" <<<"$1"; }  # has <texto> <regex>
finish() { [ "$fail" = 0 ] && echo "resultado: passou" || echo "resultado: falhou"; exit "$fail"; }

brief=$(ls .agent_plans/*/brief.md 2>/dev/null | head -1 || true)
check "nenhum commit novo" test "$(git rev-list --count HEAD)" = 8
check "só .agent_plans/ novo" test "$(git status --porcelain)" = "?? .agent_plans/"
check "um brief.md" test "$(ls .agent_plans/*/brief.md 2>/dev/null | wc -l | tr -d ' ')" = 1
[ -n "$brief" ] || finish
check "Status: rascunho" grep -q '^Status: rascunho' "$brief"
check "nenhuma spec.md" test -z "$(ls .agent_plans/*/spec.md 2>/dev/null || true)"

section() { awk -v h="## $1" '{l=$0; sub(/[ \t]+$/, "", l)} l==h {p=1; next} /^## / {p=0} p' "$brief"; }
validator="$repo/skills/refine/scripts/check_brief.py"
out=$(python3 "$validator" "$brief" . || true)
only_markers() { [ -z "$(grep -v 'marcador pendente' <<<"$out" | grep -v '^limpo$' || true)" ]; }
markers=$(grep -c 'marcador pendente' <<<"$out" || true)
case "$1" in
  funcionalidade)
    check "check_brief.py limpo ou só marcadores" only_markers
    check "Pedido e Necessidade diferem" python3 -c '
import re, sys
t = " ".join(sys.argv[1].split())
p, n = re.search(r"Pedido:(.*?)Necessidade:", t).group(1), t.split("Necessidade:", 1)[1]
sys.exit(0 if p.strip() and n.strip() and p.strip() != n.strip() else 1)' "$(section "Pedido vs. necessidade")"
    check "cita app/handlers/" has "$(section "Opções consideradas")$(section Recomendação)" 'app/handlers'
    check "Modo padrão no Apetite" has "$(section Apetite)" '^Modo padrão:'
    check "no máximo 60 linhas" test "$(wc -l < "$brief")" -le 60
    ;;
  vaga)
    check "o validador reclama, e só de marcador pendente" test -n "$out" -a "$out" != limpo
    check "validador só com marcadores" only_markers
    check "de 1 a 5 marcadores" test "$markers" -ge 1 -a "$markers" -le 5
    ;;
  bug)
    check "check_brief.py limpo ou só marcadores" only_markers
    check "tem a seção Diagnóstico" has "$(section Diagnóstico)" 'Causa raiz'
    check "Causa raiz cita app/money.py:1-3" grep -qE 'Causa raiz:.*app/money\.py:[1-3]' "$brief"
    check "Reprodução com comando e o erro" has "$(grep 'Reprodução:' "$brief")" '`.*ValueError|ValueError.*`'
    ;;
  descartada)
    check "check_brief.py limpo ou só marcadores" only_markers
    check "a recomendada é não fazer" has "$(section "Opções consideradas")" 'não fazer.*Recomendada'
    check "cita app/text.py" has "$(cat "$brief")" 'app/text\.py:[0-9]'
    ;;
esac
finish
