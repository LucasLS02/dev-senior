# Lente: manutenção e complexidade

## Quando roda

Pela triagem do `SKILL.md`.

## Como procurar

1. Abstração com uma implementação só, fábrica para um produto só,
   configuração para valor que nunca varia.
1. Código morto que o diff adiciona: função sem chamador, ramo impossível,
   parâmetro ignorado.
1. Complexidade: só pela ferramenta configurada no repositório (por exemplo,
   `ruff` com `C901` ou a regra `complexity` do `eslint`), rodada nos arquivos
   alterados. Sem ferramenta, não afirme número.
1. Função alterada com mais de 50 linhas ou aninhamento acima de 4 níveis:
   aponte o trecho e o padrão mais simples que o repositório já usa para o
   mesmo caso.

## O que conta como evidência

A saída da ferramenta; ou a linha mais o exemplo mais simples que já existe no
repositório (`arquivo:linha`).

## Não é desta lente

Helper que já existe (conformidade). Gosto pessoal sem padrão no repositório
não é achado.
