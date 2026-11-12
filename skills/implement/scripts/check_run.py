#!/usr/bin/env python3
"""Confere uma execução da skill implement: gatilhos detectáveis no diff,
indicadores de qualidade, impressão digital da árvore e o progress.md.

Uso:
  check_run.py tree [raiz]
  check_run.py triggers <spec.md> [raiz]
  check_run.py quality <spec.md> [raiz]
  check_run.py progress <progress.md> <spec.md> [raiz]
  check_run.py converge <progress.md> <spec.md> [raiz]

Imprime um problema por linha e sai 1, ou imprime "limpo" e sai 0 (`tree` e
`quality` só informam). Arquivo ausente sai 2. Só biblioteca padrão; roda no
python3 3.9 do macOS. O diff é o da árvore contra o HEAD, mais os arquivos não
rastreados; `.agent_plans/` nunca conta.
"""
from __future__ import annotations

import hashlib
import re
import subprocess
import sys
from fnmatch import fnmatch
from pathlib import Path
from typing import NamedTuple

Line = tuple[int, str]  # (número da linha, texto)

PLANS = ".agent_plans"
EXCLUDE = f":(exclude){PLANS}"
SECTIONS = ("Prontidão", "Critérios de aceite", "Tarefas", "Qualidade", "Achados",
            "Escaladas e decisões", "Log")
AC_STATUS = ("passou", "falhou", "pendente")
TASK_STATUS = ("pendente", "em andamento", "concluída", "escalada")
FINDING_RESULT = ("aberto", "corrigido", "refutado", "escalado", "registrado")
VERDICTS = ("confirmado", "refutado", "plausível")
MANIFESTS = ("package.json", "package-lock.json", "yarn.lock", "pnpm-lock.yaml",
             "requirements*.txt", "pyproject.toml", "poetry.lock", "Pipfile*", "go.mod",
             "go.sum", "Cargo.toml", "Cargo.lock", "Gemfile*", "composer.*", "*.csproj")

FENCE = re.compile(r"^\s*(`{3,}|~{3,})")
SEPARATOR = re.compile(r":?-{3,}:?")
MARKER = re.compile(r"\[PRECISA DECISÃO[^\]]*\]")
TITLE = re.compile(r"^# Progresso · spec: \S+")
SCOPE_LINE = re.compile(r"^[-*] (Permitido|Proibido|Orçamento):\s*(.*)$")
BUDGET = re.compile(r"arquivos novos (\d+)")
AC_HEAD = re.compile(r"^### (AC-\d{3})\b")
AC_QUALITY = re.compile(r"^- (AC-Q\d{2})\b")
TASK_HEAD = re.compile(r"^### (T\d+)\b")
TRIGGER_CELL = re.compile(r"(?:(?:G[1-9]|S[1-7]|P[1-4])(?:\s*,\s*)?)+")
DEF = re.compile(r"^(?:async\s+)?(?:def|class)\s+([A-Za-z]\w*)")
EXPORT = re.compile(r"^export\s+(?:default\s+)?(?:async\s+)?"
                    r"(?:function|class|const|let|var|interface|type|enum)\s+(\w+)")
MIGRATION = re.compile(r"(?:^|/)(?:migrations?|alembic)/|migrate|schema\.prisma$|\.sql$", re.I)
SENSITIVE = re.compile(
    r"(?<![a-z])(?:auth(?:entication|orization)?|oauth|login|jwt|permissions?|crypto(?:graphy)?|"
    r"encrypt(?:ion)?|secrets?|terraform|infra(?:structure)?)(?![a-z])|\.github/workflows|"
    r"azure-pipelines|\.gitlab-ci|jenkinsfile|dockerfile|\.env", re.I)
SKIP = re.compile(r"@unittest\.skip|@unittest\.expectedFailure|pytest\.mark\.skip|pytest\.mark\.xfail|"
                  r"skipTest\(|\bxit\(|\.skip\(|\.only\(|t\.Skip\(")
SUPPRESSION = re.compile(r"@ts-ignore|@ts-expect-error|eslint-disable|#\s*noqa|#\s*type:\s*ignore|"
                         r"#\s*pylint:\s*disable|#\s*nosec|--no-verify|nolint")
TEST_DIRS = ("test", "tests", "__tests__", "spec")
TEST_NAMES = ("test_*.py", "*_test.py", "*.test.*", "*.spec.*")


class Change(NamedTuple):
    status: str  # M, A, D ou ? (não rastreado)
    path: str
    added: list[str]
    removed: list[str]


