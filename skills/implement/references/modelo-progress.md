# Formato do `progress.md`

Estado operacional, não transcrição: o relatório final e o plano de commits saem
destas tabelas. Os títulos e os vocabulários abaixo são lidos por
`check_run.py progress` e `converge`: não renomeie.

## Vocabulário

| Coluna | Valores |
|---|---|
| Prontidão: Resultado | `ok` ou `falhou` |
| Critérios: Status | `passou`, `falhou`, `pendente` |
| Tarefas: Status | `pendente`, `em andamento`, `concluída`, `escalada` |
| Achados: Veredito | `confirmado`, `refutado`, `plausível` |
| Achados: Gatilho | `—` ou IDs separados por vírgula (`G6`, `S1`, `P2`) |
| Achados: Resultado | `aberto`, `corrigido`, `refutado`, `escalado`, `registrado` |

`Estado da árvore` é a saída de `check_run.py tree` no momento em que a evidência
foi colhida. `converge` só aceita a evidência cuja impressão é a da árvore atual.
`Qualidade` e `Log` não têm vocabulário fixo; o `Log` só acrescenta.

## Esqueleto

````markdown
# Progresso · spec: <.agent_plans/pasta/spec.md>

## Prontidão
| Checagem | Resultado |
| --- | --- |

## Critérios de aceite
| AC | Status | Evidência | Estado da árvore |
| --- | --- | --- | --- |

## Tarefas
| T | Status | Arquivos alterados | Verificação |
| --- | --- | --- | --- |

## Qualidade
| Indicador | Antes | Depois | Limite | Origem |
| --- | --- | --- | --- | --- |

## Achados
| ID | Severidade | Veredito | Gatilho | Ação | Resultado |
| --- | --- | --- | --- | --- | --- |

## Escaladas e decisões

## Log
````

Cada escalada nova usa um número estável, sem reutilização, e contém:

```text
### Escalada 1
Gatilho: S1 · Tarefa ou achado: RV-001
Motivo: <evidência>
Arquivos: <arquivos>
Efeito: <efeito>
Alternativas: <alternativas>
Recomendação: <recomendação>
Dependência externa: sim ou não
Decisão: pendente
```

Troque `pendente` pela decisão registrada quando houver resposta. Entradas
antigas continuam válidas para o `implement`; a `track` não presume que foram
resolvidas sem um bloco reconhecível.

## Exemplo

Execução concluída da spec de `skills/spec/references/exemplo.md`:

```markdown
# Progresso · spec: .agent_plans/reservas/spec.md

## Prontidão
| Checagem | Resultado |
| --- | --- |
| check_spec.py limpo | ok |
| Status aprovado | ok |
| Sem marcador pendente | ok |
| Árvore limpa | ok |

## Critérios de aceite
| AC | Status | Evidência | Estado da árvore |
| --- | --- | --- | --- |
| AC-001 | passou | `python3 -m unittest tests.test_booking.CancelTest` → OK | a1b2c3d4e5f6 |
| AC-002 | passou | `python3 -m unittest tests.test_booking.CancelInvalidTest` → OK | a1b2c3d4e5f6 |
| AC-003 | passou | `python3 -m unittest tests.test_booking.CancelTwiceTest` → OK | a1b2c3d4e5f6 |
| AC-Q01 | passou | `git grep -n "def release" app/booking.py` → app/booking.py:2 | a1b2c3d4e5f6 |

## Tarefas
| T | Status | Arquivos alterados | Verificação |
| --- | --- | --- | --- |
| T1 | concluída | app/booking.py, tests/test_booking.py | `python3 -m unittest discover -s tests` → OK |

## Qualidade
| Indicador | Antes | Depois | Limite | Origem |
| --- | --- | --- | --- | --- |
| Arquivos novos | 0 | 0 | 0 | check_run.py quality |
| Supressões novas | 0 | 0 | 0 | check_run.py quality |

## Achados
| ID | Severidade | Veredito | Gatilho | Ação | Resultado |
| --- | --- | --- | --- | --- | --- |
| RV-001 | alto | confirmado | — | corrigido em app/booking.py | corrigido |
| RV-002 | médio | refutado | — | — | refutado |
| RV-003 | alto | confirmado | G6 | escalado: exige trocar o valor esperado de um teste | registrado |

## Escaladas e decisões
- RV-003 (G6): humano decidiu manter o teste; o achado fica registrado.

## Log
- Prontidão ok; T1 entregue ao implementador.
- Review rodou: 3 achados.
```
