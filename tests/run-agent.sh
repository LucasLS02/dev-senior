#!/usr/bin/env bash
# Roda um agente sem interação dentro de um diretório, com a saída no stdout.
# AGENT=claude (padrão, perfil de CLAUDE_CONFIG_DIR ou ~/.claude) ou codex.
# Nunca usa modo que pula permissões.
set -euo pipefail

if [ $# -ne 2 ]; then
  echo "uso: $0 <diretório> <prompt>" >&2
  exit 2
fi
repo="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
dir=$1
prompt=$2
cd "$dir"

case "${AGENT:-claude}" in
  claude)
    CLAUDE_CONFIG_DIR="${CLAUDE_CONFIG_DIR:-$HOME/.claude}" command claude -p "$prompt" \
      --add-dir "${SKILLS_DIR:-$repo/skills}" \
      --allowedTools "Read,Grep,Glob,Write,Edit,Skill,Bash(git:*),Bash(python3:*),Bash(ls:*)${EXTRA_TOOLS:+,$EXTRA_TOOLS}"
    ;;
  codex)
    codex exec --sandbox workspace-write "$prompt"
    ;;
  *)
    echo "AGENT desconhecido: $AGENT (use claude ou codex)" >&2
    exit 2
    ;;
esac
