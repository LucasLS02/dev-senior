---
name: pr-review
description: 'Use when asked to review someone else''s GitHub pull request in a Propay repo and leave validated inline comments — "revisar PR", "fazer review da PR", "code review da PR #N", "/pr-review". Not for reviewing your own uncommitted changes.'
metadata:
  opencode/slash: "true"
---

# PR Review

Orquestra um review de PR do GitHub: uma revisão detalhada acha os pontos, o agente principal valida cada um com evidência, o usuário aprova, e só então os pontos viram comentários inline.

**Entrada:** número ou URL da PR (obrigatório) e link do card (opcional).

## Pipeline

```
Contexto → Review detalhado → Validação → GATE: aprovação → Postagem
```

Se uma etapa falhar, pare e reporte. Não pule etapas.

### 1. Contexto

Rode no diretório do repo da PR:

```bash
gh pr view <N> --json number,title,body,url,baseRefName,headRefName,headRefOid,closingIssuesReferences,files
git fetch origin pull/<N>/head:refs/remotes/origin/pr/<N>   # código da PR em origin/pr/<N>, sem checkout
```

- **Card:** use os issues em `closingIssuesReferences` (`gh issue view`) e os links da descrição. Se o card estiver numa ferramenta que você não consegue abrir, peça para o usuário colar o conteúdo. Não invente requisito.
- **Idioma:** os comentários saem no idioma da descrição da PR.

### 2. Review detalhado

Se uma ferramenta ou skill de revisão independente estiver disponível, use-a em modo somente leitura, com a URL completa da PR, e aguarde os achados. Caso contrário, faça uma revisão detalhada você mesmo, sem modificar arquivos ou postar comentários: compare o diff da PR com a base, examine o contexto e os testes e procure bugs, regressões e falhas relevantes. Use o código da versão da PR, não o branch local. Se não conseguir acessar a versão correta ou concluir a revisão, pare e reporte.

### 3. Validação (agente principal)

Para cada achado, leia o código na versão da PR (`git show origin/pr/<N>:<arquivo>`, `git grep <símbolo> origin/pr/<N>`) e cruze com a descrição da PR e o card.

| Achado chegou como | O que fazer |
|---|---|
| CONFIRMED | Checagem rápida: a linha existe e diz o que o achado afirma? |
| PLAUSIBLE ou sem verdict | Verificação completa: chamadores, testes existentes, cenário de falha reproduzível no raciocínio |
| Depende de regra de negócio ou de contexto fora do código | Pergunte ao usuário com uma pergunta específica e diga qual evidência falta |

Cada achado termina em **confirmado** (há evidência concreta: `arquivo:linha`, trecho, saída de comando), **refutado** (diga em uma linha por quê) ou **pendente do usuário**.

### 4. GATE: aprovação

Apresente:
1. **Confirmados.** Para cada um, exatamente o comentário que vai ser postado (formato abaixo).
2. **Refutados.** Uma linha cada, para o usuário ver o que foi descartado.
3. **Pendentes.** A pergunta para o usuário.

**PARE.** Não poste nada até o usuário aprovar explicitamente. Se ele editar ou remover pontos, aplique antes de postar.

### 5. Postagem

Todos os comentários vão em **um único review** com `event=COMMENT` (gera uma notificação, não várias). Monte o JSON no scratchpad:

```json
{
  "commit_id": "<headRefOid>",
  "event": "COMMENT",
  "body": "<N pontos encontrados; achados fora do diff, se houver, listados abaixo>",
  "comments": [
    {"path": "src/x.py", "line": 42, "side": "RIGHT", "body": "<comentário>"},
    {"path": "src/y.py", "start_line": 10, "line": 14, "side": "RIGHT", "start_side": "RIGHT", "body": "<comentário>"}
  ]
}
```

```bash
gh api repos/{owner}/{repo}/pulls/<N>/reviews --input <arquivo.json>
```

O `body` é obrigatório quando `event=COMMENT`, então nunca o deixe vazio. O GitHub só aceita comentário inline em linha que aparece no diff (senão devolve 422). Achado em linha fora do diff entra no `body` do review, prefixado com `` `arquivo:linha` ``.

Ao final, mostre o link do review (`html_url` da resposta).

## Formato do comentário

Cada comentário tem exatamente estas três partes, nesta ordem:

```markdown
**Problema:** <o que está errado, em uma frase direta>

**Evidência:** <o trecho, a linha, o chamador ou a saída que prova o problema, com `arquivo:linha`>

**Impacto:** <o que quebra, em qual cenário, para quem>
```

O local já vem da âncora inline. O comentário termina no Impacto: a correção é decisão do autor da PR. Use os rótulos traduzidos quando o idioma for inglês (`Problem / Evidence / Impact`).

## Erros comuns

| Erro | Correção |
|---|---|
| Postar achado que só o subagent afirmou | Todo comentário precisa ter passado pela Validação com evidência |
| Postar antes do "pode postar" | O GATE é obrigatório, mesmo com um único achado |
| Um review por comentário | Um único review com todos os comentários |
| Linha fora do diff no array `comments` | Mover para o `body` do review |
| Ler o código do branch local em vez da PR | Usar sempre `origin/pr/<N>` |
