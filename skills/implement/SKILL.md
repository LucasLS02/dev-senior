---
name: implement
description: >-
  Use quando for preciso executar uma spec aprovada de ponta a ponta: confere a prontidão,
  implementa as tarefas com os testes antes do código, verifica cada critério de aceite, chama
  o review-diff, corrige o que não tem gatilho de parada, para nos que têm e entrega o relatório
  e o plano de commits sem commitar. Disparos: "implementar a spec", "executar a spec",
  "implement", "/implement".
metadata:
  opencode/slash: "true"
---

# Implement

Executa uma `.agent_plans/<pasta>/spec.md` aprovada e prova que cada critério
passa. Você orquestra: não decide o que construir (isso é da spec), não commita,
nunca faz push, não abre PR e não cria branch. Grava só o código e os testes que
a spec permite, mais `.agent_plans/<pasta>/progress.md`, o estado operacional
que você e o humano leem.

Leia antes de começar `references/modelo-progress.md` (o `progress.md`),
`references/pacote.md` (o que cada implementador recebe) e
`references/gatilhos.md` (as paradas). O que dá para medir, mede
`scripts/check_run.py`, desta pasta, rodado na raiz do repositório: `tree`
(impressão digital da árvore), `triggers <spec>`, `quality <spec>`,
`progress <progress> <spec>` e `converge <progress> <spec>`. A ferramenta
calcula; você interpreta e nunca conta lendo o código.

**Qualquer gatilho para.** Você pode acrescentar uma parada com o motivo por
escrito; nunca remove uma.

## Entrada

A pasta `.agent_plans/<pasta>/` com a `spec.md`. Sem ela, pergunte qual é. Se já
existe `progress.md`, é retomada: leia-o, rode `converge` e `tree`, e continue na
primeira tarefa que não está `concluída`, sem refazer o que tem evidência
válida.

## 1. Prontidão

Confira e registre cada item na tabela `Prontidão` do `progress.md`:

- Rode `check_spec.py <spec> .` (está em `scripts/` na skill `spec`; sem ela, confira
  o formato à mão e diga no relatório que a spec não passou por script).
- `Status: aprovado` no cabeçalho.
- Zero `[PRECISA DECISÃO: …]` na spec.
- Árvore de trabalho limpa fora de `.agent_plans/`. Mudança que já estava lá é
  do humano e se misturaria com o diff: pergunte antes de seguir.

Use os nomes de linha do exemplo em `references/modelo-progress.md` para que
o verificador de acompanhamento consiga reconhecer as quatro checagens.

Falhou qualquer item: grave o `progress.md` só com a prontidão, **pare e
pergunte**, sem escrever código. Passou: crie as linhas de todos os AC e de todas
as tarefas como `pendente`.

Se o `AGENTS.md` da raiz tiver `## Acompanhamento de projeto`, chame `track` com
a pasta e origem `implement` na prontidão aprovada, em cada escalada, quando a
decisão for registrada e na entrega. Sem a seção, não chame.

## 2. Tarefas

Em ordem de `Depende de`, uma de cada vez. Paralelo só para tarefas de arquivos
disjuntos, sem interface em comum e só quando há delegação; na dúvida, em
sequência.

Para cada tarefa, monte o pacote de `references/pacote.md` e entregue ao
implementador. Com delegação, um subagent novo por tarefa; sem ela, você mesmo, e
então só o pacote vale, sem o resto do contexto. Os testes da `Matriz de casos`
vêm antes do código: veja-os falhar. O implementador não commita.

Quando ele volta:

1. Rode você mesmo o `Pronto quando` da tarefa e leia a saída. O relato dele não
   conta como evidência.
2. Rode `check_run.py triggers <spec>`. Qualquer linha é um gatilho: não siga,
   vá a "Gatilhos e escalada". O diff é cumulativo: linha cuja decisão do humano
   já está em `Escaladas e decisões` não para de novo, salvo se a mudança
   aprovada deixou de ser a descrita.
3. Marque a tarefa `concluída`, com os arquivos alterados, na tabela `Tarefas`.

Teste que já existia e passa a falhar por causa da mudança pedida **não se
altera para passar**: é G6, quase sempre com S1 (a spec e o código discordam).
Pare e escale. Condição de parada que o implementador citar, ou incerteza que
ele devolver, também é gatilho (S2 ou S3).

## 3. Critérios

Rode a verificação de cada AC e de cada AC-Q na árvore atual. Na tabela
`Critérios de aceite` grave o status, o comando com o sinal da saída e a
impressão que `check_run.py tree` devolve naquele momento (coluna `Estado da
árvore`). AC de tipo `manual` não se prova sozinho: deixe `pendente` (só o
`converge` aceita isso, e só para AC manual), descreva o passo no relatório e
peça o ok junto com a entrega; com o ok vira `passou`, com a evidência "ok do
humano: <o que conferiu>".

