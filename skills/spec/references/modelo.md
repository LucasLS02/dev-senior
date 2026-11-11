# Formato da `spec.md`

Os títulos, os nomes das colunas e as palavras `QUANDO`, `ENTÃO`, `Verificação`,
`Tipo`, `Depende de`, `Cobre` e `Pronto quando` são lidos por `check_spec.py` e
pelo `review-diff`: não renomeie. O `Modo: rápido` leva só Objetivo, Escopo,
Critérios de aceite e Tarefas.

````markdown
# Spec: <título>
Status: rascunho · Brief: <.agent_plans/pasta/brief.md ou —> · Modo: <rápido|padrão|profundo>

## Objetivo
<uma frase testável>

## Entendimento
<a necessidade reescrita; cenário de demonstração que um humano repetiria>

## Padrões aplicáveis
| Regra | Onde está |
| --- | --- |
| <regra da casa que toca a tarefa> | `<arquivo>:<linha>` |

## Referências no código
| Funcionalidade parecida | Local | O que imitar |
| --- | --- | --- |
| <nome> | `<arquivo>:<linha>` | <o que copiar do jeito de fazer> |

## Reuso
| Termos buscados | Encontrado | Decisão |
| --- | --- | --- |
| <nome, sinônimos, chamada de biblioteca> | `<arquivo>:<linha>` ou nada | Reusar, Adaptar ou Criar: <motivo> |

## Decisões
| Decisão | Alternativa mais simples | Por que não serve |
| --- | --- | --- |
| <escolha> | <o mais simples que existia> | <motivo> |

## Escopo
- Permitido: `<arquivo>`, `<arquivo>`
- Proibido: `<arquivo>` ou —
- Exige aprovação: <migração, dependência nova, ...>
- Orçamento: arquivos novos 0 · abstrações novas 0 · dependências novas 0

## Matriz de casos
| Caso | Entrada ou estado | Resultado esperado | AC |
| --- | --- | --- | --- |
| <entrada vazia de X> | <valor> | <resultado> | AC-001 |
| <categoria que não cabe> | não se aplica: <motivo> | — | fora de escopo |

## Critérios de aceite
### AC-001 <nome>
- QUANDO <condição> ENTÃO <resultado observável>
- Verificação: `<comando ou teste>` → <sinal esperado>
- Tipo: teste | comando | inspeção | manual
### Critérios de qualidade
- AC-Q01 Usa `<símbolo>` de `<arquivo>` · Verificação: `<busca ou comando>`

## Tarefas
### T1 <nome> · [P] · Depende de: — · Cobre: AC-001, AC-Q01
- Arquivos: criar `<arquivo>`; modificar `<arquivo>`; testar `<arquivo>`
- Interfaces: consome <o que>; produz <assinatura>
- Pronto quando: `<comando>` → <sinal>

## Rastreabilidade
| AC | Tarefas |
| --- | --- |
| AC-001 | T1 |
| AC-Q01 | T1 |
````

Notas:

- `[P]` é opcional e só vale em tarefa que não divide arquivo com outra.
- A coluna `AC` da matriz aceita `fora de escopo: <motivo>`; nenhuma linha fica
  sem destino.
- Dúvida aberta: `[PRECISA DECISÃO: <pergunta, nomeando o termo>]` no ponto em
  que a resposta entra; o validador a aponta como `marcador pendente` até ser
  substituída.
- `Brief: —` só no pedido direto, sem brief (modos `rápido` e `padrão`; `profundo` exige brief).