def _git(root: Path, *args: str, literal: bool = False) -> str:
    cmd = ["git", "-c", "core.quotepath=off"] + (["--literal-pathspecs"] if literal else [])
    done = subprocess.run(cmd + ["-C", str(root), *args],
                          capture_output=True, text=True, errors="replace", check=True)
    return done.stdout


def _untracked(root: Path) -> list[str]:
    """Arquivos não rastreados (só arquivos: repositório aninhado e link quebrado ficam de fora)."""
    out = _git(root, "ls-files", "--others", "--exclude-standard", "-z")
    paths = [p for p in out.split("\0") if p and not p.startswith(PLANS + "/")]
    return sorted(p for p in paths if (root / p).is_file())


def _body(root: Path, path: str) -> tuple[list[str], list[str]]:
    added: list[str] = []
    removed: list[str] = []
    in_hunk = False
    for row in _git(root, "diff", "HEAD", "--no-renames", "-U0", "--no-color", "--", path,
                    literal=True).splitlines():
        if row.startswith("@@"):
            in_hunk = True
        elif in_hunk and row[:1] == "+":
            added.append(row[1:])
        elif in_hunk and row[:1] == "-":
            removed.append(row[1:])
    return added, removed


def changes(root: Path) -> list[Change]:
    """Mudanças da árvore contra o HEAD, com as linhas acrescentadas e removidas."""
    tokens = _git(root, "diff", "HEAD", "--no-renames", "--name-status", "-z", "--", ".", EXCLUDE).split("\0")
    result = [Change(code[:1], path, *_body(root, path))
              for code, path in zip(tokens[0::2], tokens[1::2]) if code]
    for path in _untracked(root):
        try:
            lines = (root / path).read_text(encoding="utf-8").splitlines()
        except UnicodeDecodeError:
            lines = []  # binário ou outra codificação: é mudança, sem linhas para ler
        except OSError:
            continue
        result.append(Change("?", path, lines, []))
    return sorted(result, key=lambda c: c.path)


def fingerprint(root: Path) -> str:
    """Impressão digital (12 hex) do que mudou na árvore, sem `.agent_plans/`."""
    digest = hashlib.sha1(_git(root, "diff", "HEAD", "--no-renames", "--", ".", EXCLUDE).encode())
    for path in _untracked(root):
        try:
            digest.update(path.encode() + b"\0" + (root / path).read_bytes())
        except OSError:
            continue
    return digest.hexdigest()[:12]


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


# ---- escopo e gatilhos ----

def _scope(spec: Path) -> dict[str, list[str]]:
    lines = _read(spec) or []
    found: dict[str, list[str]] = {"Permitido": [], "Proibido": [], "Orçamento": []}
    for _, text in _unfenced(lines)[0]:
        if match := SCOPE_LINE.match(text):
            if match.group(1) == "Orçamento":
                found["Orçamento"].append(match.group(2))
            else:
                found[match.group(1)] += re.findall(r"`([^`]+)`", match.group(2))
    return found


def _matches(path: str, entry: str) -> bool:
    if entry.endswith("/"):
        return path.startswith(entry)
    return path == entry or fnmatch(path, entry)


def _is_test(path: str) -> bool:
    parts = path.split("/")
    return any(p in TEST_DIRS for p in parts[:-1]) or any(fnmatch(parts[-1], n) for n in TEST_NAMES)


def _names(rows: list[str]) -> set[str]:
    return {m.group(1) for row in rows if (m := DEF.match(row) or EXPORT.match(row))}


def _budget(spec: Path) -> int | None:
    match = BUDGET.search(" ".join(_scope(spec)["Orçamento"]))
    return int(match.group(1)) if match else None


def triggers(spec: Path, root: Path) -> list[str]:
    """Gatilhos G1 a G7 e G9 (arquivos novos) presentes no diff da árvore."""
    scope, found, new = _scope(spec), [], []
    for change in changes(root):
        path = change.path
        if any(_matches(path, e) for e in scope["Proibido"]):
            found.append(f"G1 {path}: dentro de Proibido")
        elif not any(_matches(path, e) for e in scope["Permitido"]):
            found.append(f"G1 {path}: fora de Permitido")
        if change.status == "D":
            found.append(f"G2 {path}: arquivo apagado ou renomeado")
        gone = _names(change.removed) - _names(change.added)
        if change.status == "M" and gone:
            found.append(f"G2 {path}: símbolo removido: {', '.join(sorted(gone))}")
        if any(fnmatch(path.split("/")[-1], m) for m in MANIFESTS):
            found.append(f"G3 {path}: manifesto ou lockfile alterado")
        if MIGRATION.search(path):
            found.append(f"G4 {path}: migração ou schema de banco")
        if SENSITIVE.search(path):
            found.append(f"G5 {path}: caminho sensível")
        if _is_test(path):
            if change.status == "D" or (change.status == "M" and any(r.strip() for r in change.removed)):
                found.append(f"G6 {path}: teste existente apagado ou com linha removida")
            if any(SKIP.search(a) for a in change.added):
                found.append(f"G6 {path}: skip acrescentado")
        if any(SUPPRESSION.search(a) for a in change.added):
            found.append(f"G7 {path}: supressão acrescentada")
        if change.status in ("A", "?"):
            new.append(path)
    limit = _budget(spec)
    if limit is not None:
        found += [f"G9 {p}: arquivo novo acima do orçamento ({limit})" for p in new[limit:]]
    return found


