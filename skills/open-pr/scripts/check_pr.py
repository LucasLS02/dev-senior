#!/usr/bin/env python3
"""Reprova um pr.md que não está pronto para virar descrição de PR.

Uso: python3 check_pr.py <pr.md> <spec.md> [raiz]

O pr.md tem na linha 1 "Título: <texto>" e, depois, o corpo em Markdown, com a
tabela "| AC | Status | Evidência |" na seção "Critérios de aceite". Imprime um
erro por linha ("<pr.md>:<linha>: <problema>") e sai 1, ou imprime "limpo" e
sai 0; arquivo ausente ou ilegível sai 2. Só biblioteca padrão; roda no python3
3.9 do macOS.
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

Line = tuple[int, str]  # (número da linha, texto)

TITLE_MAX = 72
BODY_MAX = 80
REQUIRED = ("Resumo", "Critérios de aceite")
STATUSES = ("passou", "pendente")

FENCE = re.compile(r"^\s*(`{3,}|~{3,})")
SEPARATOR = re.compile(r":?-{3,}:?")
MARKER = re.compile(r"\[PRECISA DECISÃO[^\]]*\]")
TITLE = re.compile(r"^Título:\s*(.*?)\s*$")
AC_HEAD = re.compile(r"^### (AC-\d{3})\b")
AC_QUALITY = re.compile(r"^- (AC-Q\d{2})\b")
LOCAL_PATH = ".agent_plans/"


def _err(pr: Path, line: int, msg: str) -> str:
    return f"{pr.name}:{line}: {msg}" if line else f"{pr.name}: {msg}"


def _read(path: Path) -> list[Line] | None:
    try:
        return list(enumerate(path.read_text(encoding="utf-8").splitlines(), start=1))
    except UnicodeDecodeError:
        return None


def _unfenced(lines: list[Line]) -> tuple[list[Line], int]:
    """Linhas fora de blocos de código cercados e a linha da cerca que não fechou (0 = nenhuma)."""
    out, fence, opened = [], None, 0
    for n, text in lines:
        match = FENCE.match(text)
        if fence is None and match:
            fence, opened = match.group(1), n
        elif fence is not None and text.strip().startswith(fence) and \
                set(text.strip()) == {fence[0]}:
            fence = None
        elif fence is None:
            out.append((n, text))
    return out, (opened if fence else 0)


def _sections(lines: list[Line]) -> dict[str, list[Line]]:
    out: dict[str, list[Line]] = {"": []}
    current = ""
    for n, text in _unfenced(lines)[0]:
        match = re.match(r"^## (.+?)\s*$", text)
        if match:
            current = match.group(1)
            out[current] = []
        out[current].append((n, text))
    return out


def _split_cells(text: str) -> list[str]:
    """Células de uma linha de tabela; `|` em crases ou escapado (`\\|`) não parte."""
    s = text.strip()
    s = s[1:] if s.startswith("|") else s
    s = s[:-1] if s.endswith("|") and not s.endswith("\\|") else s
    cells, cur, in_code, i = [], [], False, 0
    while i < len(s):
        ch = s[i]
        if ch == "\\" and s[i + 1:i + 2] == "|":
            cur.append("|")
            i += 2
            continue
        in_code = in_code != (ch == "`")
        if ch == "|" and not in_code:
            cells.append("".join(cur).strip())
            cur = []
        else:
            cur.append(ch)
        i += 1
    cells.append("".join(cur).strip())
    return cells


def _rows(section: list[Line]) -> list[tuple[int, list[str]]]:
    rows, header_seen = [], False
    for n, text in section:
        if not text.strip().startswith("|"):
            continue
        cells = _split_cells(text)
        if not header_seen:  # a primeira linha de tabela da seção é o cabeçalho
            header_seen = True
        elif not all(SEPARATOR.fullmatch(c) for c in cells):
            rows.append((n, cells))
    return rows


def _spec_acs(spec: Path) -> tuple[list[str], set[str]]:
    """Todos os AC da spec e, entre eles, os de tipo manual."""
    acs: list[str] = []
    manual: set[str] = set()
    current = ""
    for _, text in _unfenced(_read(spec) or [])[0]:
        if m := AC_HEAD.match(text) or AC_QUALITY.match(text):
            current = m.group(1) if text.startswith("###") else ""
            acs.append(m.group(1))
        elif current and text.startswith("- Tipo:") and text.split(":", 1)[1].strip() == "manual":
            manual.add(current)
    return acs, manual


def _check_title(pr: Path, lines: list[Line]) -> list[str]:
    match = TITLE.match(lines[0][1]) if lines else None
    if not match:
        return [_err(pr, 1, 'título: a linha 1 deve ser "Título: <texto>"')]
    title = match.group(1)
    if not title or len(title) > TITLE_MAX:
        return [_err(pr, 1, f"título: de 1 a {TITLE_MAX} caracteres")]
    return [_err(pr, 1, "título: sem ponto final")] if title.endswith(".") else []


def _check_criteria(pr: Path, sections: dict[str, list[Line]], spec: Path) -> list[str]:
    errors = []
    acs, manual = _spec_acs(spec)
    seen: set[str] = set()
    for n, cells in _rows(sections.get("Critérios de aceite", [])):
        ident, status, evidence = (cells + ["", "", ""])[:3]
        if ident not in acs:
            errors.append(_err(pr, n, f"desconhecido: {ident}"))
            continue
        if status not in STATUSES:
            errors.append(_err(pr, n, f"status inválido: {status} ({ident})"))
        elif status == "pendente" and ident not in manual:
            errors.append(_err(pr, n, f"pendente só vale para AC manual: {ident}"))
        if evidence in ("", "—"):
            errors.append(_err(pr, n, f"AC sem evidência: {ident}"))
        else:
            seen.add(ident)
    return errors + [_err(pr, 0, f"AC sem evidência: {ident}") for ident in acs if ident not in seen]


def check(pr: Path, spec: Path, root: Path) -> list[str]:
    """Erros do pr.md contra a spec; lista vazia = pronto. `root` é a raiz do repositório."""
    lines = _read(pr)
    if lines is None:
        return [_err(pr, 0, "arquivo não é UTF-8")]
    errors = _check_title(pr, lines)
    if opened := _unfenced(lines)[1]:
        errors.append(_err(pr, opened, "cerca de código aberta, sem fechar"))
    body = lines[1:]
    if len(body) > BODY_MAX:
        errors.append(_err(pr, 0, f"corpo maior que {BODY_MAX} linhas ({len(body)})"))
    sections = _sections(body)
    errors += [_err(pr, 0, f"seção ausente: {name}") for name in REQUIRED if name not in sections]
    summary = sections.get("Resumo", [])
    if summary and not any(t.strip() for _, t in summary[1:]):
        errors.append(_err(pr, summary[0][0], "Resumo vazio"))
    errors += _check_criteria(pr, sections, spec)
    errors += [_err(pr, n, f"marcador pendente: {m}")
               for n, text in _unfenced(lines)[0] for m in MARKER.findall(text)]
    errors += [_err(pr, n, f"caminho local: {LOCAL_PATH} não existe para quem lê a PR")
               for n, text in lines if LOCAL_PATH in text]
    return errors


def main(argv: list[str]) -> int:
    if len(argv) < 2:
        print("uso: check_pr.py <pr.md> <spec.md> [raiz]", file=sys.stderr)
        return 2
    pr, spec = Path(argv[0]), Path(argv[1])
    for f in (pr, spec):
        if not f.is_file():
            print(f"arquivo não encontrado: {f}", file=sys.stderr)
            return 2
    try:
        errors = check(pr, spec, Path(argv[2] if len(argv) > 2 else ".").resolve())
    except OSError as exc:
        print(f"erro de leitura: {exc}", file=sys.stderr)
        return 2
    print("\n".join(errors) if errors else "limpo")
    return 1 if errors else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
