---
name: open-pr
description: >-
  Use quando o humano mandar abrir a PR de uma tarefa já implementada e commitada: reverifica
  cada critério de aceite na árvore commitada, monta a descrição a partir da spec e das
  evidências em `.agent_plans/<pasta>/pr.md`, valida com `check_pr.py`, apresenta e, só com
  ordem escrita, empurra a branch e abre a PR em rascunho no GitHub. Disparos: "abrir a PR",
  "criar o PR", "open-pr", "/open-pr".
metadata:
  opencode/slash: "true"
---

# Open PR

Publica o que a skill `implement` entregou e o humano commitou. Duas ações saem
do seu controle, empurrar a branch e abrir a PR, e só acontecem com **ordem
escrita do humano nesta conversa**. Você grava apenas
`.agent_plans/<pasta>/pr.md` (e o corpo sem título, ao lado): não edita código,
não commita e não cria branch.

O formato do `pr.md` e um exemplo válido estão em `references/modelo-pr.md`.
Leia antes de escrever. O que dá para conferir por script, confere
`scripts/check_pr.py`, desta pasta.

## Entrada

A pasta `.agent_plans/<pasta>/` com `spec.md` e `progress.md`. Sem ela, pergunte
qual é.

## 1. Prontidão

Confira e diga o resultado de cada item:

- A branch atual não é a padrão do repositório. Descubra a padrão com
  `git symbolic-ref refs/remotes/origin/HEAD`; sem isso, `main` ou `master`; na
  dúvida, pergunte.
- Há commits à frente da base (`git log <base>..HEAD`).
- Árvore limpa fora de `.agent_plans/`.
- Existe o remoto `origin`. Se ele não é um GitHub, diga: a PR não vai existir
  lá.

Falhou um item: pare e diga qual.

## 2. Verificação

Rode de novo, na árvore commitada, a `Verificação` de cada AC e AC-Q da spec e o
`Pronto quando` de cada tarefa. O `progress.md` é o roteiro, não a evidência: a
impressão digital da árvore muda ao commitar. Rode **cada comando de AC
separadamente**: a suíte inteira verde não prova um critério cujo teste nem
existe.

Um AC falhou, ou o comando dele não roda: **pare, diga qual AC e não abra a PR.**
AC de tipo `manual` entra como `pendente`, com o passo que o revisor deve fazer.

## 3. Descrição

Escreva `.agent_plans/<pasta>/pr.md`: linha 1 `Título: <texto>` (até 72
caracteres, sem ponto final), depois o corpo com as seções `Resumo` (do
`Objetivo` e do `Entendimento` da spec), `Critérios de aceite` (tabela
`| AC | Status | Evidência |` com o que você colheu **agora**), `Achados do
review` (corrigidos, refutados e escalados, e a decisão do humano, do
`progress.md`) e `Riscos e decisões`.

- Há `.github/pull_request_template.md`: siga o template e mantenha a tabela de
  critérios dentro dele.
- Idioma: o das últimas PRs e commits do repositório.
- Sem atribuição de IA: nenhuma linha "Generated with" nem coautoria, a menos
  que a configuração do dono peça.
- Sem caminho de `.agent_plans/`: quem lê a PR não tem a pasta. Descreva o que
  importa em vez de apontar o arquivo.

Rode `python3 check_pr.py <pr.md> <spec.md> .` e corrija até sair `limpo`.
Grave também o corpo, sem a linha de título, em
`.agent_plans/<pasta>/pr-corpo.md`, que é o que vai para o `gh`.

## 4. Apresentar e parar

Mostre a branch, a base, o remoto, os commits (`git log --oneline`), o título, o
corpo e que a PR vai como rascunho. **Sem ordem escrita do humano nesta
conversa, termine aqui.** Pedir "prepare a PR", ter aprovado o plano de commits
do `implement` ou ter aprovado a spec não é ordem de push.

## 5. Executar, com ordem

0. O humano pode ter editado o `pr.md`: grave de novo o `pr-corpo.md` (o `pr.md`
   sem a linha de título e a linha em branco) e rode `check_pr.py`, que também
   confere se o `pr-corpo.md` é o corpo do `pr.md`. Só siga com `limpo`.
1. `gh pr list --head <branch>`: se já existe PR dessa branch, não crie outra;
   ofereça atualizar a descrição e espere. Se o `gh` falhar, pare e diga o erro.
2. `git push -u origin <branch>`.
3. `gh pr create --draft --base <base> --title "<título>" --body-file
   .agent_plans/<pasta>/pr-corpo.md`. Sem `--draft` só se o humano pediu.
4. Devolva a URL e diga que está em rascunho. Marcar como pronta para revisão
   é outra ordem.

## Nunca

- `--force` ou `--force-with-lease` num push.
- Push para a branch padrão do repositório, ou PR com a base errada.
- Merge, fechar, comentar, editar ou marcar como pronta uma PR de outra pessoa,
  ou qualquer PR sem ordem.
- Abrir a PR com um AC falhando ou sem prova.
- Atribuição de IA em commit ou na descrição.
- Caminho de máquina (`/Users/…`) ou credencial na descrição, nem dentro da saída
  colada como evidência.
- Tratar uma aprovação de antes como ordem agora.

## Erros comuns

| Erro | Correção |
|---|---|
| Confiar no `progress.md` em vez de rodar os comandos | Rode cada verificação na árvore commitada |
| Rodar só a suíte inteira | Rode o comando de cada AC: teste inexistente também passa a suíte |
| Abrir normal quando ninguém pediu | `--draft` é o padrão |
| Citar `.agent_plans/` ou a spec por caminho na descrição | O leitor não tem a pasta; resuma |
| Descrição só na resposta, sem `pr.md` | O humano lê e edita o arquivo antes de dar a ordem |
| Empurrar porque o plano de commits foi aprovado | Aprovar commits não é ordem de push |
