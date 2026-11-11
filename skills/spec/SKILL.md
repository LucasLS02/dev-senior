---
name: spec
description: >-
  Use quando for preciso transformar um brief aprovado, ou um pedido direto pequeno e claro,
  numa spec verificável em `.agent_plans/<pasta>/spec.md`: investiga o código, decide o reuso,
  escreve critérios de aceite executáveis e tarefas, valida com `check_spec.py` e para para
  aprovação. Disparos: "criar a spec", "especificar a tarefa", "escrever spec a partir do
  brief", "/spec".
metadata:
  opencode/slash: "true"
---

# Spec

Transforma a necessidade aprovada num contrato que outra pessoa, ou outro
agente, executa sem adivinhar e que o review confere linha a linha. A spec diz
**o que** vale como pronto e **onde** mexer; não escreve o código do produto.
Esta skill só grava `.agent_plans/<pasta>/spec.md`: não edita código, não
commita, não cria branch.

O formato está em `references/modelo.md`; uma spec completa e válida está em
`references/exemplo.md`. Leia os dois antes de escrever.

## Entrada e modo

- **Com brief:** leia `.agent_plans/<pasta>/brief.md`. Se o `Status` não for
  `aprovado`, pare e diga isso. O `Modo` (`rápido`, `padrão` ou `profundo`)
  vem do brief e a spec o repete; `profundo` usa o formato do `padrão`.
- **Sem brief (pedido direto):** só `rápido` ou `padrão`. `rápido` exige
  mudança clara, pequena e fora de migração e de caminho sensível
  (autenticação, pagamento, dados de usuário); fora disso, `padrão`, e o que o
  pedido não esclarece vira dúvida (abaixo). O cabeçalho leva `Brief: —`.
- **Pasta:** nome curto em kebab-case ASCII, tirado do título do brief ou do
  pedido. Se `.agent_plans/<pasta>/spec.md` já existe, leia-o e atualize em vez
  de recomeçar.
- Pedido pequeno e claro **não dispensa a spec**: o modo `rápido` existe para
  ele (só Objetivo, Escopo, Critérios de aceite e Tarefas, em poucas linhas).
  Quem recebe um pedido assim escreve a spec rápida e para; não implementa.

## Fase 1: investigar antes de desenhar

No modo `rápido` basta o que o Escopo precisa: o arquivo a mudar e o teste que
já o cobre. Nos demais modos, nesta ordem:

1. Leia o `AGENTS.md` da raiz e o das pastas no caminho da mudança, os
   `docs/agents/` pertinentes e o `REVIEW.md`, se existirem.
2. Rode `git log --oneline -- <arquivos que a tarefa toca>` e leia o corpo dos
   commits de correção (`fix`): cada erro já corrigido ali que a tarefa pode
   repetir é um caso a pôr na matriz.
3. **Padrões aplicáveis:** cada regra da casa que toca a tarefa, aplique-se ou
   não, com o `arquivo:linha` onde está escrita (confira o número com `grep -n`).
4. **Referências no código:** de uma a três funcionalidades parecidas que já
   existem, com `arquivo:linha` e o que imitar.
5. **Reuso:** para cada coisa que a tarefa criaria (função, tipo, constante,
   arquivo), busque por nome, por sinônimos e pela chamada de biblioteca que
   ela faria. Registre os termos buscados, o que achou com `arquivo:linha` e
   decida `Reusar`, `Adaptar` ou `Criar`, com o motivo. `docs/agents/reuse.md`
   é ponto de partida, nunca substituto da busca.

## Fase 2: desenhar

- **Entendimento:** a necessidade reescrita com suas palavras e um cenário de
  demonstração que um humano repetiria.
- **Decisões:** cada escolha com a alternativa mais simples e por que ela não
  serve. Sem alternativa mais simples, não há decisão a registrar.
- **Escopo:** arquivos permitidos, proibidos e o que exige aprovação. O
  orçamento (arquivos novos, abstrações novas, dependências novas) começa em
  zero; número acima de zero precisa de uma decisão que o justifique.

## Fase 3: verificar

- **Matriz de casos:** aplique cada categoria a cada entrada concreta da
  tarefa (o campo, o argumento, o arquivo), nomeando a entrada: entrada vazia,
  inválida, limite, erro de dependência, concorrência, permissão e estado
  anterior. Categoria que não cabe ganha a linha `não se aplica: <motivo>`.
  Mais uma linha por correção anterior achada na Fase 1. A última coluna é um
  `AC-NNN` ou `fora de escopo: <motivo>`; caso sem destino é lacuna.
- **Critérios de aceite:** `QUANDO <condição> ENTÃO <resultado observável>`,
  uma `Verificação` executável com o sinal esperado e o `Tipo`.
- **Critérios de qualidade:** `AC-Qnn`, sempre com arquivo ou comando que
  prova. Critério de desempenho só em superfície quente (consulta, laço sobre
  coleção, listagem) e sempre como contagem (consultas com 1 e com 10 itens,
  chamadas externas), nunca como tempo.
- **Tarefas:** `Cobre`, `Arquivos`, `Interfaces` e `Pronto quando` com comando
  e sinal. `[P]` só em tarefas que não dividem arquivo com outra.
- **Rastreabilidade:** derivada das tarefas; todo AC aparece, toda tarefa
  cobre algum AC.

## Dúvida

Pergunta sem resposta no código, no brief ou no card (um termo que ninguém
define, uma regra de negócio ausente) vira `[PRECISA DECISÃO: <a pergunta,
nomeando o termo>]` no lugar exato em que a resposta entra. Nunca invente regra
de negócio nem escolha em silêncio uma leitura do termo.

O marcador é só para o que apenas o dono do pedido sabe (regra de negócio, termo
sem definição). Escolha de desenho que o código permite resolver, como o
comportamento numa entrada vazia ou no limite, ou por onde um dado novo entra
numa função, **você decide**: registre em `Decisões` e escreva o caso na matriz.

**Grave o rascunho com os marcadores antes de perguntar.** Depois pergunte, no
máximo cinco perguntas por rodada, e substitua cada marcador pela resposta. Se
ninguém pode responder agora (execução sem interação), termine listando os
marcadores abertos: a spec existe e o validador os aponta.

## Validar e parar

1. Rode `python3 <pasta desta skill>/scripts/check_spec.py <spec.md> .` na raiz
   do repositório e corrija até a saída ser `limpo`. Cada linha de erro traz o
   número da linha. Linha `marcador pendente` não se corrige: é pergunta aberta.
2. Com o validador limpo, **PARE** e peça a aprovação. O `Status` fica
   `rascunho`; só quem aprova o muda para `aprovado`, e o validador roda de novo.
3. Na resposta final: o caminho da spec, o número de linhas, os marcadores
   abertos e as decisões que mais merecem os olhos de quem aprova.

## Regras de escrita

- Spec maior que o código que descreve é transcrição: corte. Sem seção
  decorativa, sem repetir o brief.
- Só fato com `arquivo:linha` entre crases; o validador confere que o arquivo e
  a linha existem. Sem número de linha, não é citação.
- Imperativo e verificável: nada de "deveria", "idealmente", "robusto".
- Português do brief; identificadores e comandos como estão no código.
