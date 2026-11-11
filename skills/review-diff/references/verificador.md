# Verificador

Recebe candidatos e tenta derrubar cada um. Parte do código, não do raciocínio
de quem achou.

Para cada candidato:

1. **Reabrir.** Leia o código na revisão do alvo: `git show <head>:<arquivo>`
   num intervalo, o arquivo em disco na árvore de trabalho. Se a linha não
   existe ou não diz o que o candidato afirma, o veredito é `refutado`.
1. **Tentar refutar.** Procure o que derruba o candidato:
   - o caso é tratado em outro lugar: chamador que valida antes, guarda,
     middleware, restrição no banco, configuração;
   - algum teste prova o contrário;
   - a entrada concreta não chega até a linha: siga do ponto de entrada (rota,
     comando, função pública) até ela e veja se alguém chama com essa entrada;
   - a regra citada não diz o que o candidato afirma, ou não vale para esse
     caminho.
1. **Escolher o método.**
   - `teste`: rodou um teste que falha por causa do problema.
   - `reprodução`: rodou um comando que mostra o problema.
   - `inspeção`: seguiu o caminho no código, da entrada até a linha.

   No perfil `colega`, só rode código ou testes com o ok de quem pediu.
1. **Dar o veredito.**
   - `confirmado`: a evidência está completa e a refutação falhou.
   - `refutado`: a evidência diz o que derrubou o candidato, com
     `arquivo:linha`.
   - `plausível`: não deu para confirmar nem refutar (por exemplo, depende de
     regra de negócio fora do código); o problema vira pergunta.
1. **Rever a severidade** pela régua de `achados.md`. Bug sem entrada concreta
   não é `alto`.

Achado cuja evidência não cita `arquivo:linha` não pode ser `confirmado`.
