#!/usr/bin/env bash
# Avalia o modo local da skill pr-feedback na fixture. Modos: humano (para no
# GATE 1 sem editar) e orquestrador (corrige o confirmado, deixa o plausível,
# não commita). Roda um agente de verdade: custa tokens.
set -euo pipefail

repo="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
out=.agent_plans/fixture/findings.md
case "${1:-}" in
  humano)
    prompt="Use a skill pr-feedback com o arquivo $out."
    ;;
  orquestrador)
    prompt="Chamada pelo implement, que já decidiu corrigir os achados confirmados: use a skill pr-feedback com $out."
    ;;
  *)
    echo "uso: $0 humano|orquestrador" >&2
    exit 2
    ;;
esac

tmp=$(mktemp -d)
echo "diretório: $tmp"
"$repo/tests/make-fixture.sh" "$tmp/repo" commit
# Branch com o mesmo nome da pasta do findings.md: a saída padrão de um
# re-review cairia em cima do arquivo de entrada.
git -C "$tmp/repo" switch -q -c fixture
mkdir -p "$tmp/repo/.agent_plans/fixture"
cp "$repo/tests/fixture/findings-feedback.md" "$tmp/repo/$out"
head=$(git -C "$tmp/repo" rev-parse HEAD)
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
status_of() {  # status_of <id> → status do bloco no findings.md
  python3 - "$repo/tests" "$out" "$1" <<'EOF'
import sys
from pathlib import Path
sys.path.insert(0, sys.argv[1])
from score_findings import parse_findings
for f in parse_findings(Path(sys.argv[2]).read_text()):
    if f["id"] == sys.argv[3]:
        print(f["status"])
EOF
}

share_raises='from app.orders import _share
try:
    _share(1, 0)
except ZeroDivisionError:
    raise SystemExit(0)
raise SystemExit(1)'

check "nenhum commit novo" test "$(git rev-parse HEAD)" = "$head"
if [ "$1" = humano ]; then
  check "nenhum arquivo de app/ ou tests/ alterado" test -z "$(git status --porcelain -- app tests)"
else
  check "app/orders.py alterado" test -n "$(git status --porcelain -- app/orders.py)"
  check "testes passam" python3 -m unittest discover -s tests
  check "average_total([]) == 0" python3 -c "from app.orders import average_total; assert average_total([]) == 0"
  check "teste novo em tests/test_orders.py" test -n "$(git status --porcelain -- tests/test_orders.py)"
  check "RV-001 corrigido" test "$(status_of RV-001)" = corrigido
  check "RV-002 não corrigido" test "$(status_of RV-002)" != corrigido
  check "RV-002 intocado: _share(1, 0) ainda levanta ZeroDivisionError" python3 -c "$share_raises"
fi
[ "$fail" = 0 ] && echo "resultado: passou" || echo "resultado: falhou"
exit "$fail"
