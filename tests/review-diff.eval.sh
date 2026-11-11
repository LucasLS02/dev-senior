#!/usr/bin/env bash
# Avalia a skill review-diff na fixture. Modos: base (sem a skill, a linha de
# base), commit, arvore e vazio. Roda um agente de verdade: custa tokens.
# O diretório temporário fica para inspeção (agent.log e repo/).
set -euo pipefail

repo="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
out=.agent_plans/fixture/findings.md
case "${1:-}" in
  base)
    fixture=commit
    prompt="Revise as mudanças do intervalo HEAD~1..HEAD. O card está em docs/card.md. Grave os achados em $out no formato descrito em $repo/skills/review-diff/references/achados.md."
    ;;
  commit)
    fixture=commit
    prompt="Use a skill review-diff, perfil próprio, no intervalo HEAD~1..HEAD. Card: docs/card.md. Saída: $out."
    ;;
  arvore)
    fixture=arvore
    prompt="Use a skill review-diff, perfil próprio, na árvore de trabalho. Card: docs/card.md. Saída: $out."
    ;;
  vazio)
    fixture=commit
    prompt="Use a skill review-diff, perfil próprio, no intervalo HEAD..HEAD. Saída: $out."
    ;;
  *)
    echo "uso: $0 base|commit|arvore|vazio" >&2
    exit 2
    ;;
esac

tmp=$(mktemp -d)
echo "diretório: $tmp"
"$repo/tests/make-fixture.sh" "$tmp/repo" "$fixture"
# O log fica fora de repo/ para não virar arquivo não rastreado no review.
rc=0
"$repo/tests/run-agent.sh" "$tmp/repo" "$prompt" > "$tmp/agent.log" 2>&1 || rc=$?
if [ "$rc" != 0 ]; then
  echo "resultado final: falhou (o agente saiu com código $rc; veja $tmp/agent.log)"
  exit 1
fi

fail=0
"$repo/tests/check-review-run.sh" "$tmp/repo" "$fixture" || fail=1
if [ "$1" = vazio ]; then
  if [ -f "$tmp/repo/$out" ] && grep -q '^```yaml' "$tmp/repo/$out"; then
    echo "FALHOU: achado num intervalo vazio"
    fail=1
  fi
else
  python3 "$repo/tests/score_findings.py" "$tmp/repo/$out" --root "$tmp/repo" \
    --expected "$repo/tests/fixture/expected.tsv" --expect-coverage requirements.lock ||
    fail=1
fi
[ "$fail" = 0 ] && echo "resultado final: passou" || echo "resultado final: falhou"
exit "$fail"
