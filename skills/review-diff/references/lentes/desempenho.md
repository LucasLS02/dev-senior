# Lente: desempenho

## Quando roda

Pela triagem do `SKILL.md`.

## Como procurar

1. Consulta ou chamada externa dentro de laço: conte quantas acontecem com 1
   item e com 10 itens.
1. Listagem ou consulta sem limite sobre tabela que cresce.
1. Coleção carregada inteira para usar uma parte; trabalho repetido dentro do
   laço que podia sair dele.
1. Dependência nova de frontend: o tamanho no bundle, se o repositório mede.
1. No perfil `próprio`, se houver teste, rode-o contando consultas ou chamadas.

## O que conta como evidência

A linha do laço, a chamada de E/S dentro dele e a contagem (por exemplo: com 1
item, 2 consultas; com 10 itens, 11). Tempo de relógio nunca é evidência.

## Não é desta lente

Otimização que não muda nenhuma contagem: não é achado.