AC que passava e deixou de passar, e não voltou em uma tentativa: P3.

## 4. Qualidade

Rode `check_run.py quality <spec>` e o que o linter ou a configuração do
repositório medirem (complexidade, duplicação, consultas); preencha a tabela
`Qualidade` com antes, depois, limite e origem. Métrica é um olhar a mais, não
veredito. Sem ferramenta, escreva "não medido" e o motivo.

## 5. Review

Chame a skill `review-diff` no perfil `próprio`, alvo a árvore de trabalho, com a
spec, gravando em `.agent_plans/<pasta>/findings.md`. Copie cada achado para a
tabela `Achados` (ID, severidade, veredito, gatilho `—`, ação, resultado
`aberto`). Mais de 10 confirmados na mesma tarefa: P4, o problema é a
implementação ou a spec.

## 6. Correções

Para cada achado, por veredito:

- `refutado`: resultado `refutado`.
- `plausível`: S7. Não corrige; vai para a escalada.
- `confirmado`: avalie os gatilhos. `check_run.py triggers <spec>` cobre G1 a G7 e
  o orçamento de arquivos; os outros (G8, o resto de G9, S e P) são seus, pela
  tabela de `references/gatilhos.md`. Compare `git diff --numstat` antes e depois
  de cada correção para o teto de G8.

Sem gatilho: corrija pelo Modo local da skill `pr-feedback`, passando o
`findings.md` (o gatilho que você aplicou faz o papel do "implementar?"), uma
correção por achado, cada uma separável das outras. Rode de novo o que ela
afetou, depois o `review-diff` só dos arquivos tocados, gravando em
`re-review.md`. Resultado `corrigido`, com os arquivos na coluna `Ação`.

Com gatilho: não corrija; resultado `escalado`, ID do gatilho na coluna
`Gatilho`.

Duas falhas da mesma correção na verificação: P1. Terceira rodada de review e
correção na mesma tarefa: P2.

## Gatilhos e escalada

Os escalados de uma rodada vão **em lote**, enquanto os que não tocam os mesmos
arquivos seguem sendo corrigidos. Cada escalada leva o formato de
`references/gatilhos.md` (gatilho, motivo, arquivos, efeito, alternativas,
recomendação) e entra em `Escaladas e decisões` com o ID. A aprovação do humano
vale para a mudança descrita; se a solução mudar de forma relevante, deixa de
valer. Enquanto houver escalada sem resposta, não existe "pronto": explique
onde parou e o que precisa ser decidido.

Grave cada bloco completo no formato de `references/modelo-progress.md`, com
`Decisão: pendente` antes de escalar e a resposta no mesmo campo ao retomá-lo.

## 7. Convergência

Rode de novo toda a tabela de verificação, os AC e o `Pronto quando` de cada
tarefa, na árvore final; atualize evidências e a impressão `tree`. Só então rode
`check_run.py converge <progress> <spec> .`: ele tem de sair limpo. Confira
também que o último `review-diff` não deixou crítico ou alto confirmado em
aberto. Se `converge` reclama, o trabalho não terminou; mostre o motivo, não
contorne editando a tabela.

## 8. Entrega

Escreva o relatório: critérios com a evidência, achados (corrigidos sozinhos,
refutados, pendentes, escalados com o gatilho), qualidade e as paradas com o ID.
Monte o mapa tarefa → arquivos (uma linha por tarefa e uma por correção de
review) e peça o plano de commits à skill `smart-commit`, entregando o mapa como
dica de agrupamento. Apresente relatório e plano e **pare**: a aprovação é do
humano. Esta skill não commita e nunca faz push.

Toda ação relevante vira uma linha em `Log` (só acrescenta).

## Erros comuns

| Erro | Correção |
|---|---|
| Declarar pronto com a spec reprovada no validador | Prontidão falhou: pare e pergunte |
| Alterar teste existente para a implementação passar | G6: escale, não edite |
| Aceitar o "passou" do implementador | Rode o `Pronto quando` você mesmo |
| Reusar evidência de antes de uma edição | `converge` compara com `tree`: rode de novo |
| Corrigir achado com gatilho "porque é pequeno" | Gatilho para sempre; só o humano libera |
| Contar complexidade ou linhas lendo o código | `quality`, `git diff --numstat`, o linter |
| Commitar ou propor push para "fechar" | Só o plano de commits, e a aprovação é do humano |
