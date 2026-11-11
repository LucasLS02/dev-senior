# Brief: Cancelar reserva de sala
Status: rascunho · Origem: card-7 · Modo: padrão

## Problema
Quem reserva uma sala e desiste precisa chamar o suporte para liberar o horário;
o suporte registrou 14 pedidos assim no mês. Hoje só `app/booking.py:2` cria
reservas.

## Pedido vs. necessidade
Pedido: um botão de cancelar. Necessidade: o horário voltar a ficar livre sem
depender de uma pessoa do suporte.

## Apetite
Modo padrão: mexe em dado de reserva, mas em um arquivo só.
Pequeno: um dia.

## Referências de mercado
| Fonte | Como resolve | O que aproveitar |
| --- | --- | --- |
| — | — | — |

## Opções consideradas
| Opção | Prós | Contras | Veredito |
| --- | --- | --- | --- |
| Não fazer | Sem custo | O suporte segue cancelando à mão | Descartada |
| Resolver sem código | O suporte cancela por formulário | Não elimina a espera | Descartada |
| Cancelar pela própria pessoa | Libera na hora, sem suporte | Precisa tratar cancelamento repetido | Recomendada |

## Recomendação
Permitir que quem reservou cancele uma reserva futura, liberando o horário.

## Fora de escopo
Reembolso, aviso aos demais participantes, histórico de cancelamentos.

## Riscos e armadilhas
Cancelar duas vezes a mesma reserva não pode liberar o horário de outra pessoa.

## Perguntas em aberto
Nenhuma.
