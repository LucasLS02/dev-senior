#!/usr/bin/env bash
# Liga cada skill deste repositório nas pastas de skills das ferramentas
# instaladas. Só cria ou atualiza links: uma pasta real nunca é sobrescrita.
set -euo pipefail

repo="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
roots=("$HOME/.agents/skills" "$HOME/.claude/skills" "$HOME/.claude-work/skills"
       "$HOME/.codex/skills" "$HOME/.config/opencode/skills" "$HOME/.gemini/config/skills")

for root in "${roots[@]}"; do
  # Ferramenta não instalada nesta máquina: a pasta-mãe não existe.
  [ -d "$(dirname "$root")" ] || continue
  mkdir -p "$root"
  for skill in "$repo"/skills/*/; do
    target="$root/$(basename "$skill")"
    if [ -e "$target" ] && [ ! -L "$target" ]; then
      echo "pulado (pasta real, não é link): $target" >&2
      continue
    fi
    ln -sfn "${skill%/}" "$target"
    echo "ligado: $target"
  done
done
