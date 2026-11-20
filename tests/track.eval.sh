#!/usr/bin/env bash
# Avaliação com agente real e gh simulado; não acessa GitHub. Custa tokens.
set -euo pipefail
repo="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
case "${1:-}" in
  criar|vincular|repetir|sem-estado|escalada|sem-config) mode=$1 ;;
  *) echo "uso: bash tests/track.eval.sh criar|vincular|repetir|sem-estado|escalada|sem-config" >&2; exit 2 ;;
esac
tmp=$(mktemp -d "${TMPDIR:-/tmp}/track.XXXXXX")
echo "diretório: $tmp"
"$repo/tests/make-docs-fixture.sh" "$tmp/repo" spec
git -C "$tmp/repo" remote add origin https://github.com/example/project.git
mkdir -p "$tmp/bin" "$tmp/repo/.agent_plans/aviso-exportacao" "$tmp/repo/.agents/skills"
ln -s "$repo/skills/track" "$tmp/repo/.agents/skills/track"
ln -s "$repo/skills/implement" "$tmp/repo/.agents/skills/implement"
ln -s "$repo/tests/track_fake_gh.py" "$tmp/bin/gh"
mkdir -p "$tmp/zsh" "$tmp/empty-gh-config"
printf 'export PATH="%s:$PATH"\n' "$tmp/bin" > "$tmp/zsh/.zprofile"
export ZDOTDIR="$tmp/zsh" PATH="$tmp/bin:$PATH" TRACK_GH_STATE="$tmp/gh.json" EXTRA_TOOLS='Bash(gh:*)'
export GH_CONFIG_DIR="$tmp/empty-gh-config" GH_TOKEN='fixture-invalid-token' GH_ENTERPRISE_TOKEN='fixture-invalid-token'
if [ "$(zsh -lc 'command -v gh')" != "$tmp/bin/gh" ]; then
  echo "ambiente inseguro: gh real visível no shell; avaliação cancelada" >&2
  exit 1
fi
cp "$repo/tests/implement-specs/feliz.md" "$tmp/repo/.agent_plans/aviso-exportacao/spec.md"
cat > "$tmp/repo/.agent_plans/aviso-exportacao/progress.md" <<'PROGRESS'
# Progresso · spec: .agent_plans/aviso-exportacao/spec.md
## Prontidão
| Checagem | Resultado |
| --- | --- |
| check_spec.py limpo | ok |
| Status aprovado | ok |
| Sem marcador pendente | ok |
| Árvore limpa | ok |
## Tarefas
| T | Status | Arquivos alterados | Verificação |
| --- | --- | --- | --- |
| T1 | pendente | — | — |
## Escaladas e decisões
PROGRESS
if [ "$mode" != sem-config ]; then
  cat >> "$tmp/repo/AGENTS.md" <<'CONFIG'

## Acompanhamento de projeto
- Ferramenta: GitHub · Acesso: gh · Projeto: example/project
- Tipos: spec → Issue
- Status: em andamento = "em andamento" · em review = "em review"
- Impedimento: bloqueado
CONFIG
fi
if [ "$mode" = escalada ]; then
  cat >> "$tmp/repo/.agent_plans/aviso-exportacao/progress.md" <<'ESC'
### Escalada 1
Gatilho: S1 · Tarefa ou achado: T1
Motivo: comportamento diverge
Arquivos: app/export.py
Efeito: a entrega está impedida
Alternativas: alterar a regra ou mantê-la
Recomendação: confirmar a regra
Dependência externa: sim
Decisão: pendente
ESC
fi
if [ "$mode" = vincular ]; then
  python3 - "$TRACK_GH_STATE" <<'PY'
import json, sys
from pathlib import Path
Path(sys.argv[1]).write_text(json.dumps({"calls": [], "issues": [{"number": 1, "url": "https://github.com/example/project/issues/1", "title": "Origem", "body": "Descrição humana", "labels": [], "comments": []}]}))
PY
  origin='O card de origem é https://github.com/example/project/issues/1.'
else
  origin='Não há card de origem; verifiquei no quadro simulado que não existe outro item para esta tarefa.'
fi
prompt="Use a skill track na pasta .agent_plans/aviso-exportacao, origem implement. $origin Autorizo explicitamente a criação ou vínculo, edição da descrição proposta e todas as atualizações de rotina desta tarefa no gh simulado. Use apenas $tmp/bin/gh; não use rede nem outro executável gh."
run_agent() { "$repo/tests/run-agent.sh" "$tmp/repo" "$prompt" >> "$tmp/agent.log" 2>&1; }
if ! run_agent; then echo "agente falhou: $tmp/agent.log"; exit 1; fi
if [ "$mode" = repetir ] || [ "$mode" = sem-estado ]; then
  if [ "$mode" = sem-estado ]; then mv "$tmp/repo/.agent_plans/aviso-exportacao/tracker.md" "$tmp/tracker-anterior.md"; fi
  if ! run_agent; then echo "agente falhou na retomada: $tmp/agent.log"; exit 1; fi
fi
python3 - "$TRACK_GH_STATE" "$mode" "$tmp/repo/.agent_plans/aviso-exportacao/spec.md" <<'PY'
import json, re, sys
from pathlib import Path
path, mode, spec = Path(sys.argv[1]), sys.argv[2], Path(sys.argv[3]).read_text()
state = json.loads(path.read_text()) if path.exists() else {"issues": [], "calls": []}
issues, calls = state["issues"], state["calls"]
if mode == "sem-config":
    assert not calls, calls
else:
    assert len(issues) == 1, issues
    issue = issues[0]
    assert "fluxo-" in issue["body"], issue
    acs = set(re.findall(r"^### (AC-\d{3})\b|^- (AC-Q\d{2})\b", spec, re.M))
    for pair in acs:
        assert next(part for part in pair if part) in issue["body"], pair
    tasks = re.findall(r"^### T\d+\s+(.+?)\s+·\s+Depende de:", spec, re.M)
    assert tasks and all(task in issue["body"] for task in tasks), tasks
    assert len([c for c in calls if c[:2] == ["issue", "create"]]) == (0 if mode == "vincular" else 1), calls
    if mode == "vincular":
        assert "Descrição humana" in issue["body"]
    comments = [c["body"] for c in issue["comments"]]
    footers = [m.group(0) for c in comments for m in re.finditer(r"^— fluxo: .+$", c, re.M)]
    assert len(footers) == len(set(footers)), comments
    assert len(comments) <= (4 if mode == "escalada" else 3), comments
    if mode == "escalada":
        assert any("impedimento" in c.lower() for c in comments), comments
    assert not re.search(r"/Users/|/home/|github_pat_|AKIA[0-9A-Z]{16}|\.agent_plans/", issue["body"] + "\n".join(comments))
print("resultado: passou")
PY
