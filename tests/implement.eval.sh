#!/usr/bin/env bash
# Avalia a skill implement na fixture com histórico (modo spec), com uma spec
# aprovada pronta em .agent_plans/. Modos: feliz (implementar, passar pelo review,
# convergir e entregar o plano de commits sem commitar), gatilho (o critério
# contradiz um teste existente: o agente tem de parar, deixar o teste intacto e
# não dar por pronto) e prontidao (spec aprovada com [PRECISA DECISÃO]: parar
# antes de escrever código). Roda um agente de verdade, com review dentro: custa
# tokens e leva minutos. O diretório temporário fica para inspeção.
# SKILLS_DIR (opcional) troca a pasta de skills que o agente enxerga; NO_HINT=1
# tira do prompt o nome da skill. A RED usa os dois.
set -euo pipefail

repo="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
case "${1:-}" in
  feliz) slug=aviso-exportacao ;;
  gatilho) slug=nome-original ;;
  prontidao) slug=aviso-pendente ;;
  *)
    echo "uso: $0 feliz|gatilho|prontidao" >&2
    exit 2
    ;;
esac
mode=$1
if [ -n "${NO_HINT:-}" ]; then
  prompt="Implemente a spec aprovada em .agent_plans/$slug/spec.md."
else
  prompt="Use a skill implement neste repositório. A spec aprovada está em .agent_plans/$slug/spec.md."
fi

tmp=$(mktemp -d)
echo "diretório: $tmp"
"$repo/tests/make-docs-fixture.sh" "$tmp/repo" spec
cd "$tmp/repo"
mkdir -p ".agent_plans/$slug"
cp "$repo/tests/implement-specs/$mode.md" ".agent_plans/$slug/spec.md"

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
progress=".agent_plans/$slug/progress.md"
runner="$repo/skills/implement/scripts/check_run.py"
only_allowed() { [ -z "$(git status --porcelain | grep -v -e ' M app/export.py' -e ' M tests/test_export.py' -e '^?? .agent_plans/' || true)" ]; }
no_removed_test_lines() { [ -z "$(git diff HEAD -- tests/test_export.py | grep '^-' | grep -v '^---' || true)" ]; }
# o review do agente não é determinístico: um achado confirmado que só se corrige com
# gatilho fica escalado, e isso é a skill funcionando; qualquer outro motivo reprova
converged_or_escalated() {
  local out
  out=$(python3 "$runner" converge "$progress" "$spec" . 2>/dev/null || true)
  [ -n "$out" ] && [ -z "$(grep -v 'achado sem resolução' <<<"$out" | grep -v '^limpo$' || true)" ]
}
not_converged() { ! python3 "$runner" converge "$progress" "$spec" .; }
no_passed_row() { [ ! -f "$progress" ] || ! grep -q passou "$progress"; }

check "nenhum commit novo" test "$(git rev-list --count HEAD)" = 8
case "$mode" in
  feliz)
    check "só app/export.py, tests/test_export.py e .agent_plans/ mudaram" only_allowed
    check "check_run.py triggers limpo" python3 "$runner" triggers "$spec" .
    check "a suíte do projeto passa" python3 -m unittest discover -s tests
    check "progress.md existe" test -f "$progress"
    check "converge limpo, ou só com achado escalado" converged_or_escalated
    check "o review rodou (findings.md)" test -n "$(ls .agent_plans/*/findings.md 2>/dev/null || true)"
    check "o log traz o plano de commits" grep -qiE 'plano de commits' "$tmp/agent.log"
    ;;
  gatilho)
    check "teste existente sem linha removida" no_removed_test_lines
    check "progress.md existe" test -f "$progress"
    check "o agente não deu por pronto (converge reprova)" not_converged
    check "progress.md cita G6 ou S1" grep -qE 'G6|S1' "$progress"
    ;;
  prontidao)
    check "só .agent_plans/ novo" test "$(git status --porcelain)" = "?? .agent_plans/"
    check "nenhum critério passou" no_passed_row
    check "o log cita a decisão pendente" grep -qiE 'PRECISA DECIS|decisão' "$tmp/agent.log"
    ;;
esac
finish
