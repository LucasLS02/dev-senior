# Pedidos

Serviço pequeno de pedidos em Python, só com a biblioteca padrão.

## Regras

- Datas sempre com `datetime.now(timezone.utc)`; nunca `datetime.now()` sem fuso.
- SQL só com parâmetro `?`; nunca monte consulta com f-string ou concatenação.
- Antes de criar um helper, procure se ele já existe no projeto.

## Testes

`python3 -m unittest discover -s tests`
