#!/usr/bin/env bash
# Roda o install.sh num HOME falso e confere os três casos: cria o link,
# atualiza um link antigo e preserva uma pasta real.
set -euo pipefail

repo="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
home="$(mktemp -d)"
trap 'rm -rf "$home"' EXIT

skill="$(basename "$(ls -d "$repo"/skills/*/ | head -1)")"
mkdir -p "$home/.agents" "$home/.claude/skills" "$home/.claude-work/skills/$skill"
ln -s /caminho/antigo "$home/.claude/skills/$skill"

HOME="$home" bash "$repo/install.sh" >/dev/null 2>&1

[ -L "$home/.agents/skills/$skill" ]
[ "$(readlink "$home/.claude/skills/$skill")" = "$repo/skills/$skill" ]
[ ! -L "$home/.claude-work/skills/$skill" ]
[ ! -e "$home/.codex" ]
echo ok
