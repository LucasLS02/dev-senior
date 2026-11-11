#!/usr/bin/env python3
"""Reprova a documentação de agentes que passa dos limites ou cita o que não existe.

Uso: python3 check_docs.py [raiz]

Imprime um erro por linha ("<arquivo>: <problema>") e sai 1, ou imprime
"limpo" e sai 0. Só biblioteca padrão; roda no python3 3.9 do macOS.
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

ROOT_MAX = 120
DIR_GUIDE_MAX = 75
TOPIC_MAX = 140
RECIPE_MAX = 160
REVIEW_MAX = 80
TOPIC_LINKS_MAX = 1
IGNORED_DIRS = {".git", ".agent_plans", "node_modules", "vendor", ".venv", "dist",
                "build"}

FENCE = re.compile(r"^\s*(`{3,}|~{3,})")
LINK = re.compile(r"\]\(([^)\s]+)\)")
CODE = re.compile(r"`([^`\n]+)`")
CITED = re.compile(r"(?P<path>[^:]+?)(?::(?P<line>\d+)(?:-\d+)?)?")
NOT_A_PATH = (" ", "<", ">", "*", "$", "://")


def _read(path: Path) -> str:
    # repositório antigo pode ter arquivo latin-1: contar linhas não exige decodificar bem
    return path.read_text(encoding="utf-8", errors="replace")


def _prose_lines(text: str) -> list[str]:
    """Linhas fora de blocos de código cercados."""
    out, fence = [], None
    for line in text.splitlines():
        match = FENCE.match(line)
        if fence is None and match:
            fence = match.group(1)
        elif fence is not None and line.strip().startswith(fence) and \
                set(line.strip()) == {fence[0]}:
            fence = None
        elif fence is None:
            out.append(line)
    return out


def _doc_files(root: Path) -> list[Path]:
    guides = [p for p in root.rglob("AGENTS.md")
              if not IGNORED_DIRS & set(p.relative_to(root).parts)]
    agents_dir = root / "docs/agents"
    topics = sorted(agents_dir.rglob("*.md")) if agents_dir.is_dir() else []
    review = [root / "REVIEW.md"] if (root / "REVIEW.md").is_file() else []
    return sorted(guides) + topics + review


def _limit(root: Path, path: Path) -> int:
    rel = path.relative_to(root).as_posix()
    if rel == "AGENTS.md":
        return ROOT_MAX
    if rel == "REVIEW.md":
        return REVIEW_MAX
    if rel.startswith("docs/agents/recipes/"):
        return RECIPE_MAX
    if rel.startswith("docs/agents/"):
        return TOPIC_MAX
    return DIR_GUIDE_MAX


def _check_citations(root: Path, doc: Path, prose: list[str]) -> list[str]:
    errors = []
    rel = doc.relative_to(root).as_posix()
    for token in CODE.findall("\n".join(prose)):
        # "/x" é rota ou caminho absoluto, não caminho do repositório
        if token.startswith("/") or any(mark in token for mark in NOT_A_PATH):
            continue
        cited = CITED.fullmatch(token)
        cited_path = cited.group("path").rstrip("/") if cited else ""
        first = cited_path.split("/")[0]
        # vale a partir da raiz ou da pasta do documento (guia de pasta)
        bases = [b for b in (root, doc.parent) if (b / first).exists()]
        if not cited_path or first in {".", ".."} or not bases:
            continue  # ponytail: só confere o que começa num item real
        targets = [b / cited_path for b in bases if (b / cited_path).exists()]
        if not targets:
            errors.append(f"{rel}: cita `{token}`, que não existe")
        elif cited.group("line") and targets[0].is_file():
            if int(cited.group("line")) > len(_read(targets[0]).splitlines()):
                errors.append(f"{rel}: cita `{token}`, além do fim do arquivo")
    return errors


def check(root: Path) -> list[str]:
    errors = []
    if not (root / "AGENTS.md").is_file():
        errors.append("AGENTS.md: não existe na raiz")
    index = set()
    for path in _doc_files(root):
        rel = path.relative_to(root).as_posix()
        text = _read(path)
        prose = _prose_lines(text)
        limit = _limit(root, path)
        if len(text.splitlines()) > limit:
            errors.append(f"{rel}: {len(text.splitlines())} linhas, limite {limit}")
        if any(line.startswith("### ") for line in prose):
            errors.append(f"{rel}: título ### fora de bloco de código")
        links = [t for t in LINK.findall("\n".join(prose))
                 if not t.startswith(("http://", "https://", "mailto:", "#"))]
        if rel.startswith("docs/agents/") and "/" not in rel[len("docs/agents/"):] \
                and len(links) > TOPIC_LINKS_MAX:
            errors.append(f"{rel}: {len(links)} links, limite {TOPIC_LINKS_MAX}")
        for target in links:
            resolved = (path.parent / target.split("#")[0]).resolve()
            if not resolved.exists():
                errors.append(f"{rel}: link para {target}, que não existe")
            elif rel == "AGENTS.md":
                index.add(resolved)
        errors += _check_citations(root, path, prose)
    for path in _doc_files(root):
        rel = path.relative_to(root).as_posix()
        if rel.startswith("docs/agents/") and path.resolve() not in index:
            errors.append(f"{rel}: fora do índice do AGENTS.md da raiz")
    return errors


def main() -> int:
    root = Path(sys.argv[1] if len(sys.argv) > 1 else ".").resolve()
    errors = check(root)
    print("\n".join(errors) if errors else "limpo")
    return 1 if errors else 0


if __name__ == "__main__":
    sys.exit(main())
