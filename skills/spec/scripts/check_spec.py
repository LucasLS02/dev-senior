#!/usr/bin/env python3
"""Reprova uma spec.md que não segue o formato da skill spec.

Uso: python3 check_spec.py <spec.md> [raiz]

Imprime um erro por linha ("<spec.md>:<linha>: <problema>") e sai 1, ou
imprime "limpo" e sai 0. Só biblioteca padrão; roda no python3 3.9 do macOS.
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

Line = tuple[int, str]  # (número da linha, texto)

MODES = ("rápido", "padrão", "profundo")
STATUSES = ("rascunho", "aprovado")
FAST_SECTIONS = ("Objetivo", "Escopo", "Critérios de aceite", "Tarefas")
FULL_SECTIONS = FAST_SECTIONS + (
    "Entendimento", "Padrões aplicáveis", "Referências no código", "Decisões",
    "Reuso", "Matriz de casos", "Rastreabilidade")
INVESTIGATION = ("Padrões aplicáveis", "Referências no código", "Reuso")
SCOPE_LINES = ("Permitido", "Proibido", "Exige aprovação", "Orçamento")

FENCE = re.compile(r"^\s*(`{3,}|~{3,})")
HEADER = re.compile(r"^Status:\s*(?P<status>[^·]+?)\s*·\s*Brief:\s*(?P<brief>[^·]+?)"
                    r"\s*·\s*Modo:\s*(?P<mode>.+?)\s*$")
SCOPE_LINE = re.compile(r"^[-*] (Permitido|Proibido|Exige aprovação|Orçamento):\s*(.*)$")
BUDGET = re.compile(r"arquivos novos \d+ · abstrações novas \d+ · dependências novas \d+")
DECISION = re.compile(r"(?i)(reusar|adaptar|criar)\b")
SEPARATOR = re.compile(r":?-{3,}:?")
KINDS = ("teste", "comando", "inspeção", "manual")
AC_ID = re.compile(r"AC-Q?\d+")
AC_HEAD = re.compile(r"^### (AC-\d{3})\b")
AC_QUALITY = re.compile(r"^- (AC-Q\d{2})\b")
TASK_HEAD = re.compile(r"^### (T\d+)\b(.*)$")
BACKTICKED = re.compile(r"`[^`]+`")
MARKER = re.compile(r"\[PRECISA DECISÃO[^\]]*\]")
CITATION = re.compile(r"(?P<path>[^\s:]+):(?P<first>\d+)(?:-(?P<last>\d+))?")


def _err(spec: Path, line: int, msg: str) -> str:
    return f"{spec.name}:{line}: {msg}" if line else f"{spec.name}: {msg}"


def _unfenced(lines: list[Line]) -> list[Line]:
    """Linhas fora de blocos de código cercados."""
    out, fence = [], None
    for n, text in lines:
        match = FENCE.match(text)
        if fence is None and match:
            fence = match.group(1)
        elif fence is not None and text.strip().startswith(fence) and \
                set(text.strip()) == {fence[0]}:
            fence = None
        elif fence is None:
            out.append((n, text))
    return out


def _sections(lines: list[Line]) -> dict[str, list[Line]]:
    """Linhas por título `## `, fora de cerca. A primeira linha de cada seção é o
    próprio título; a chave "" guarda o que vem antes do primeiro `##`."""
    out: dict[str, list[Line]] = {"": []}
    current = ""
    for n, text in _unfenced(lines):
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
    """Linhas de dado das tabelas de uma seção (sem cabeçalho nem separador)."""
    rows, in_table = [], False
    for n, text in section:
        if not text.strip().startswith("|"):
            in_table = False
            continue
        cells = _split_cells(text)
        if not in_table:  # a primeira linha de cada tabela é o cabeçalho
            in_table = True
        elif not all(SEPARATOR.fullmatch(c) for c in cells):
            rows.append((n, cells))
    return rows


def _heading_line(sections: dict[str, list[Line]], name: str) -> int:
    return sections[name][0][0] if sections.get(name) else 0


def _parse_header(sections: dict[str, list[Line]]) -> tuple[int, dict[str, str]] | None:
    for n, text in sections[""]:
        match = HEADER.match(text)
        if match:
            return n, match.groupdict()
    return None


def _check_header(spec: Path, sections: dict[str, list[Line]]) -> tuple[list[str], str]:
    """Erros do cabeçalho e o modo a usar nas demais checagens."""
    header = _parse_header(sections)
    if header is None:
        return [_err(spec, 0, 'cabeçalho: falta a linha "Status: … · Brief: … · Modo: …"')], "padrão"
    n, fields = header
    errors, mode = [], fields["mode"]
    if fields["status"] not in STATUSES:
        errors.append(_err(spec, n, f"Status inválido: {fields['status']}"))
    if mode not in MODES:
        errors.append(_err(spec, n, f"Modo inválido: {mode}"))
        mode = "padrão"
    return errors, mode


def _check_sections(spec: Path, sections: dict[str, list[Line]], mode: str) -> list[str]:
    required = FAST_SECTIONS if mode == "rápido" else FULL_SECTIONS
    return [_err(spec, 0, f"seção ausente: {name}") for name in required
            if name not in sections]


def _check_investigation(spec: Path, sections: dict[str, list[Line]]) -> list[str]:
    return [_err(spec, _heading_line(sections, name), f"seção sem linhas: {name}")
            for name in INVESTIGATION if name in sections and not _rows(sections[name])]


def _check_scope(spec: Path, sections: dict[str, list[Line]]) -> list[str]:
    if "Escopo" not in sections:
        return []
    found = {m.group(1): (n, m.group(2).strip()) for n, text in sections["Escopo"]
             if (m := SCOPE_LINE.match(text))}
    errors = [_err(spec, _heading_line(sections, "Escopo"), f'Escopo: falta "{name}"')
              for name in SCOPE_LINES if not found.get(name, (0, ""))[1]]
    budget = found.get("Orçamento")
    if budget and budget[1] and not BUDGET.search(budget[1]):
        errors.append(_err(spec, budget[0], "Escopo: Orçamento precisa dos três números "
                           "(arquivos novos, abstrações novas, dependências novas)"))
    return errors


def _check_tables(spec: Path, sections: dict[str, list[Line]]) -> list[str]:
    errors = []
    for n, cells in _rows(sections.get("Reuso", [])):
        if not DECISION.match(cells[-1]):
            errors.append(_err(spec, n, "Reuso: linha sem decisão (Reusar, Adaptar ou Criar)"))
    for n, cells in _rows(sections.get("Decisões", [])):
        if len(cells) < 2 or not cells[1]:
            errors.append(_err(spec, n, "Decisões: linha sem alternativa mais simples"))
    return errors


def _check_ac(spec: Path, ac: str, n: int, body: list[Line]) -> list[str]:
    texts = [t for _, t in body]
    verification = next((t for t in texts if t.startswith("- Verificação:")), None)
    kind = next((t for t in texts if t.startswith("- Tipo:")), None)
    errors = []
    if not any(re.search(r"\bQUANDO\b.*\bENTÃO\b", t) for t in texts):
        errors.append(_err(spec, n, f'{ac}: falta "QUANDO … ENTÃO …"'))
    if verification is None:
        errors.append(_err(spec, n, f'{ac}: falta "Verificação"'))
    if kind is None:
        errors.append(_err(spec, n, f'{ac}: falta "Tipo"'))
        return errors
    value = kind.split(":", 1)[1].strip()
    if value not in KINDS:
        errors.append(_err(spec, n, f"{ac}: Tipo inválido: {value}"))
    elif verification and value in ("teste", "comando") and not BACKTICKED.search(verification):
        errors.append(_err(spec, n, f"{ac}: Verificação sem comando entre crases"))
    return errors


def _check_quality(spec: Path, ac: str, n: int, text: str) -> list[str]:
    errors = []
    if "Verificação:" not in text:
        errors.append(_err(spec, n, f'{ac}: falta "Verificação"'))
    if not BACKTICKED.search(text):
        errors.append(_err(spec, n, f"{ac}: não nomeia arquivo ou comando"))
    return errors


def _check_criteria(spec: Path, sections: dict[str, list[Line]]) -> tuple[list[str], dict[str, int]]:
    """Erros dos AC e dos critérios de qualidade, e o mapa ID -> linha."""
    ids: dict[str, int] = {}
    errors: list[str] = []
    blocks: list[tuple[str, int, list[Line]]] = []
    quality = False
    section = sections.get("Critérios de aceite", [])
    for n, text in section[1:]:
        if text.startswith("### "):
            quality = text.startswith("### Critérios de qualidade")
            head = AC_HEAD.match(text)
            if head:
                if head.group(1) in ids:
                    errors.append(_err(spec, n, f"{head.group(1)} duplicado"))
                ids.setdefault(head.group(1), n)
                blocks.append((head.group(1), n, []))
        elif quality and (item := AC_QUALITY.match(text)):
            ids[item.group(1)] = n
            errors += _check_quality(spec, item.group(1), n, text)
        elif blocks and not quality:
            blocks[-1][2].append((n, text))
    for ac, n, body in blocks:
        errors += _check_ac(spec, ac, n, body)
    if section and not blocks:
        errors.append(_err(spec, section[0][0], "nenhum critério de aceite"))
    return errors, ids


def _check_tasks(spec: Path, sections: dict[str, list[Line]], ac_ids: dict[str, int]
                 ) -> tuple[list[str], dict[str, list[str]]]:
    """Erros das tarefas e, por AC, as tarefas que o cobrem."""
    tasks: list[tuple[str, int, str, list[str]]] = []
    for n, text in sections.get("Tarefas", [])[1:]:
        head = TASK_HEAD.match(text)
        if head:
            tasks.append((head.group(1), n, head.group(2), []))
        elif tasks:
            tasks[-1][3].append(text)
    known = {task_id for task_id, *_ in tasks}
    covers: dict[str, list[str]] = {}
    errors: list[str] = []
    for task_id, n, head, body in tasks:
        depends = head.partition("Depende de:")[2].split("·")[0]
        covered = AC_ID.findall(head.partition("Cobre:")[2])
        if not covered:
            errors.append(_err(spec, n, f"{task_id}: não cobre nenhum AC"))
        for ac in covered:
            covers.setdefault(ac, []).append(task_id)
            if ac not in ac_ids:
                errors.append(_err(spec, n, f"{task_id}: cobre {ac}, que não existe"))
        errors += [_err(spec, n, f"{task_id}: depende de {dep}, que não existe")
                   for dep in re.findall(r"T\d+", depends) if dep not in known]
        if not any(t.startswith("- Arquivos:") for t in body):
            errors.append(_err(spec, n, f'{task_id}: falta "Arquivos"'))
        ready = next((t for t in body if t.startswith("- Pronto quando:")), "")
        if not BACKTICKED.search(ready):
            errors.append(_err(spec, n, f'{task_id}: falta "Pronto quando" com comando entre crases'))
    errors += [_err(spec, line, f"{ac}: nenhuma tarefa o cobre")
               for ac, line in ac_ids.items() if ac not in covers]
    return errors, covers


def _check_traceability(spec: Path, sections: dict[str, list[Line]],
                        covers: dict[str, list[str]]) -> list[str]:
    if "Rastreabilidade" not in sections:
        return []
    table = {cells[0]: (n, sorted(re.findall(r"T\d+", cells[1] if len(cells) > 1 else "")))
             for n, cells in _rows(sections["Rastreabilidade"])}
    errors = []
    for ac, tasks in covers.items():
        expected = sorted(tasks)
        if ac not in table:
            errors.append(_err(spec, _heading_line(sections, "Rastreabilidade"),
                               f"Rastreabilidade: falta {ac}"))
        elif table[ac][1] != expected:
            listed = ", ".join(table[ac][1]) or "—"
            errors.append(_err(spec, table[ac][0], f"Rastreabilidade: {ac} lista {listed}, "
                               f"as tarefas dizem {', '.join(expected)}"))
    return errors


def _check_matrix(spec: Path, sections: dict[str, list[Line]], ac_ids: dict[str, int]) -> list[str]:
    errors = []
    for n, cells in _rows(sections.get("Matriz de casos", [])):
        case, target = cells[0], cells[-1]
        refs = AC_ID.findall(target)
        if not refs and not target.lower().startswith("fora de escopo"):
            errors.append(_err(spec, n, f'Matriz de casos: "{case}" não aponta para um AC '
                               'nem para "fora de escopo"'))
        errors += [_err(spec, n, f'Matriz de casos: "{case}" aponta para {ac}, que não existe')
                   for ac in refs if ac not in ac_ids]
    return errors


def _prose(sections: dict[str, list[Line]]) -> list[Line]:
    """Todas as linhas fora de cerca, na ordem do arquivo."""
    return sorted(line for lines in sections.values() for line in lines)


def _check_markers(spec: Path, sections: dict[str, list[Line]]) -> list[str]:
    return [_err(spec, n, f"marcador pendente: {marker}")
            for n, text in _prose(sections) for marker in MARKER.findall(text)]


def _check_citations(spec: Path, sections: dict[str, list[Line]], root: Path) -> list[str]:
    """Só `arquivo:linha`; caminho solto pode ser arquivo a criar."""
    errors = []
    for n, text in _prose(sections):
        for token in BACKTICKED.findall(text):
            cited = CITATION.fullmatch(token.strip("`"))
            if not cited or cited["path"].startswith("/"):
                continue
            path = cited["path"].rstrip("/")
            # ponytail: só confere o que começa num item real da raiz
            if path.split("/")[0] in {".", ".."} or not (root / path.split("/")[0]).exists():
                continue
            target = root / path
            last = int(cited["last"] or cited["first"])
            if not target.exists():
                errors.append(_err(spec, n, f"cita {token}, que não existe"))
            elif target.is_file() and last > len(
                    target.read_text(encoding="utf-8", errors="replace").splitlines()):
                errors.append(_err(spec, n, f"cita {token}, além do fim do arquivo"))
    return errors


def _check_brief(spec: Path, sections: dict[str, list[Line]], root: Path) -> list[str]:
    header = _parse_header(sections)
    if header is None:
        return []
    n, fields = header
    brief, mode = fields["brief"], fields["mode"]
    if brief == "—":
        return [] if mode == "rápido" else [_err(spec, n, f"Modo {mode} exige Brief")]
    return [] if (root / brief).is_file() else [_err(spec, n, f"Brief inexistente: {brief}")]


def check(spec: Path, root: Path) -> list[str]:
    """Erros da spec; lista vazia = limpa. `root` é a raiz do repositório."""
    text = spec.read_text(encoding="utf-8", errors="replace")
    sections = _sections(list(enumerate(text.splitlines(), start=1)))
    errors, mode = _check_header(spec, sections)
    errors += _check_sections(spec, sections, mode)
    errors += _check_investigation(spec, sections)
    errors += _check_scope(spec, sections)
    errors += _check_tables(spec, sections)
    criteria_errors, ac_ids = _check_criteria(spec, sections)
    task_errors, covers = _check_tasks(spec, sections, ac_ids)
    errors += criteria_errors + task_errors
    errors += _check_traceability(spec, sections, covers)
    errors += _check_matrix(spec, sections, ac_ids)
    errors += _check_markers(spec, sections)
    errors += _check_citations(spec, sections, root)
    errors += _check_brief(spec, sections, root)
    return errors


def main(argv: list[str]) -> int:
    if not argv:
        print("uso: check_spec.py <spec.md> [raiz]", file=sys.stderr)
        return 2
    spec = Path(argv[0])
    if not spec.is_file():
        print(f"spec não encontrada: {spec}", file=sys.stderr)
        return 2
    errors = check(spec, Path(argv[1] if len(argv) > 1 else ".").resolve())
    print("\n".join(errors) if errors else "limpo")
    return 1 if errors else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
