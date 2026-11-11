# Lente: correção e regressão

## Quando roda

Sempre.

## Como procurar

1. Leia cada linha alterada e, em volta dela, quem a chama e o que ela chama.
1. Para cada assinatura, retorno, exceção ou efeito colateral alterado, busque
   todos os chamadores no repositório (`git grep -n <nome> <head>`), inclusive
   fora do diff, e confira se continuam corretos.
1. Passe os valores de borda por cada operação: vazio, nulo, zero, negativo,
   limite, duplicado, texto com acento ou espaço.
1. Siga os caminhos de erro: exceção engolida, recurso não fechado, estado
   parcial deixado para trás.
1. Para cada suspeita, construa a entrada concreta e siga até a linha que
   falha. Sem entrada concreta, o candidato é no máximo `plausível`.

## O que conta como evidência

A entrada concreta, o caminho até a linha e a linha que falha
(`arquivo:linha`). Melhor ainda: o comando que reproduz e a saída dele.

## Não é desta lente

Divergência do pedido (requisito); falta de teste para um caminho que está
correto (testes).
