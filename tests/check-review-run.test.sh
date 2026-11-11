#!/usr/bin/env bash
# Confere o check-review-run.sh sem agente: aceita a fixture com só
# .agent_plans/ novo e recusa arquivo editado, arquivo adicionado e commit.
set -euo pipefail

repo="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
tmp="$(mktemp -d)"
trap 'rm -rf "$tmp"' EXIT
check="$repo/tests/check-review-run.sh"
g() { git -C "$1" -c user.name=t -c user.email=t@example.invalid "${@:2}"; }
review() { mkdir -p "$1/.agent_plans/fixture" && echo x > "$1/.agent_plans/fixture/findings.md"; }
# "! cmd" não dispara o set -e; a recusa precisa de if explícito.
refuses() { if "$check" "$1" "$2" >/dev/null; then echo "aceitou e devia recusar: $1" >&2; exit 1; fi; }

for mode in commit arvore; do
  "$repo/tests/make-fixture.sh" "$tmp/$mode" "$mode"
  review "$tmp/$mode"
  "$check" "$tmp/$mode" "$mode" >/dev/null

  cp -R "$tmp/$mode" "$tmp/$mode-edit"
  echo "# editado" >> "$tmp/$mode-edit/app/db.py"
  refuses "$tmp/$mode-edit" "$mode"

  cp -R "$tmp/$mode" "$tmp/$mode-commit"
  g "$tmp/$mode-commit" add app tests requirements.lock
  g "$tmp/$mode-commit" commit -q --allow-empty -m "agente"
  refuses "$tmp/$mode-commit" "$mode"
done

cp -R "$tmp/arvore" "$tmp/arvore-add"
g "$tmp/arvore-add" add app/orders.py
refuses "$tmp/arvore-add" arvore
echo ok
