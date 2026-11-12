# Pacote de trabalho do implementador

O implementador vê só o pacote: nada do resto da conversa. O que faltar nele,
ele vai inventar. Monte um pacote por tarefa, a partir da `spec.md`.

| Campo | Conteúdo |
|---|---|
| Objetivo | A frase da tarefa e o `Objetivo` da spec |
| Critérios | Cada AC que a tarefa cobre, com o `QUANDO … ENTÃO …` e a `Verificação` por extenso |
| Arquivos permitidos | A lista de `Permitido` que a tarefa toca |
| Arquivos proibidos | `Proibido` da spec, mais tudo fora de `Permitido` |
| Padrões e reuso | As linhas citadas em `Padrões aplicáveis`, `Referências no código` e `Reuso` que a tarefa usa, com o `arquivo:linha` |
| Casos | As linhas da `Matriz de casos` que apontam para os AC da tarefa |
| Interfaces | `consome` e `produz` da tarefa, com os nomes e tipos exatos |
| Verificação | O `Pronto quando` da tarefa |
| Orçamento | Arquivos, abstrações e dependências novas que ainda restam |

## Regras que o pacote leva escritas

- Escreva primeiro os testes dos casos, rode-os e confirme que falham pelo motivo
  certo; só então o código.
- Não commite, não crie branch, não mexa em arquivo fora de "Arquivos permitidos".
- Teste que já existia e passa a falhar por causa da mudança: **não o altere**.
  Pare e devolva.
- Reuse o que a tabela de reuso manda reusar; não escreva uma segunda versão.

## Condições de parada

Devolva o controle, sem tentar contornar, quando:

- o trabalho exige arquivo fora de "Arquivos permitidos" ou dentro de "Proibido";
- exige alterar, apagar ou pular teste existente;
- exige dependência, migração, caminho de autenticação, permissão, criptografia,
  segredo, CI ou infraestrutura;
- duas leituras válidas da spec levam a código diferente, ou falta uma regra de
  negócio que a spec e o código não trazem;
- a verificação falhou duas vezes pelo mesmo motivo.

## O que ele devolve

1. Os arquivos que alterou ou criou.
2. O comando de verificação e a saída que viu, sem resumir o que falhou.
3. As incertezas, uma por linha, cada uma com a decisão que ele tomou ou a
   pergunta que ficou.

Sem delegação, o orquestrador segue este mesmo pacote como lista de controle e
faz as três devoluções para si, por escrito, no `Log`.
