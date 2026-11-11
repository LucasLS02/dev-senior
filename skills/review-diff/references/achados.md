# Formato do `findings.md`

Contrato entre `review-diff` (escreve), `pr-review`, `pr-feedback` e
`implement` (leem e atualizam). Um arquivo por alvo revisado, em
`.agent_plans/<slug>/findings.md`.

## Estrutura

1. Cabeçalho `# Achados · <alvo>`.
1. Um bloco de código `yaml` por achado, na ordem dos IDs.
1. A seção `## Cobertura`, sempre, mesmo sem achados.

`local`, `verificação` e `correção` ficam sempre em mapa de uma linha. Assim um
script lê o arquivo sem parser de YAML.

## Campos

| Campo | O que é | Quem preenche |
|---|---|---|
| `id` | `RV-001`, `RV-002`…, em ordem de severidade; nunca reaproveitado | `review-diff` |
| `lente` | `requisito`, `correção`, `testes`, `conformidade`, `segurança`, `desempenho` ou `manutenção` | `review-diff` |
| `severidade` | `crítico`, `alto`, `médio` ou `baixo` (régua abaixo) | `review-diff` |
| `local` | `{arquivo: <caminho a partir da raiz>, linhas: <início>-<fim>}`; uma linha só pode ser `linhas: 42` | `review-diff` |
| `problema` | O que está errado, numa frase direta | `review-diff` |
| `viola` | O que o achado contraria: `AC-004`, `AGENTS.md` com a seção, o card, ou `—` | `review-diff` |
| `evidência` | O que prova o problema, com ao menos um `arquivo:linha`: trecho, chamador, comando e saída. Uma linha ou bloco `\|` | `review-diff` |
| `impacto` | Cenário → consequência: o que quebra, quando, para quem | `review-diff` |
| `verificação` | `{veredito: <veredito>, método: <método>}` | verificador do `review-diff` |
| `correção` | `{escopo: local \| amplo, arquivos_esperados: [...]}`. Uso interno: nunca é postado em PR de outra pessoa | `review-diff` |
| `gatilho` | ID do gatilho de parada que o achado acionou (`G4`, `S7`…) ou `—`. Nasce `—` | `implement` |
| `status` | `aberto`, `corrigido`, `escalado` ou `registrado`. Nasce `aberto` | `pr-feedback`, `implement` |

Não existe campo de confiança. O que distingue um achado é o veredito e o
método.

## Severidade

| Severidade | Quando |
|---|---|
| `crítico` | Vulnerabilidade ou risco de perda de dados |
| `alto` | Bug ou problema relevante de qualidade |
| `médio` | Manutenção |
| `baixo` | Estilo |

Achado bloqueante é o de severidade `crítico` ou `alto`.

## Veredito e método

| Veredito | Significa |
|---|---|
| `confirmado` | A evidência está completa e a tentativa de refutar falhou |
| `refutado` | O verificador mostrou que não é problema; a evidência diz por quê |
| `plausível` | Não deu para confirmar nem refutar; vira pergunta, nunca afirmação |

| Método | Significa |
|---|---|
| `teste` | Rodou um teste que falha por causa do problema |
| `reprodução` | Rodou um comando que mostra o problema |
| `inspeção` | Seguiu o caminho no código, da entrada até a linha |

## Status

| Status | Significa |
|---|---|
| `aberto` | Ainda não tratado |
| `corrigido` | Corrigido e verificado |
| `escalado` | Levado ao humano por um gatilho |
| `registrado` | Anotado sem correção (ex.: código anterior à tarefa) |

## Exemplo

````markdown
# Achados · HEAD~1..HEAD

```yaml
id: RV-001
lente: correção
severidade: alto
local: {arquivo: app/orders.py, linhas: 12-14}
problema: average_total divide por zero quando recebe uma lista vazia.
viola: docs/card.md (média de lista vazia é 0)
evidência: |
  app/orders.py:13 faz sum(o["total"] for o in orders) / len(orders) sem guarda.
  python3 -c "from app.orders import average_total; average_total([])"
  → ZeroDivisionError: division by zero
impacto: exportar um status sem pedidos derruba o relatório inteiro.
verificação: {veredito: confirmado, método: reprodução}
correção: {escopo: local, arquivos_esperados: [app/orders.py, tests/test_orders.py]}
gatilho: —
status: aberto
```

```yaml
id: RV-002
lente: correção
severidade: médio
local: {arquivo: app/orders.py, linhas: 40}
problema: share divide sem guarda quando whole é 0.
viola: —
evidência: app/orders.py:47 só chama share dentro de "if whole:"; tests/test_orders.py:30 cobre whole = 0.
impacto: nenhum hoje; o único chamador já protege a divisão.
verificação: {veredito: refutado, método: inspeção}
correção: {escopo: local, arquivos_esperados: []}
gatilho: —
status: aberto
```

## Cobertura

- Alvo: HEAD~1..HEAD
- Perfil: próprio
- Fontes de requisito: docs/card.md
- Regras lidas: REVIEW.md, AGENTS.md
- Lentes: requisito, correção, testes, conformidade; segurança (consulta SQL no diff); desempenho não acionada (sem laço com E/S); manutenção acionada (arquivo novo)
- Lidos por inteiro: app/orders.py, tests/test_orders.py
- Não conferido: requirements.lock — arquivo gerado
````
