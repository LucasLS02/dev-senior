#!/usr/bin/env python3
"""Reprova um brief.md que não segue o formato da skill refine.

Uso: python3 check_brief.py <brief.md> [raiz]

Imprime um erro por linha ("<brief.md>:<linha>: <problema>") e sai 1, ou
imprime "limpo" e sai 0. Só biblioteca padrão; roda no python3 3.9 do macOS.
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

Line = tuple[int, str]  # (número da linha, texto)

MODES = ("rápido", "padrão", "profundo")
STATUSES = ("rascunho", "aprovado", "descartado")
SECTIONS = ("Problema", "Pedido vs. necessidade", "Apetite", "Referências de mercado",
            "Opções consideradas", "Recomendação", "Fora de escopo", "Riscos e armadilhas",
            "Perguntas em aberto")
DIAGNOSTIC = ("Reprodução", "Causa raiz", "Comportamento atual", "Comportamento esperado",
              "Deve permanecer igual")
VERDICTS = ("Recomendada", "Descartada")
MAX_QUESTIONS = 5

FENCE = re.compile(r"^\s*(`{3,}|~{3,})")
TITLE = re.compile(r"^# Brief: \S")
HEADER = re.compile(r"^Status:\s*(?P<status>[^·]+?)\s*·\s*Origem:\s*(?P<origin>[^·]+?)"
                    r"\s*·\s*Modo:\s*(?P<mode>.+?)\s*$")
APPETITE_MODE = re.compile(r"^Modo (?P<mode>\S+):\s*\S")
SEPARATOR = re.compile(r":?-{3,}:?")
BACKTICKED = re.compile(r"`[^`]+`")
MARKER = re.compile(r"\[PRECISA DECISÃO[^\]]*\]")
CITATION = re.compile(r"(?P<path>[^\s:]+):(?P<first>\d+)(?:-(?P<last>\d+))?")


def _err(brief: Path, line: int, msg: str) -> str:
    return f"{brief.name}:{line}: {msg}" if line else f"{brief.name}: {msg}"


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
    """Linhas por título `## `, fora de cerca. A primeira linha de cada seção é o
    próprio título; a chave "" guarda o que vem antes do primeiro `##`."""
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


def _prose(sections: dict[str, list[Line]]) -> list[Line]:
    """Todas as linhas fora de cerca, na ordem do arquivo."""
    return sorted(line for lines in sections.values() for line in lines)


def _check_header(brief: Path, sections: dict[str, list[Line]]) -> tuple[list[str], str, str]:
    """Erros do título e do cabeçalho, mais o status e o modo para as demais checagens."""
    errors = []
    if not any(TITLE.match(text) for _, text in sections[""]):
        errors.append(_err(brief, 0, 'cabeçalho: falta o título "# Brief: <título>"'))
    header = next(((n, m) for n, text in sections[""] if (m := HEADER.match(text))), None)
    if header is None:
        errors.append(_err(brief, 0, 'cabeçalho: falta a linha "Status: … · Origem: … · Modo: …"'))
        return errors, "", ""
    n, match = header
    status, mode = match["status"], match["mode"]
    if status not in STATUSES:
        errors.append(_err(brief, n, f"cabeçalho: Status inválido: {status}"))
    if mode not in MODES:
        errors.append(_err(brief, n, f"cabeçalho: Modo inválido: {mode}"))
    return errors, status, mode


def _check_sections(brief: Path, sections: dict[str, list[Line]]) -> list[str]:
    return [_err(brief, 0, f"seção ausente: {name}") for name in SECTIONS if name not in sections]


def _check_appetite(brief: Path, sections: dict[str, list[Line]], mode: str) -> list[str]:
    if "Apetite" not in sections:
        return []
    found = next(((n, m) for n, text in sections["Apetite"][1:] if (m := APPETITE_MODE.match(text))), None)
    if found is None:
        return [_err(brief, sections["Apetite"][0][0], 'Apetite: falta a linha "Modo <modo>: <motivo>"')]
    n, match = found
    if mode in MODES and match["mode"] != mode:
        return [_err(brief, n, f"Apetite: modo {match['mode']} difere do cabeçalho ({mode})")]
    return []


def _check_need(brief: Path, sections: dict[str, list[Line]]) -> list[str]:
    if "Pedido vs. necessidade" not in sections:
        return []
    text = "\n".join(t for _, t in sections["Pedido vs. necessidade"][1:])
    return [_err(brief, sections["Pedido vs. necessidade"][0][0], f'Pedido vs. necessidade: falta "{label}"')
            for label in ("Pedido:", "Necessidade:") if label not in text]


def _check_market(brief: Path, sections: dict[str, list[Line]]) -> list[str]:
    if "Referências de mercado" not in sections:
        return []
    rows = _rows(sections["Referências de mercado"])
    if not rows:
        return [_err(brief, sections["Referências de mercado"][0][0],
                     "Referências de mercado: a tabela precisa de ao menos uma linha (`—` se não houve pesquisa)")]
    return [_err(brief, n, f"Referências de mercado: fonte sem URL nem caminho entre crases: {cells[0]}")
            for n, cells in rows
            if cells[0] != "—" and not re.search(r"https?://", cells[0]) and not BACKTICKED.search(cells[0])]


def _check_options(brief: Path, sections: dict[str, list[Line]], status: str) -> list[str]:
    if "Opções consideradas" not in sections:
        return []
    title = sections["Opções consideradas"][0][0]
    rows = _rows(sections["Opções consideradas"])
    errors = []
    if len(rows) < 3:
        errors.append(_err(brief, title, "Opções consideradas: menos de três opções"))
    for needle in ("não fazer", "sem código"):
        if not any(needle in cells[0].lower() for _, cells in rows):
            errors.append(_err(brief, title, f"Opções consideradas: falta a opção {needle}"))
    recommended = []
    for n, cells in rows:
        verdict = cells[3] if len(cells) > 3 else ""
        if verdict not in VERDICTS:
            errors.append(_err(brief, n, f"Opções consideradas: Veredito inválido: {verdict or '(vazio)'}"))
        elif verdict == "Recomendada":
            recommended.append(cells[0])
    if len(recommended) != 1:
        errors.append(_err(brief, title, f"Opções consideradas: exatamente uma Recomendada (achei {len(recommended)})"))
    elif status == "descartado" and "não fazer" not in recommended[0].lower():
        errors.append(_err(brief, title, "Opções consideradas: Status descartado exige a opção não fazer como Recomendada"))
    return errors


def _check_questions(brief: Path, sections: dict[str, list[Line]]) -> list[str]:
    errors = []
    if "Perguntas em aberto" in sections and len(sections["Perguntas em aberto"]) == 1:
        errors.append(_err(brief, sections["Perguntas em aberto"][0][0],
                           "Perguntas em aberto: vazia (escreva Nenhuma.)"))
    markers = [(n, m) for n, text in _prose(sections) for m in MARKER.findall(text)]
    if len(markers) > MAX_QUESTIONS:
        errors.append(_err(brief, markers[MAX_QUESTIONS][0],
                           f"Perguntas em aberto: mais de cinco perguntas abertas ({len(markers)})"))
    return errors + [_err(brief, n, f"marcador pendente: {m}") for n, m in markers]


def _check_diagnostic(brief: Path, sections: dict[str, list[Line]]) -> list[str]:
    if "Diagnóstico" not in sections:
        return []
    errors, lines = [], sections["Diagnóstico"]
    for label in DIAGNOSTIC:
        found = next(((n, m) for n, text in lines[1:] if (m := re.match(rf"^- {label}:\s*(.*)$", text))), None)
        if found is None:
            errors.append(_err(brief, lines[0][0], f'Diagnóstico: falta a linha "- {label}:"'))
            continue
        n, match = found
        value = match.group(1)
        if label == "Reprodução" and not BACKTICKED.search(value):
            errors.append(_err(brief, n, "Diagnóstico: Reprodução sem comando entre crases"))
        if label == "Causa raiz" and not any(
                CITATION.fullmatch(t.strip("`")) for t in BACKTICKED.findall(value)):
            errors.append(_err(brief, n, "Diagnóstico: Causa raiz sem citação `arquivo:linha`"))
    return errors


def _check_citations(brief: Path, sections: dict[str, list[Line]], root: Path) -> list[str]:
    """Só `arquivo:linha`; caminho solto pode ser arquivo a criar."""
    errors = []
    for n, text in _prose(sections):
        for token in BACKTICKED.findall(text):
            cited = CITATION.fullmatch(token.strip("`"))
            if not cited or cited["path"].startswith("/"):
                continue
            path = cited["path"].rstrip("/")
            # ponytail: só confere o que começa num item real da raiz
            if path.split("/")[0] != ".." and not (root / path.split("/")[0]).exists():
                continue
            target = (root / path).resolve()
            first, last = int(cited["first"]), int(cited["last"] or cited["first"])
            if not target.is_relative_to(root.resolve()):
                errors.append(_err(brief, n, f"cita {token}, fora da raiz"))
            elif not target.exists():
                errors.append(_err(brief, n, f"cita {token}, que não existe"))
            elif target.is_dir():
                errors.append(_err(brief, n, f"cita {token}, que é um diretório"))
            elif first < 1 or last < first:
                errors.append(_err(brief, n, f"cita {token}, linha inválida"))
            elif last > len(target.read_text(encoding="utf-8", errors="replace").splitlines()):
                errors.append(_err(brief, n, f"cita {token}, além do fim do arquivo"))
    return errors


def check(brief: Path, root: Path) -> list[str]:
    """Erros do brief; lista vazia = limpo. `root` é a raiz do repositório."""
    try:
        text = brief.read_text(encoding="utf-8")
    except UnicodeDecodeError:
        return [_err(brief, 0, "arquivo não é UTF-8")]
    lines = list(enumerate(text.splitlines(), start=1))
    errors = []
    if opened := _unfenced(lines)[1]:
        errors.append(_err(brief, opened, "cerca de código aberta, sem fechar"))
    sections = _sections(lines)
    header_errors, status, mode = _check_header(brief, sections)
    errors += header_errors
    errors += _check_sections(brief, sections)
    errors += _check_appetite(brief, sections, mode)
    errors += _check_need(brief, sections)
    errors += _check_market(brief, sections)
    errors += _check_options(brief, sections, status)
    errors += _check_questions(brief, sections)
    errors += _check_diagnostic(brief, sections)
    errors += _check_citations(brief, sections, root)
    return errors


def main(argv: list[str]) -> int:
    if not argv:
        print("uso: check_brief.py <brief.md> [raiz]", file=sys.stderr)
        return 2
    brief = Path(argv[0])
    if not brief.is_file():
        print(f"brief não encontrado: {brief}", file=sys.stderr)
        return 2
    errors = check(brief, Path(argv[1] if len(argv) > 1 else ".").resolve())
    print("\n".join(errors) if errors else "limpo")
    return 1 if errors else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
