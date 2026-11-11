# Lente: requisito

## Quando roda

Sempre. Sem spec nem card, registre na Cobertura que não houve fonte de
requisito e não produza achado desta lente.

## Como procurar

1. Liste cada critério de aceite (AC) da spec, ou cada item do card, com a
   frase exata.
1. Para cada um, ache no diff o código que o cumpre (`arquivo:linha`). Confira
   valores, unidades, formatos, nomes de campo e cada caso especial que o
   pedido escreve.
1. Item sem código que o cumpra, ou cumprido de forma diferente da escrita:
   candidato.
1. Comportamento novo que nenhum item pede: candidato `médio`, por escopo além
   do pedido.
1. Com spec, confira a matriz de casos: cada linha que aponta para um AC
   precisa estar cumprida.

## O que conta como evidência

O ID do AC ou o trecho do card, citado, mais o `arquivo:linha` do código que
diverge. Quando der, a saída de um comando que mostra o valor errado.

## Não é desta lente

Bug sem relação com o pedido (correção), teste faltando (testes), regra do
repositório (conformidade).
