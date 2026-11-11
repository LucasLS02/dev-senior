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
local: {arquivo: billing/invoices.py, linhas: 21-22}
problema: due_date levanta ValueError para fatura emitida no dia 31 de um mês seguido de mês mais curto.
viola: AC-003 (vencimento um mês depois da emissão)
evidência: |
  billing/invoices.py:22 faz issued.replace(month=issued.month + 1).
  python3 -c "from datetime import date; from billing.invoices import due_date; due_date(date(2026, 1, 31))"
  → ValueError: day is out of range for month
impacto: a emissão em lote do dia 31 para na primeira fatura e nenhuma é enviada.
verificação: {veredito: confirmado, método: reprodução}
correção: {escopo: local, arquivos_esperados: [billing/invoices.py, tests/test_invoices.py]}
gatilho: —
status: aberto
```

```yaml
id: RV-002
lente: segurança
severidade: médio
local: {arquivo: billing/invoices.py, linhas: 40}
problema: lookup converte o código recebido com int() sem tratar valor inválido.
viola: —
evidência: billing/api.py:18 só chama lookup depois de code.isdigit(); tests/test_api.py:25 cobre código inválido e espera 400.
impacto: nenhum hoje; a única entrada externa já valida o código.
verificação: {veredito: refutado, método: inspeção}
correção: {escopo: local, arquivos_esperados: []}
gatilho: —
status: aberto
```

## Cobertura

- Alvo: HEAD~1..HEAD
- Perfil: próprio
- Fontes de requisito: .agent_plans/faturas/spec.md
- Regras lidas: REVIEW.md, AGENTS.md, billing/AGENTS.md
- Lentes: requisito, correção, testes, conformidade; segurança acionada (entrada externa em billing/api.py); desempenho não acionada (sem laço com E/S); manutenção não acionada (sem arquivo novo nem função longa)
- Lidos por inteiro: billing/invoices.py, billing/api.py, tests/test_invoices.py
- Não conferido: poetry.lock — arquivo gerado
````
