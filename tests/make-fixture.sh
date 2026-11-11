#!/usr/bin/env bash
# Monta o repositório de teste das avaliações: commit "base" e a mudança
# "exportar pedidos", commitada (commit) ou deixada na árvore (arvore).
set -euo pipefail

if [ $# -ne 2 ] || { [ "$2" != commit ] && [ "$2" != arvore ]; }; then
  echo "uso: $0 <destino> commit|arvore" >&2
  exit 2
fi
src="$(cd "$(dirname "${BASH_SOURCE[0]}")/fixture" && pwd)"
dest=$1
g() { git -C "$dest" -c user.name=fixture -c user.email=fixture@example.invalid "$@"; }

mkdir -p "$dest"
git init -q "$dest"
cp -R "$src/base/." "$dest/"
for i in $(seq 1 400); do echo "pkg$i==1.0.$i"; done > "$dest/requirements.lock"
g add -A
g commit -q -m "base"

cp -R "$src/change/." "$dest/"
for i in $(seq 401 420); do echo "pkg$i==1.0.$i"; done >> "$dest/requirements.lock"
if [ "$2" = commit ]; then
  g add -A
  g commit -q -m "exportar pedidos"
fi
