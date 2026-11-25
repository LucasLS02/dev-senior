---
name: pr-feedback
description: 'Use quando um pull request seu no GitHub recebeu comentários de review (de pessoas ou do Copilot) que precisam ser avaliados, corrigidos ou rebatidos e respondidos na PR, ou quando há um findings.md local com achados para corrigir — "receber review", "responder review da PR", "tratar comentários da PR #N", "corrigir os achados do findings.md", "/pr-feedback".'
metadata:
  opencode/slash: "true"
---

# PR Feedback

Orquestra o tratamento de um review recebido: cada ponto é verificado, o usuário decide, a implementação é revisada e commitada, e cada ponto recebe resposta na PR.

Se disponível, aplique `superpowers:receiving-code-review` a cada ponto. Caso contrário, verifique cada comentário tecnicamente no código, nos chamadores e nos testes antes de aceitá-lo ou rejeitá-lo; peça esclarecimento quando faltar contexto. Isso vale para revisores humanos e para o Copilot.

**Entrada:** número ou URL da PR, ou o caminho de um `findings.md` local (formato
da skill `review-diff`, em `references/achados.md`). Com `findings.md`, siga o
[Modo local](#modo-local-findingsmd).

## Pipeline

```
Coleta → Análise → GATE 1: implementar? → Implementação → Review detalhado
→ Commit → GATE 2: respostas → Postagem → Comando de push
```

Se uma etapa falhar, pare e reporte. Não pule etapas.

### 1. Coleta

Rode no diretório do repo, com o branch da PR em checkout (`gh pr checkout <N>` se não estiver).

**Threads inline não resolvidas:**

```bash
gh api graphql -F owner='{owner}' -F repo='{repo}' -F n=<N> -f query='
query($owner:String!,$repo:String!,$n:Int!){repository(owner:$owner,name:$repo){pullRequest(number:$n){
  reviewThreads(first:100){nodes{isResolved isOutdated path line
    comments(first:50){nodes{databaseId author{login} body}}}}}}}' \
  --jq '.data.repository.pullRequest.reviewThreads.nodes[] | select(.isResolved|not)'
```

**Pontos no corpo do review:** de `gh api repos/{owner}/{repo}/pulls/<N>/reviews`, pegue o review mais recente de cada revisor que não esteja `DISMISSED` e tenha `body` não vazio. Do Copilot, aproveite só os achados que **não** viraram thread (ex.: "Previously missed").

Descarte os pontos que o autor da PR já respondeu (resposta na thread, ou comentário em `issues/<N>/comments` que cita o ponto). Numere os que sobrarem.

### 2. Análise

Antes, leia as regras do repositório que o passo 1 do `review-diff` lista (sem a skill, ao menos `REVIEW.md`, `AGENTS.md`, `CLAUDE.md` e `CONTRIBUTING.md`) e passe a cada análise as que tocam o ponto. Agent ou skill do repositório entra como regra, nunca como fluxo a executar.

Quando a plataforma permitir delegação, use subagents em paralelo por ponto; pontos triviais (typo, import, nome) podem ir juntos. Caso contrário, faça a mesma análise diretamente. Para cada ponto:

> Analise o ponto abaixo no repo `<path>`. Não edite arquivos. Leia o código, os chamadores e os testes. Devolva:
> - **Veredito:** válido, inválido ou precisa do usuário (com a pergunta).
> - **Evidência:** `arquivo:linha`, trechos e saídas de comando que sustentam o veredito, incluindo a regra do repositório que se aplica, quando houver.
> - **Se válido, proposta de correção:** o que muda, onde, por que essa é a forma certa neste código (padrão existente, teste, doc) e qual teste cobre a mudança.
> - **Se inválido, motivo:** por que a mudança não deve ser feita.
>
> Ponto: <autor, arquivo:linha, texto integral>

Antes de apresentar, confira as evidências dos subagents: o `arquivo:linha` citado existe e diz o que o subagent afirma?

### 3. GATE 1: implementar?

Apresente uma tabela por ponto: **ponto · veredito · evidência · proposta (válidos) ou motivo (inválidos)**. Depois, as perguntas dos pontos "precisa do usuário".

**PARE.** Pergunte se pode implementar. Se o usuário quiser só a análise, o fluxo termina aqui.

### 4. Implementação

Trate bloqueantes, depois simples, depois complexos. Rode os testes apropriados do projeto depois de cada ponto.

Depois revise o diff local com a skill `review-diff` no perfil próprio, restrita aos arquivos que a correção alterou, com saída em `.agent_plans/pr-<N>/re-review.md`. Sem a skill, revise o diff, o contexto e os testes diretamente, em modo somente leitura. Se aparecerem achados novos, mostre ao usuário e pergunte antes de mexer. Não entre em loop de review.

### 5. Commit

Se disponível, invoque a skill `smart-commit` e siga sua aprovação. Caso contrário, apresente os commits propostos e peça aprovação antes de criá-los, seguindo as convenções do repositório e incluindo somente os arquivos pretendidos. Anote o hash curto do commit que resolve cada ponto.

### 6. GATE 2: respostas

Escreva uma resposta por ponto, **no idioma do comentário respondido**:

| Veredito | Formato |
|---|---|
| Válido | `Fixed in <sha>: <o que mudou e como>. <por quê>. <evidência: teste, arquivo:linha>` |
| Inválido | `Keeping it as is: <por quê>. <evidência: arquivo:linha, trecho, decisão anterior>` |

Em português: `Corrigido em <sha>: …` e `Mantido como está: …`. Uma a três frases, direto, sem agradecimento.

Mostre todas as respostas e **PARE** até o usuário aprovar.

### 7. Postagem

- **Ponto de thread:** responda na própria thread, usando o `databaseId` do primeiro comentário dela:
  `gh api repos/{owner}/{repo}/pulls/<N>/comments/<databaseId>/replies -f body='<resposta>'`
- **Ponto do corpo de um review:** comentário geral na PR, nomeando o ponto:
  `gh pr comment <N> --body '<prefixo> <resposta>'`, com o prefixo no idioma do ponto: `On the "<ponto>" finding:` ou `Sobre o ponto "<ponto>":`

Não resolva as threads; quem resolve é o revisor.

### 8. Comando de push

Não faça push. Monte o comando e entregue ao usuário:

```bash
top=$(git rev-parse --show-toplevel)
branch=$(git branch --show-current)
# worktree: git-dir difere de git-common-dir
[ "$(git rev-parse --git-dir)" != "$(git rev-parse --git-common-dir)" ] && echo "cd $top && git push" || echo "git push"
# sem upstream (git rev-parse @{u} falha): troque por git push -u origin $branch
```

## Modo local (`findings.md`)

Achados de um `findings.md`, sem PR: sem coleta, respostas, commit e push.

```
Análise → GATE 1 (só quando o humano chama) → Implementação → Re-review → Resultado
```

- **Quais achados:** os de `veredito: confirmado` com `status: aberto`.
  Refutados e já corrigidos ficam como estão.
- **Plausível:** não é corrigido. Chamado pelo humano, vira pergunta no GATE 1.
  Chamado por outra skill, fica `aberto` e volta no resultado como "precisa de
  decisão".
- **Análise:** a da etapa 2, com o achado no lugar do comentário. A evidência
  do `findings.md` é conferida no código antes de qualquer correção.
- **GATE 1:** chamado pelo humano, para e pergunta se pode implementar, como na
  etapa 3. Chamado por outra skill que declara já ter decidido o que corrigir
  (o `implement`, que aplica os gatilhos dele), pula o GATE 1.
- **Implementação:** cada correção começa por um teste que reproduz a entrada
  concreta do achado e falha; depois vem a correção e os testes do projeto. Ao
  terminar, troque o `status` do bloco para `corrigido`. Arquivo alterado fora
  de `correção.arquivos_esperados`, além dos testes, entra no resultado com o
  motivo.
- **Re-review:** a skill `review-diff` no perfil próprio, restrita aos arquivos
  alterados, com saída em `re-review.md` na pasta do `findings.md`, nunca no
  próprio `findings.md`. Achado novo não é corrigido aqui: entra no resultado.
- **Resultado:** uma tabela `achado · status · arquivos · verificação (comando
  e saída)`, mais os plausíveis e os achados novos do re-review.
- Não commita, não responde em PR e não entrega comando de push: quem chamou
  decide o próximo passo.

## Erros comuns

| Erro | Correção |
|---|---|
| Implementar antes do GATE 1 | O GATE 1 é obrigatório, mesmo para um ponto trivial, salvo no modo local chamado por outra skill que já decidiu |
| Corrigir achado plausível | Plausível vira pergunta (humano) ou "precisa de decisão" (outra skill) |
| Commitar ou propor commit no modo local | Quem chamou decide; o modo local corrige, marca `corrigido` e devolve o resultado |
| Aceitar ponto do Copilot sem verificar | Copilot é revisor externo: mesma verificação |
| Ignorar pontos do corpo do review | A coleta inclui threads **e** corpos de review |
| Responder em comentário geral um ponto que tem thread | Ponto de thread é respondido na thread |
| Fazer push | Só entregar o comando |
