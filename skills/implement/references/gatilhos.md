# Gatilhos de parada

Qualquer gatilho para. O raciocínio do agente pode acrescentar uma parada com o
motivo por escrito, nunca remover uma. O ID do gatilho vai na coluna `Gatilho` da
tabela `Achados` e em `Escaladas e decisões`; é assim que os números se calibram.

## Detectáveis no diff

`check_run.py triggers <spec>` reporta os marcados com "script". Os outros, você
avalia olhando o diff.

| ID | Quando | Quem avalia |
|---|---|---|
| G1 | Arquivo fora do "Permitido" ou dentro do "Proibido" | script |
| G2 | Arquivo apagado ou renomeado; símbolo exportado ou rota pública removidos | script (rota pública é sua) |
| G3 | Manifesto de dependências ou lockfile alterado | script |
| G4 | Migração ou schema de banco | script |
| G5 | Caminho sensível: autenticação, permissão, criptografia, segredos, CI, infraestrutura | script |
| G6 | Teste existente alterado, apagado ou pulado, ou valor esperado trocado | script |
| G7 | Supressão adicionada (`@ts-ignore`, `eslint-disable`, `# noqa`, `--no-verify`) | script |
| G8 | Correção acima do teto (inicial: 3 arquivos ou 50 linhas por achado) | você, com `git diff --numstat` antes e depois |
| G9 | Arquivo, abstração ou dependência além do orçamento, ou clone novo sem linha na tabela de reuso | script para arquivos novos; o resto é seu |

## Semânticos

Pergunta fechada, respondida por escrito.

| ID | Quando |
|---|---|
| S1 | A correção contradiz a spec ou exige mudar um AC |
| S2 | Há duas ou mais correções válidas e nada decide entre elas |
| S3 | Depende de regra de negócio que não está no código, na spec nem no card |
| S4 | Muda comportamento de chamadores fora do escopo |
| S5 | Achado de segurança ou de dados com severidade alta ou crítica |
| S6 | Achado em código anterior à tarefa: não corrige, registra |
| S7 | Achado "plausível", não "confirmado" |

## De processo

| ID | Quando |
|---|---|
| P1 | A mesma correção falhou na verificação duas vezes |
| P2 | Terceira rodada de review e correção na mesma tarefa |
| P3 | Um AC que passava deixou de passar e não voltou em uma tentativa |
| P4 | Mais de 10 achados confirmados na tarefa: o problema é a implementação ou a spec |

Os números de G8, P1, P2 e P4 são iniciais.

## Como a parada acontece

- **Em lote:** os escalados de uma rodada são apresentados juntos; os demais, que
  não tocam os mesmos arquivos, seguem sendo corrigidos.
- **Formato da escalada**, um bloco por item:

```text
Gatilho: <ID> · Tarefa ou achado: <T1 ou RV-001>
Motivo: <o que o diff ou a spec mostra, com arquivo:linha>
Arquivos: <os que a mudança tocaria>
Efeito: <o que muda para quem usa>
Alternativas: <as opções, incluindo não fazer>
Recomendação: <uma, com o motivo>
```

- **A aprovação vale para a mudança descrita.** Se a solução mudar de forma
  relevante, a aprovação deixa de valer e a escalada é refeita.
- Registre a decisão do humano em `Escaladas e decisões`, ao lado do ID.

Paradas fixas, independentes de gatilho: prontidão da spec, plano de commits,
push e abertura de PR.
