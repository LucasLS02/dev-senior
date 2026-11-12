# Formato do `pr.md`

O arquivo é o que o humano lê e edita antes de dar a ordem. A linha 1, os
títulos das seções e as colunas da tabela são lidos por `check_pr.py`: não
renomeie.

## Regras

| Parte | Regra |
|---|---|
| Linha 1 | `Título: <texto>`, de 1 a 72 caracteres, sem ponto final |
| `## Resumo` | Não vazio; sai do `Objetivo` e do `Entendimento` da spec |
| `## Critérios de aceite` | Uma linha por AC e AC-Q da spec, `Status` `passou` ou `pendente`, evidência que não seja `—` |
| `pendente` | Só para AC de tipo `manual`; a evidência diz o passo que o revisor faz |
| Marcador `[PRECISA DECISÃO` | Nenhum, fora de bloco de código |
| `.agent_plans/` | Nenhuma menção: o leitor da PR não tem a pasta |
| Tamanho | O corpo (depois do título) não passa de 80 linhas |

`Achados do review` e `Riscos e decisões` vêm do `progress.md`: o que foi
corrigido sozinho, o que foi refutado, o que foi escalado e o que o humano
decidiu. Com template de PR no repositório, o template manda no resto e a tabela
de critérios entra nele.

## Esqueleto

````markdown
Título: <o que muda, em até 72 caracteres>

## Resumo
<o objetivo e a necessidade, em poucas linhas>

## Critérios de aceite
| AC | Status | Evidência |
| --- | --- | --- |
| AC-001 | passou | `<comando>` → <sinal> |

## Achados do review
<corrigidos, refutados, escalados e a decisão do humano>

## Riscos e decisões
<o que o revisor precisa saber>
````

## Exemplo

Para a spec de `skills/spec/references/exemplo.md`:

```markdown
Título: Cancelar reserva de sala

## Resumo
Permite cancelar uma reserva futura e liberar o horário, sem chamar o suporte.

## Critérios de aceite
| AC | Status | Evidência |
| --- | --- | --- |
| AC-001 | passou | `python3 -m unittest tests.test_booking.CancelTest` → OK |
| AC-002 | passou | `python3 -m unittest tests.test_booking.CancelInvalidTest` → OK |
| AC-003 | passou | `python3 -m unittest tests.test_booking.CancelTwiceTest` → OK |
| AC-Q01 | passou | `git grep -n "def release" app/booking.py` → app/booking.py:2 |

## Achados do review
Um achado alto corrigido em `app/booking.py`; um médio refutado.

## Riscos e decisões
Cancelar apaga a reserva: nenhum relatório usa o histórico, então não há
marcação de cancelada.
```
