# Spec: Aviso por SMS quando a exportação terminar
Status: aprovado · Brief: — · Modo: padrão

## Objetivo
Depois de exportar o CSV de um cliente, a operação recebe um aviso por SMS.

## Entendimento
A operação consulta a pasta de tempos em tempos para saber se o arquivo ficou
pronto. Demonstração: exportar um cliente, chamar o aviso e ver a mensagem na
caixa de saída do canal de SMS.

## Padrões aplicáveis
| Regra | Onde está |
| --- | --- |
| Canal novo entra no registro de canais; sem isso a mensagem some | `AGENTS.md:9` |
| Testes rodam com `unittest` | `AGENTS.md:5` |

## Referências no código
| Funcionalidade parecida | Local | O que imitar |
| --- | --- | --- |
| Despacho de mensagem por canal | `app/handlers/__init__.py:7-12` | Chamar o despacho e devolver o resultado |
| Linha da exportação | `app/export.py:7` | Função pequena que recebe dados e devolve um valor |

## Reuso
| Termos buscados | Encontrado | Decisão |
| --- | --- | --- |
| aviso, notify, send_sms, canal | `app/handlers/__init__.py:7-12` | Reusar: o despacho por canal já existe e o canal de SMS já está registrado |

## Decisões
| Decisão | Alternativa mais simples | Por que não serve |
| --- | --- | --- |
| O aviso é uma função nova em `app/export.py` | Chamar o despacho direto de quem exporta | O aviso precisa de um nome e de uma validação que quem exporta não tem |

## Escopo
- Permitido: `app/export.py`, `tests/test_export.py`
- Proibido: `app/handlers/`
- Exige aprovação: migração, dependência nova, canal novo
- Orçamento: arquivos novos 0 · abstrações novas 0 · dependências novas 0

## Matriz de casos
| Caso | Entrada ou estado | Resultado esperado | AC |
| --- | --- | --- | --- |
| Nome de cliente vazio | `""` | erro de validação | AC-002 |
| Nome só com espaços | `"   "` | erro de validação | AC-002 |
| Nome muito longo | não se aplica: o pedido não fixa limite | — | fora de escopo |
| Erro de dependência | não se aplica: o canal de SMS já está registrado e grava em memória | — | fora de escopo |
| Dois avisos ao mesmo tempo | não se aplica: a caixa de saída é uma lista em memória | — | fora de escopo |
| Permissão | não se aplica: o pedido não trata de acesso | — | fora de escopo |
| Aviso repetido | mesmo cliente, duas chamadas | duas mensagens, uma por chamada | AC-001 |

## Critérios de aceite
### AC-001 Avisa pelo canal de SMS
- QUANDO `notify_export_done("Ana Lima")` é chamada ENTÃO a caixa de saída recebe uma entrada do canal `sms` e a função devolve `True`
- Verificação: `python3 -m unittest tests.test_export.NotifyTest` → OK
- Tipo: teste
### AC-002 Rejeita nome vazio
- QUANDO o nome do cliente é vazio ou só espaços ENTÃO `notify_export_done` levanta `ValueError` e nada é enviado
- Verificação: `python3 -m unittest tests.test_export.NotifyInvalidTest` → OK
- Tipo: teste
### Critérios de qualidade
- AC-Q01 Usa `dispatch` de `app/handlers/__init__.py` · Verificação: `git grep -n "dispatch" app/export.py`

## Tarefas
### T1 Avisar ao fim da exportação · Depende de: — · Cobre: AC-001, AC-002, AC-Q01
- Arquivos: modificar `app/export.py`; testar `tests/test_export.py`
- Interfaces: produz `notify_export_done(customer: str) -> bool`
- Pronto quando: `python3 -m unittest discover -s tests` → OK

## Rastreabilidade
| AC | Tarefas |
| --- | --- |
| AC-001 | T1 |
| AC-002 | T1 |
| AC-Q01 | T1 |
