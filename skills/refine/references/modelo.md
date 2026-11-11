# Formato do `brief.md`

Os títulos, os rótulos `Pedido:` e `Necessidade:`, a linha `Modo <modo>: <motivo>` e as
colunas `Veredito` e `Fonte` são lidos por `check_brief.py` e pela `spec`: não renomeie.

````markdown
# Brief: <título>
Status: rascunho · Origem: <card ou conversa> · Modo: <padrão|profundo>

## Problema
<quem sofre, quando, evidência de que é real; `arquivo:linha` onde o código entra>

## Pedido vs. necessidade
Pedido: <o que foi dito>. Necessidade: <o que resolve de fato>.

## Apetite
Modo <padrão|profundo>: <motivo do modo>
<quanto vale gastar>

## Referências de mercado
| Fonte | Como resolve | O que aproveitar |
| --- | --- | --- |
| <URL ou `caminho` que você abriu> ou — | <como resolve> | <o que aproveitar> |

## Opções consideradas
| Opção | Prós | Contras | Veredito |
| --- | --- | --- | --- |
| Não fazer | <prós> | <contras> | Descartada |
| Resolver sem código | <prós> | <contras> | Descartada |
| <opção que o problema pede> | <prós> | <contras> | Recomendada |

## Recomendação
<a opção recomendada, em uma ou duas frases>

## Fora de escopo
<o que fica de fora>

## Riscos e armadilhas
<o que pode dar errado>

## Perguntas em aberto
Nenhuma. (ou uma linha `- [PRECISA DECISÃO: <pergunta, nomeando o termo>]` por pergunta)
````

## Bug: seção a acrescentar

Entre `Pedido vs. necessidade` e `Apetite`:

````markdown
## Diagnóstico
- Reprodução: `python3 -c "from app.booking import reserve; reserve('', 10)"` → `KeyError`
- Causa raiz: `app/booking.py:2` indexa o dicionário antes de validar o id
- Comportamento atual: id vazio derruba a chamada com `KeyError`
- Comportamento esperado: erro de validação com mensagem legível
- Deve permanecer igual: reservas com id válido
````

Notas:

- Exatamente uma opção `Recomendada`. Se a recomendada é `Não fazer`, o `Status` segue
  `rascunho`: só o humano marca `descartado`.
- Mudança rápida não usa este formato: vai direto para a `spec`.
