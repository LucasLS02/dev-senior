# Lente: testes e casos alternativos

## Quando roda

Sempre.

## Como procurar

1. Para cada comportamento que o diff adiciona ou altera, monte a matriz de
   casos: vazio, inválido, limite, erro de dependência, concorrência,
   permissão, estado anterior e cada caso especial escrito na spec ou no card.
1. Para cada linha da matriz, procure o teste que a prova (`git grep` pelo nome
   da função nos testes) e leia as asserções dele.
1. Fique com as linhas que nenhum teste prova.
1. Leia os testes novos e alterados: teste que não afirma o comportamento que
   diz testar (por exemplo, confere só o id e não o valor), teste que mocka o
   próprio alvo, teste cujo valor esperado foi trocado para passar, teste
   pulado.
1. Com spec, compare com a matriz de casos dela.

`local` aponta o teste incompleto. Sem teste nenhum, aponta as linhas do código
que ficaram sem prova.

## O que conta como evidência

A linha da matriz, o teste mais próximo com `arquivo:linha` e o que ele deixa
de afirmar, ou a busca que não achou teste.

## Não é desta lente

O bug em si (correção). Esta lente aponta o caso sem prova mesmo quando o
código está certo.
