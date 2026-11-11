from app.text import slugify


def customer_handle(name: str) -> str:
    """Identificador público do cliente: "João da Silva" vira "@joao-da-silva"."""
    return "@" + slugify(name)
