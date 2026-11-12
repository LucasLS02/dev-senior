# Spec: Exportação com o nome do cliente como veio
Status: aprovado · Brief: — · Modo: padrão

## Objetivo
A linha exportada mostra o nome do cliente exatamente como foi cadastrado.

## Entendimento
A operação reconhece o cliente pelo nome original e não entende a forma
normalizada. Demonstração: exportar "Ana Lima" e ver "Ana Lima" na coluna.

## Padrões aplicáveis
| Regra | Onde está |
| --- | --- |
| Testes rodam com `unittest` | `AGENTS.md:5` |

## Referências no código
| Funcionalidade parecida | Local | O que imitar |
| --- | --- | --- |
| Linha da exportação | `app/export.py:7-9` | Montar o dicionário da linha |

## Reuso
| Termos buscados | Encontrado | Decisão |
| --- | --- | --- |
| customer, nome, normalizar | `app/export.py:8` | Adaptar: a linha deixa de normalizar o nome |

## Decisões
| Decisão | Alternativa mais simples | Por que não serve |
| --- | --- | --- |
| A coluna recebe o nome sem tratamento | Manter a coluna normalizada | A operação pediu o nome original |

## Escopo
- Permitido: `app/export.py`, `tests/test_export.py`
- Proibido: `app/text.py`
- Exige aprovação: migração, dependência nova
- Orçamento: arquivos novos 0 · abstrações novas 0 · dependências novas 0

## Matriz de casos
| Caso | Entrada ou estado | Resultado esperado | AC |
| --- | --- | --- | --- |
| Nome com acento e espaço | `"Ana Lima"` | a coluna traz `Ana Lima` | AC-001 |
| Nome vazio | `""` | não se aplica: o pedido não muda a validação | fora de escopo |
| Limite | não se aplica: o pedido não fixa tamanho | — | fora de escopo |
| Erro de dependência | não se aplica: não há chamada externa | — | fora de escopo |
| Concorrência | não se aplica: a função é pura | — | fora de escopo |
| Permissão | não se aplica: o pedido não trata de acesso | — | fora de escopo |
| Estado anterior | não se aplica: a função não guarda estado | — | fora de escopo |

## Critérios de aceite
### AC-001 Nome como veio
- QUANDO `export_row` recebe um pedido do cliente "Ana Lima" ENTÃO a chave `customer` da linha vale `"Ana Lima"`
- Verificação: `python3 -m unittest tests.test_export.OriginalNameTest` → OK
- Tipo: teste

## Tarefas
### T1 Exportar o nome original · Depende de: — · Cobre: AC-001
- Arquivos: modificar `app/export.py`; testar `tests/test_export.py`
- Interfaces: consome `export_row(order: dict) -> dict`
- Pronto quando: `python3 -m unittest discover -s tests` → OK

## Rastreabilidade
| AC | Tarefas |
| --- | --- |
| AC-001 | T1 |
