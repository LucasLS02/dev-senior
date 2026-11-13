#!/usr/bin/env python3
"""Hook PreToolUse (Bash): `gh api` de leitura passa, de escrita pede aprovação.

Escrita é -X/--method diferente de GET, -f/-F/--field/--raw-field e --input num
endpoint REST, e `gh api graphql` cuja consulta tem `mutation` ou não é um texto
literal que se possa ler. O hook nunca libera nada: só devolve "ask" e deixa a
liberação da leitura para a regra `Bash(gh api:*)` da lista de permissões.
Só biblioteca padrão; roda no python3 3.9 do macOS.
"""
from __future__ import annotations

import json
import re
import shlex
import sys

TAKES_VALUE = {"-H", "--header", "-q", "--jq", "-t", "--template", "--cache", "--hostname",
               "-X", "--method", "-f", "-F", "--field", "--raw-field", "--input", "-p", "--preview"}
FIELD_FLAGS = {"-f", "-F", "--field", "--raw-field"}
GRAPHQL_TEXT = re.compile(r"^\s*(query\b|\{)", re.I)
ENV = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*=")
HEREDOC = re.compile(r"<<-?\s*['\"]?(\w+)['\"]?")


def _strip_heredocs(command: str) -> str:
    """Tira o corpo dos heredocs: é texto para outro comando, não comando."""
    out, tag = [], ""
    for line in command.split("\n"):
        if tag:
            tag = "" if line.strip() == tag else tag
            continue
        out.append(line)
        if found := HEREDOC.search(line):
            tag = found.group(1)
    return "\n".join(out)


def _segments(command: str) -> list[str]:
    """Pedaços do comando separados por && || ; | ( ) crase e quebra de linha, fora de aspas."""
    command = _strip_heredocs(command)
    out, cur, quote = [], [], ""
    for i, ch in enumerate(command):
        if ch == "\n" and command[i - 1:i] == "\\" and quote != "'":
            cur.pop()  # continuação de linha: \ + quebra não separa comandos
        elif quote:
            cur.append(ch)
            quote = "" if ch == quote else quote
        elif ch in "'\"":
            quote = ch
            cur.append(ch)
        elif ch in "&|;()`\n":
            out.append("".join(cur))
            cur = []
        else:
            cur.append(ch)
    out.append("".join(cur))
    return [s.strip() for s in out if s.strip()]


def _option(tok: str) -> tuple[str, str | None]:
    """Separa `--method=PUT` e `-XPOST` em (flag, valor); sem valor colado, o valor é None."""
    if tok.startswith("--") and "=" in tok:
        flag, value = tok.split("=", 1)
        return flag, value
    if len(tok) > 2 and tok[0] == "-" and tok[1] != "-" and tok[:2] in TAKES_VALUE:
        return tok[:2], tok[2:]
    return tok, None


def _api_verdict(args: list[str]) -> str | None:
    endpoint, fields, i = "", [], 0
    while i < len(args):
        flag, value = _option(args[i])
        if flag in TAKES_VALUE and value is None:
            i += 1
            value = args[i] if i < len(args) else ""
        if flag in ("-X", "--method") and value.upper() != "GET":
            return f"gh api com método {value.upper() or '?'}"
        if flag == "--input":
            return "gh api com --input"
        if flag in FIELD_FLAGS:
            fields.append(value)
        elif not flag.startswith("-") and not endpoint:
            endpoint = flag
        i += 1
    if endpoint != "graphql":
        return "gh api com campo -f/-F (vira POST)" if fields else None
    queries = [f.split("=", 1)[1] for f in fields if f.startswith("query=")]
    if not queries or not all(GRAPHQL_TEXT.match(q) for q in queries):
        return "gh api graphql sem consulta literal legível"
    return "gh api graphql com mutation" if any("mutation" in q.lower() for q in queries) else None


def verdict(command: str) -> str | None:
    """Motivo para pedir aprovação, ou None se nenhum `gh api` do comando escreve."""
    for seg in _segments(command):
        try:
            toks = shlex.split(seg)
        except ValueError:
            if re.search(r"\bgh\s+api\b", seg):
                return "gh api com aspas que não consigo ler"
            continue
        while toks and ENV.match(toks[0]):
            toks = toks[1:]
        if toks[:2] == ["gh", "api"] and (reason := _api_verdict(toks[2:])):
            return reason
    return None


def main() -> int:
    try:
        command = json.load(sys.stdin)["tool_input"]["command"]
    except (ValueError, KeyError, TypeError):
        return 0
    if reason := verdict(command):
        print(json.dumps({"hookSpecificOutput": {
            "hookEventName": "PreToolUse",
            "permissionDecision": "ask",
            "permissionDecisionReason": f"{reason}: pode escrever no GitHub",
        }}))
    return 0


if __name__ == "__main__":
    sys.exit(main())
