#!/usr/bin/env bash
# Monta o repositório de teste da skill codebase-agent-docs: um serviço Python
# pequeno, sem remoto, cujo histórico planta três armadilhas (commits de
# correção), um helper recriado e depois reaproveitado e um arquivo gerado.
# Em "auditar", um último commit traz um AGENTS.md escrito à mão. Em "spec", o
# último commit traz um AGENTS.md correto, sem citação quebrada e sem mencionar
# o helper de slug (a skill spec precisa achá-lo por busca).
set -euo pipefail

if [ $# -ne 2 ] || { [ "$2" != criar ] && [ "$2" != auditar ] && [ "$2" != spec ]; }; then
  echo "uso: $0 <destino> criar|auditar|spec" >&2
  exit 2
fi
dest=$1
mkdir -p "$dest"
git init -q "$dest"
cd "$dest"
w() { mkdir -p "$(dirname "$1")"; cat > "$1"; }
commit() {  # commit <assunto> [corpo]
  git add -A
  git -c user.name=fixture -c user.email=fixture@example.invalid \
    commit -q -m "$1" ${2:+-m "$2"}
}

# 1. estrutura inicial
w .gitignore <<'EOF'
__pycache__/
.env
EOF
w .env.example <<'EOF'
DATABASE_URL=postgresql://localhost:5432/notify
EOF
w README.md <<'EOF'
# Notificações

Serviço pequeno de notificações e exportação de pedidos.

Testes: `python3 -m unittest discover -s tests`
EOF
w app/__init__.py </dev/null
w app/text.py <<'EOF'
import re
import unicodedata


def slugify(text: str) -> str:
    plain = unicodedata.normalize("NFKD", text).encode("ascii", "ignore").decode()
    return re.sub(r"[^a-z0-9]+", "-", plain.lower()).strip("-")
EOF
w app/handlers/outbox.py <<'EOF'
OUTBOX: list = []
EOF
w app/handlers/email.py <<'EOF'
from app.handlers.outbox import OUTBOX


def send_email(message: str) -> None:
    OUTBOX.append(("email", message))
EOF
w app/handlers/sms.py <<'EOF'
from app.handlers.outbox import OUTBOX


def send_sms(message: str) -> None:
    OUTBOX.append(("sms", message))
EOF
w app/handlers/__init__.py <<'EOF'
from app.handlers.email import send_email

HANDLERS = {"email": send_email}


def dispatch(channel: str, message: str) -> bool:
    handler = HANDLERS.get(channel)
    if handler is None:
        return False
    handler(message)
    return True
EOF
w app/export.py <<'EOF'
from datetime import datetime


def export_row(order: dict) -> dict:
    return {"id": order["id"], "total": order["total"],
            "exported_at": datetime.now().isoformat()}
EOF
w tests/test_text.py <<'EOF'
import unittest

from app.text import slugify


class SlugifyTest(unittest.TestCase):
    def test_removes_accents(self):
        self.assertEqual(slugify("João da Silva"), "joao-da-silva")
EOF
w tests/test_handlers.py <<'EOF'
import unittest

from app.handlers import dispatch
from app.handlers.outbox import OUTBOX


class DispatchTest(unittest.TestCase):
    def test_email_is_sent(self):
        self.assertTrue(dispatch("email", "oi"))
        self.assertIn(("email", "oi"), OUTBOX)
EOF
w tests/integration/__init__.py </dev/null
w tests/integration/test_db.py <<'EOF'
import os
import unittest


@unittest.skipUnless(os.environ.get("DATABASE_URL"), "precisa de DATABASE_URL")
class DatabaseTest(unittest.TestCase):
    def test_connects(self):
        self.assertTrue(os.environ["DATABASE_URL"].startswith("postgresql://"))
EOF
commit "chore: initial structure"

# 2. exportação com uma cópia local de slugify
w app/export.py <<'EOF'
import re
import unicodedata
from datetime import datetime


def _slug(text: str) -> str:
    plain = unicodedata.normalize("NFKD", text).encode("ascii", "ignore").decode()
    return re.sub(r"[^a-z0-9]+", "-", plain.lower()).strip("-")


def export_row(order: dict) -> dict:
    return {"id": order["id"], "customer": _slug(order["customer"]),
            "total": order["total"], "exported_at": datetime.now().isoformat()}


def export_csv(orders: list) -> str:
    rows = [export_row(o) for o in orders]
    lines = ["id,customer,total,exported_at"]
    lines += [f'{r["id"]},{r["customer"]},{r["total"]},{r["exported_at"]}' for r in rows]
    return "\n".join(lines)
EOF
w tests/test_export.py <<'EOF'
import unittest

from app.export import export_row


class ExportTest(unittest.TestCase):
    def test_customer_is_slugified(self):
        row = export_row({"id": 1, "customer": "Ana Lima", "total": "10,00"})
        self.assertEqual(row["customer"], "ana-lima")
EOF
commit "feat: add csv export"

# 3. armadilha A1: hora local
sed -i.bak 's/^from datetime import datetime$/from datetime import datetime, timezone/; s/datetime.now()/datetime.now(timezone.utc)/' app/export.py
rm app/export.py.bak
commit "fix: use UTC timestamps in export" \
  "Exports ran in the server's local time. The nightly job compares them with UTC cutoffs, so orders near midnight were skipped with no error."

# 4. armadilha A2: canal fora de HANDLERS
w app/handlers/__init__.py <<'EOF'
from app.handlers.email import send_email
from app.handlers.sms import send_sms

HANDLERS = {"email": send_email, "sms": send_sms}


def dispatch(channel: str, message: str) -> bool:
    handler = HANDLERS.get(channel)
    if handler is None:
        return False
    handler(message)
    return True
EOF
commit "fix: register sms handler in HANDLERS" \
  "dispatch() returns False for a channel missing from HANDLERS and nothing logs it. app/handlers/sms.py existed since the start, but every SMS was dropped silently."

# 5. reuso R1: slugify
w app/export.py <<'EOF'
from datetime import datetime, timezone

from app.text import slugify


def export_row(order: dict) -> dict:
    return {"id": order["id"], "customer": slugify(order["customer"]),
            "total": order["total"], "exported_at": datetime.now(timezone.utc).isoformat()}


def export_csv(orders: list) -> str:
    rows = [export_row(o) for o in orders]
    lines = ["id,customer,total,exported_at"]
    lines += [f'{r["id"]},{r["customer"]},{r["total"]},{r["exported_at"]}' for r in rows]
    return "\n".join(lines)
EOF
commit "refactor: reuse slugify from app.text in export" \
  "export kept a private copy of slugify. app.text.slugify is the single implementation."

# 6. armadilha A3: dinheiro em float
w app/money.py <<'EOF'
def to_cents(value: str) -> int:
    reais, _, cents = value.partition(",")
    return int(reais) * 100 + int((cents + "00")[:2])
EOF
sed -i.bak 's/"total": order\["total"\]/"total_cents": to_cents(order["total"])/; s/^from app.text import slugify$/from app.money import to_cents\nfrom app.text import slugify/; s/id,customer,total,exported_at/id,customer,total_cents,exported_at/; s/{r\["total"\]}/{r["total_cents"]}/' app/export.py
rm app/export.py.bak
commit "fix: keep totals in integer cents" \
  "Totals were parsed into float reais and summed. Large batches drifted by a cent with no error. Money stays in integer cents end to end."

# 7. arquivo gerado
w scripts/gen_schema.py <<'EOF'
from pathlib import Path

FIELDS = ["id", "customer", "total_cents", "exported_at"]
HEADER = "# Gerado por scripts/gen_schema.py. Não editar.\n"
Path("app/schema_gen.py").write_text(HEADER + f"EXPORT_FIELDS = {FIELDS!r}\n")
EOF
python3 scripts/gen_schema.py
commit "chore: add generated schema"

if [ "$2" = auditar ]; then
  w AGENTS.md <<'EOF'
# Notificações — guia para agentes

Escrito à mão pela equipe. Leia antes de mexer.

## Comandos

- Testes: `python3 -m unittest discover -s tests`
- Integração: precisa de `DATABASE_URL` (veja `.env.example`).

## Onde fica cada coisa

| Caminho | O que tem |
| --- | --- |
| `app/handlers/` | Canais de envio e o despacho |
| `app/export.py` | Exportação CSV |
| `app/legacy_export.py` | Exportação antiga, mantida por compatibilidade |
| `scripts/` | Geradores |

## Regras

Regra da casa: revisar com a Ana antes de mexer em HANDLERS.

Dinheiro sempre em centavos inteiros.

## Conflito entre este arquivo e o código

Vale o código. Corrija este arquivo junto com a mudança.
EOF
  commit "docs: add agent guide"
fi

if [ "$2" = spec ]; then
  w AGENTS.md <<'EOF'
# Notificações — guia para agentes

## Comandos

- Testes: `python3 -m unittest discover -s tests`

## Regras

- Canal novo entra no registro de `app/handlers/__init__.py`; sem isso a mensagem é descartada sem aviso.
- Dinheiro em centavos inteiros, nunca float.
- Horários em UTC.
EOF
  commit "docs: add agent guide"
fi
