# Spec: Cancelar reserva de sala
Status: rascunho · Brief: .agent_plans/reservas/brief.md · Modo: padrão

## Objetivo
Permitir cancelar uma reserva futura e liberar o horário.

## Entendimento
Quem reserva precisa desfazer o pedido sem chamar o suporte. Demonstração:
reservar 10h–11h, cancelar e reservar de novo o mesmo horário.

## Padrões aplicáveis
| Regra | Onde está |
| --- | --- |
| Nome de sala sempre em minúsculas | `AGENTS.md:3` |

## Referências no código
| Funcionalidade parecida | Local | O que imitar |
| --- | --- | --- |
| Criar reserva | `app/booking.py:2` | Validar antes de gravar |

## Reuso
| Termos buscados | Encontrado | Decisão |
| --- | --- | --- |
| cancel, remove, free_slot | `app/booking.py:2` | Adaptar: liberar horário já existe em `release` |

## Decisões
| Decisão | Alternativa mais simples | Por que não serve |
| --- | --- | --- |
| Cancelar apaga a reserva | Marcar como cancelada | Nenhum relatório usa o histórico |

## Escopo
- Permitido: `app/booking.py`, `tests/test_booking.py`
- Proibido: `app/db.py`
- Exige aprovação: migração, dependência nova
- Orçamento: arquivos novos 0 · abstrações novas 0 · dependências novas 0

## Matriz de casos
| Caso | Entrada ou estado | Resultado esperado | AC |
| --- | --- | --- | --- |
| Id vazio | `""` | erro de validação | AC-002 |
| Reserva inexistente | id desconhecido | erro "não encontrada" | AC-002 |
| Reserva que já começou | cancelamento depois do início | fora de escopo: o brief só trata reserva futura | fora de escopo |
| Erro de dependência | não se aplica: a reserva vive em memória, sem chamada externa | — | fora de escopo |
| Dois cancelamentos ao mesmo tempo | mesmo id, duas chamadas | só a primeira cancela; a segunda falha | AC-003 |
| Permissão | não se aplica: o brief deixa autenticação de fora | — | fora de escopo |
| Estado anterior | reserva já cancelada | segunda chamada falha sem efeito | AC-003 |

## Critérios de aceite
### AC-001 Cancelar libera o horário
- QUANDO a reserva futura é cancelada ENTÃO o horário volta a ficar livre
- Verificação: `python3 -m unittest tests.test_booking.CancelTest` → OK
- Tipo: teste
### AC-002 Cancelar rejeita id inválido
- QUANDO o id é vazio ou desconhecido ENTÃO `cancel` levanta `ValueError`
- Verificação: `python3 -m unittest tests.test_booking.CancelInvalidTest` → OK
- Tipo: teste
### AC-003 Cancelar duas vezes falha
- QUANDO a mesma reserva é cancelada pela segunda vez ENTÃO `cancel` levanta `ValueError` e nada muda
- Verificação: `python3 -m unittest tests.test_booking.CancelTwiceTest` → OK
- Tipo: teste
### Critérios de qualidade
- AC-Q01 Usa `release` de `app/booking.py` · Verificação: `git grep -n "def release" app/booking.py`

## Tarefas
### T1 Cancelar reserva · Depende de: — · Cobre: AC-001, AC-002, AC-003, AC-Q01
- Arquivos: modificar `app/booking.py`; testar `tests/test_booking.py`
- Interfaces: produz `cancel(booking_id: str) -> None`
- Pronto quando: `python3 -m unittest discover -s tests` → OK

## Rastreabilidade
| AC | Tarefas |
| --- | --- |
| AC-001 | T1 |
| AC-002 | T1 |
| AC-003 | T1 |
| AC-Q01 | T1 |