def quality(spec: Path, root: Path) -> list[str]:
    """Indicadores que saem do diff; a ferramenta calcula, o agente interpreta."""
    done = changes(root)
    limit = _budget(spec)
    return [
        f"arquivos alterados: {len(done)}",
        f"arquivos novos (orçamento {'—' if limit is None else limit}): "
        f"{sum(c.status in ('A', '?') for c in done)}",
        f"linhas adicionadas: {sum(len(c.added) for c in done)}",
        f"linhas removidas: {sum(len(c.removed) for c in done)}",
        f"supressões novas: {sum(bool(SUPPRESSION.search(a)) for c in done for a in c.added)}",
    ]


# ---- progress.md ----

def _err(path: Path, line: int, msg: str) -> str:
    return f"{path.name}:{line}: {msg}" if line else f"{path.name}: {msg}"


def _spec_ids(spec: Path) -> tuple[list[str], list[str]]:
    acs, tasks = [], []
    for _, text in _unfenced(_read(spec) or [])[0]:
        if m := AC_HEAD.match(text) or AC_QUALITY.match(text):
            acs.append(m.group(1))
        elif m := TASK_HEAD.match(text):
            tasks.append(m.group(1))
    return acs, tasks


def _manual_acs(spec: Path) -> set[str]:
    manual, current = set(), ""
    for _, text in _unfenced(_read(spec) or [])[0]:
        if head := AC_HEAD.match(text):
            current = head.group(1)
        elif text.startswith("- Tipo:") and current and text.split(":", 1)[1].strip() == "manual":
            manual.add(current)
    return manual


def _table(prog: Path, sections: dict[str, list[Line]], name: str, width: int,
           errors: list[str]) -> list[tuple[int, list[str]]]:
    rows = []
    for n, cells in _rows(sections.get(name, [])):
        if len(cells) < width:
            errors.append(_err(prog, n, f"{name}: linha incompleta"))
        else:
            rows.append((n, cells))
    return rows


def _check_ids(prog: Path, rows: list[tuple[int, list[str]]], known: list[str], kind: str,
               statuses: tuple[str, ...]) -> list[str]:
    errors = [_err(prog, n, f"desconhecido: {c[0]}") for n, c in rows if c[0] not in known]
    errors += [_err(prog, n, f"status inválido: {c[1]}") for n, c in rows if c[1] not in statuses]
    seen = {c[0] for _, c in rows}
    return errors + [_err(prog, 0, f"{kind} faltando: {i}") for i in known if i not in seen]


def progress(prog: Path, spec: Path, root: Path) -> list[str]:
    """Erros de formato do progress.md contra a spec; lista vazia = limpo."""
    lines = _read(prog)
    if lines is None:
        return [_err(prog, 0, "arquivo não é UTF-8")]
    errors = []
    if opened := _unfenced(lines)[1]:
        errors.append(_err(prog, opened, "cerca de código aberta, sem fechar"))
    sections = _sections(lines)
    if not any(TITLE.match(t) for _, t in sections[""]):
        errors.append(_err(prog, 0, 'título: falta "# Progresso · spec: <caminho>"'))
    errors += [_err(prog, 0, f"seção ausente: {name}") for name in SECTIONS if name not in sections]
    acs, tasks = _spec_ids(spec)
    ready = _table(prog, sections, "Prontidão", 2, errors)
    criteria = _table(prog, sections, "Critérios de aceite", 4, errors)
    task_rows = _table(prog, sections, "Tarefas", 4, errors)
    findings = _table(prog, sections, "Achados", 6, errors)
    if criteria or "Critérios de aceite" in sections:
        errors += _check_ids(prog, criteria, acs, "AC", AC_STATUS)
    if task_rows or "Tarefas" in sections:
        errors += _check_ids(prog, task_rows, tasks, "tarefa", TASK_STATUS)
    for n, c in findings:
        if c[2] not in VERDICTS:
            errors.append(_err(prog, n, f"status inválido: Veredito {c[2]}"))
        if c[5] not in FINDING_RESULT:
            errors.append(_err(prog, n, f"status inválido: Resultado {c[5]}"))
        if c[3] != "—" and not TRIGGER_CELL.fullmatch(c[3]):
            errors.append(_err(prog, n, f"gatilho inválido: {c[3]}"))
    return errors + ([_err(prog, 0, "Prontidão: sem linhas")] if "Prontidão" in sections and not ready else [])


