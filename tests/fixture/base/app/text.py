import re
import unicodedata


def slugify(text: str) -> str:
    """Converte "João da Silva" em "joao-da-silva"."""
    plain = unicodedata.normalize("NFKD", text).encode("ascii", "ignore").decode()
    return re.sub(r"[^a-z0-9]+", "-", plain.lower()).strip("-")
