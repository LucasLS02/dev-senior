"""Fonte única do que cada ferramenta aprova sozinha e do que continua perguntando.

`apply.py` converte estas listas no formato de cada ferramenta.
"""
from __future__ import annotations

# Cada item é o comando como se digita; o argumento final varia (`ls -la`, `git diff HEAD`).
READ = """
cd ls pwd cat head tail wc file stat du which date basename dirname realpath
grep rg cut sort uniq tr awk diff cmp jq shasum echo printf sleep lsof
""".split()

GIT_READ = ["git " + g for g in """
status diff log show grep ls-files ls-tree ls-remote rev-parse rev-list merge-base
check-ignore remote fetch blame describe shortlog cat-file show-ref for-each-ref name-rev
""".split()] + [
    "git branch --list", "git branch -a", "git branch -r", "git branch -vv",
    "git branch --show-current", "git stash list", "git stash show", "git worktree list",
    "git config --get", "git tag -l", "git reflog show",
]

GH_READ = [
    "gh pr view", "gh pr list", "gh pr diff", "gh pr checks", "gh pr status",
    "gh run list", "gh run view", "gh issue view", "gh issue list", "gh repo view",
    "gh auth status",
    "gh api",  # o hook gh_api_guard.py pede aprovação quando for escrita
]

LOCAL_WRITE = ["mkdir", "touch", "cp", "mv", "ln", "chmod +x", "git add", "git switch",
               "git worktree add", "sed -n"]

# Só estes verificadores abrem via `pnpm exec` e `npx`; os dois sozinhos rodam qualquer binário.
JS_CHECKERS = ("tsc", "eslint", "vitest", "prettier", "biome")

STACKS = [
    # Python
    "pytest", "ruff check", "ruff format", "uv run pytest", "uv run ruff", "poetry run pytest",
    "poetry run ruff", "poetry show", "pre-commit run", "mdformat", "pymarkdown",
    "python3 -m unittest", "python3 -m pytest", "python -m pytest", ".venv/bin/pytest",
    # make: só os alvos medidos, nunca `make` solto
    "make validate", "make unit-tests", "make integration-tests", "make targets",
    "make github-actions-validate", "make github-actions-unit-coverage",
    "make github-actions-coverage", "make github-actions-integration-tests",
    "make check-tf-versions",
    # Node
    "pnpm test", "pnpm test:components", "pnpm lint", "pnpm lint:ci", "pnpm build",
    "pnpm typecheck", "pnpm tsc", "pnpm eslint", "pnpm vitest", "pnpm playwright test",
    "pnpm e2e", "pnpm e2e:i18n-contract", "pnpm deploy:validate", "pnpm audit",
    *[f"pnpm exec {t}" for t in JS_CHECKERS],
    "npx tsc", "npx eslint", "npx vitest", "npx prettier",
    "npx biome ci", "npx biome check", "npx biome lint", "npx next build",
    "node --test", "node --experimental-strip-types --test",
    # .NET
    "dotnet build", "dotnet test", "dotnet restore",
    # Terraform (nunca apply, destroy, import, state rm/mv)
    "terraform fmt", "terraform validate", "terraform init", "terraform test",
    "terraform plan", "terraform state list", "terraform state show", "terraform version",
    "actionlint",
    # Docker
    "docker ps", "docker logs", "docker images", "docker image ls", "docker image inspect",
    "docker inspect", "docker compose config", "docker compose ps", "docker compose logs",
    "docker version",
]

ALL = READ + GIT_READ + GH_READ + LOCAL_WRITE + STACKS

ASK = ["rm", "git commit", "git push", "git reset", "git clean", "git restore", "git checkout",
       "git branch -D", "git branch -d", "gh pr create", "gh pr merge", "gh pr close",
       "terraform apply", "terraform destroy", "docker rm", "docker run", "docker exec",
       "sudo", "pip install", "pnpm add", "pnpm install", "npm install", "brew install",
       "sed -i"]

# Nada disto pode entrar em ALL (conferido em tests/permissions_test.py).
NEVER_ALLOW = tuple(ASK) + ("gh auth token", "find", "xargs", "uvx")

# Credenciais: leitura bloqueada. `.env`: pergunta, porque às vezes o projeto precisa dele.
SECRET_DIRS = ("~/.ssh", "~/.aws", "~/.config/gh", "~/.azure", "~/.kube", "~/.gnupg")
SECRET_FILES = ("~/.netrc", "**/*.pem", "**/id_rsa*", "**/id_ed25519*")
ENV_GLOBS = ("**/.env", "**/.env.local", "**/.env.production", "**/.env.development")
ENV_NAMES = (".env", "./.env")
READERS = ("cat", "head", "tail", "less", "grep", "rg", "cp")