def _markers(path: Path) -> list[str]:
    return [f"convergência: marcador pendente em {path.name}:{n}: {m}"
            for n, text in _unfenced(_read(path) or [])[0] for m in MARKER.findall(text)]


def converge(prog: Path, spec: Path, root: Path) -> list[str]:
    """Progress limpo mais as condições mecânicas da seção 9 do design."""
    errors = progress(prog, spec, root)
    lines = _read(prog)
    if lines is None:
        return errors
    sections, tree = _sections(lines), fingerprint(root)
    for _, c in _rows(sections.get("Prontidão", [])):
        if len(c) >= 2 and c[1] != "ok":
            errors.append(f"convergência: prontidão: {c[0]} = {c[1]}")
    manual = _manual_acs(spec)
    for _, c in _rows(sections.get("Critérios de aceite", [])):
        if len(c) < 4 or (c[0] in manual and c[1] == "pendente"):
            continue  # AC manual espera o ok do humano; não é falha
        if c[1] != "passou" or c[2] in ("", "—"):
            errors.append(f"convergência: AC sem evidência: {c[0]} ({c[1]})")
        elif c[3] != tree:
            errors.append(f"convergência: evidência anterior à última alteração: {c[0]}")
    for _, c in _rows(sections.get("Tarefas", [])):
        if len(c) >= 2 and c[1] != "concluída":
            errors.append(f"convergência: tarefa não concluída: {c[0]} ({c[1]})")
    for _, c in _rows(sections.get("Achados", [])):
        if len(c) < 6:
            continue
        ident, verdict, gate, result = c[0], c[2], c[3], c[5]
        if result in ("aberto", "escalado"):
            errors.append(f"convergência: achado sem resolução: {ident} ({result})")
        elif result == "corrigido" and gate != "—":
            errors.append(f"convergência: achado com gatilho {gate} não pode terminar corrigido: {ident}")
        elif result == "refutado" and verdict != "refutado":
            errors.append(f"convergência: achado {ident} refutado sem veredito refutado")
    errors += _markers(prog) + _markers(spec)
    errors += [f"convergência: escopo: {t}" for t in triggers(spec, root) if t.startswith("G1 ")]
    return errors


# ---- CLI ----

USAGE = ("uso: check_run.py tree [raiz] | triggers|quality <spec.md> [raiz] | "
         "progress|converge <progress.md> <spec.md> [raiz]")


def _run(command: str, files: list[Path], root: Path) -> tuple[list[str], int]:
    """Linhas a imprimir e o exit quando o comando só informa; exit 1 se há problema."""
    if command == "tree":
        return [fingerprint(root)], 0
    if command == "quality":
        return quality(files[0], root), 0
    errors = {"triggers": lambda: triggers(files[0], root),
              "progress": lambda: progress(files[0], files[1], root),
              "converge": lambda: converge(files[0], files[1], root)}[command]()
    return errors or ["limpo"], 1 if errors else 0


def main(argv: list[str]) -> int:
    command, args = (argv[0], argv[1:]) if argv else ("", [])
    arity = {"tree": 0, "triggers": 1, "quality": 1, "progress": 2, "converge": 2}
    if command not in arity or len(args) < arity[command]:
        print(USAGE, file=sys.stderr)
        return 2
    files = [Path(a) for a in args[:arity[command]]]
    for f in files:
        if not f.is_file():
            print(f"arquivo não encontrado: {f}", file=sys.stderr)
            return 2
    root = Path(args[arity[command]] if len(args) > arity[command] else ".").resolve()
    try:
        lines, code = _run(command, files, root)
    except (subprocess.CalledProcessError, OSError) as exc:
        print(f"erro ao ler o repositório em {root}: {getattr(exc, 'stderr', '') or exc}".strip(),
              file=sys.stderr)
        return 2
    print("\n".join(lines))
    return code


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
