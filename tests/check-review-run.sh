#!/usr/bin/env bash
# Confere que um agente deixou o repositório da fixture como estava: o único
# rastro permitido é .agent_plans/. O review-diff só lê (spec, seção 6.4).
set -euo pipefail

if [ $# -ne 2 ] || { [ "$2" != commit ] && [ "$2" != arvore ]; }; then
  echo "uso: $0 <repo da fixture> commit|arvore" >&2
  exit 2
fi
repo=$1
if [ "$2" = commit ]; then
  commits=2
  expected=""
else
  commits=1
  expected=$(printf '%s\n' ' M requirements.lock' '?? app/orders.py' '?? tests/test_orders.py' | sort)
fi

fail=0
actual=$(git -C "$repo" status --porcelain | grep -v '^?? \.agent_plans/$' | sort || true)
if [ "$(git -C "$repo" rev-list --count HEAD)" != "$commits" ]; then
  echo "FALHOU: o histórico mudou (esperava $commits commits)"
  fail=1
fi
if [ "$actual" != "$expected" ]; then
  echo "FALHOU: a árvore mudou além de .agent_plans/:"
  printf '%s\n' "$actual"
  fail=1
fi
[ "$fail" = 0 ] && echo "ok: repositório intacto"
exit "$fail"
