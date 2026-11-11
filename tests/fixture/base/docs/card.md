# Card: exportar pedidos

Criar em `app/orders.py`:

- `export_orders(conn, status)`: lista de dicts com `id`, `customer_slug`,
  `email`, `total` e `created_at`. `created_at` é o momento da exportação, em
  UTC. `total` é inteiro, em centavos (o banco guarda reais). O chamador passa
  `paid` ou `cancelled`. Pedido cancelado sai com `total` 0.
- `average_total(orders)`: média de `total` dos pedidos exportados; com lista
  vazia, devolve 0.
- `summary(conn)`: `{"paid_share": <fração de pedidos pagos>}`; sem pedidos,
  `paid_share` é 0.
