---
name: refine
description: >-
  Use quando for preciso entender e questionar um pedido antes de especificar: transforma um
  card, uma descrição ou uma conversa em `.agent_plans/<pasta>/brief.md` (problema, pedido
  contra necessidade, opções, recomendação), com diagnóstico quando o pedido é um bug, valida
  com `check_brief.py` e para para aprovação. Disparos: "refinar o pedido", "entender a
  necessidade", "criar o brief", "investigar o bug", "/refine".
metadata:
  opencode/slash: "true"
---

# Refine

Antes de decidir **como** fazer, decide **se** e **o quê**: reescreve a necessidade,
duvida do pedido, compara opções (inclusive não fazer) e recomenda uma. O resultado é o
brief que a `spec` lê. Esta skill só grava `.agent_plans/<pasta>/brief.md`: não edita
código, não escreve a spec, não commita.

O formato está em `references/modelo.md`; um brief completo e válido está em
`references/exemplo.md`. Leia os dois antes de escrever.

## Entrada, porta e modo

- **Entrada:** card, descrição ou conversa. Classifique a porta: **funcionalidade**
  (necessidade aberta ou ambígua) ou **bug** (comportamento errado).
- **Mudança rápida não passa por aqui.** Se o pedido é claro, pequeno e fora de migração
  e de caminho sensível (autenticação, pagamento, dados de usuário), diga em uma frase que
  é caso da `spec` no modo `rápido` e pare.
- **Modo:** `padrão` ou `profundo` (profundo: risco alto, dado sensível ou muitas
  superfícies). Registre o modo e o motivo na primeira linha de `Apetite`:
  `Modo padrão: <motivo>`.
- **Pasta:** nome curto em kebab-case ASCII, tirado do pedido. Se o brief já existe, leia-o
  e atualize em vez de recomeçar. `Origem` é o id do card, ou `conversa`.

## Entender antes de propor

1. Reescreva a necessidade com suas palavras e separe `Pedido:` (o que foi dito) de
   `Necessidade:` (o que resolve de fato). Os dois quase nunca são a mesma frase.
2. Duvide: o problema é real? Qual a evidência (quem sofre, quando, quantas vezes)? O
   pedido resolve a necessidade ou só parece resolver?
3. Olhe o código o bastante para saber o que já existe: o `AGENTS.md`, o histórico dos
   arquivos que o pedido tocaria e uma busca por nome e por sinônimo do que se pede
   construir. Cite `arquivo:linha` entre crases só onde o brief afirma algo sobre o código.
4. **Referências de mercado:** só com pesquisa disponível e só de fonte que você abriu
   (URL ou arquivo). Sem pesquisa, a tabela leva uma linha `—`. Nunca invente fonte.

## Opções e recomendação

- Sempre inclua **não fazer** e **resolver sem código**, mais as opções que o problema
  pedir. Cada uma com prós, contras e veredito (`Recomendada` ou `Descartada`);
  **exatamente uma** é a recomendada.
- Se o que se pede já existe, ou o custo não se paga, a recomendada é **não fazer**, com o
  motivo e a citação do que já resolve. O `Status` continua `rascunho`: quem marca
  `descartado` é o humano.
- Se falta uma informação que decide a escolha, a recomendada pode ser "definir o critério
  primeiro" e a pergunta entra como marcador.

## Bug (modo diagnóstico)

Acrescente `## Diagnóstico` com cinco linhas: **Reprodução** (o comando que mostra a falha
e o que ele imprime), **Causa raiz** (`arquivo:linha` e o porquê), **Comportamento atual**,
**Comportamento esperado** e **Deve permanecer igual**. Reproduza antes de afirmar a causa;
se não reproduzir, a Causa raiz vira marcador.

## Dúvida

Pergunta sem resposta no código, no card ou na conversa vira
`[PRECISA DECISÃO: <a pergunta, nomeando o termo>]` em `Perguntas em aberto`. Marcador é só
para o que apenas o dono do pedido sabe (critério de negócio, termo sem definição). Escolha
que o código permite resolver, **você decide** e registra nas opções.

**Grave o rascunho com os marcadores antes de perguntar.** Depois pergunte, no máximo cinco
perguntas por rodada, e troque cada marcador pela resposta. Sem ninguém para responder
(execução sem interação), termine listando os marcadores abertos: o brief existe.

## Validar e parar

1. Rode `python3 <pasta desta skill>/scripts/check_brief.py <brief.md> .` na raiz do
   repositório até a saída ser `limpo` ou só linhas `marcador pendente`. Essas linhas não
   se corrigem: são perguntas abertas.
2. **PARE** e peça a aprovação. O `Status` fica `rascunho`; só o humano muda para
   `aprovado` ou `descartado`, e o validador roda de novo.
3. Na resposta final: o caminho do brief, os marcadores abertos e a recomendação em uma
   linha.

## Regras de escrita

- Brief maior que o problema é transcrição: corte. Sem seção decorativa.
- Só fato com `arquivo:linha`; sem número de linha, não é citação.
- Imperativo e verificável; nada de "deveria", "idealmente", "robusto".
- Português do card; identificadores e comandos como estão no código.
