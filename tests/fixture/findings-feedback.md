# Achados · HEAD~1..HEAD

```yaml
id: RV-001
lente: correção
severidade: alto
local: {arquivo: app/orders.py, linhas: 38-39}
problema: average_total divide por zero quando recebe uma lista vazia.
viola: docs/card.md (com lista vazia, devolve 0)
evidência: |
  app/orders.py:39 faz sum(order["total"] for order in orders) / len(orders) sem guarda.
  python3 -c "from app.orders import average_total; average_total([])"
  → ZeroDivisionError: division by zero
impacto: exportar um status sem pedidos e tirar a média derruba o relatório.
verificação: {veredito: confirmado, método: reprodução}
correção: {escopo: local, arquivos_esperados: [app/orders.py, tests/test_orders.py]}
gatilho: —
status: aberto
```

```yaml
id: RV-002
lente: correção
severidade: médio
local: {arquivo: app/orders.py, linhas: 42-43}
problema: _share divide sem guarda quando whole é 0.
viola: —
evidência: app/orders.py:43 faz part / whole; não ficou claro se outro chamador futuro passará whole = 0.
impacto: se um chamador novo passar whole = 0, a função levanta ZeroDivisionError.
verificação: {veredito: plausível, método: inspeção}
correção: {escopo: local, arquivos_esperados: [app/orders.py]}
gatilho: —
status: aberto
```

## Cobertura

- Alvo: HEAD~1..HEAD
- Perfil: próprio
- Fontes de requisito: docs/card.md
- Regras lidas: REVIEW.md, AGENTS.md
- Lentes: requisito, correção, testes, conformidade
- Lidos por inteiro: app/orders.py, tests/test_orders.py
- Não conferido: requirements.lock — arquivo gerado
