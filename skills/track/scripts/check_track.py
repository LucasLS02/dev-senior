#!/usr/bin/env python3
"""Cálculos locais de acompanhamento; nunca acessa a rede."""
from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
from pathlib import Path

LEAK = re.compile(r"/Users/|/home/|[A-Za-z]:\\|ghp_[A-Za-z0-9]{20,}|github_pat_|AKIA[0-9A-Z]{16}|-----BEGIN")
INTERNAL = re.compile(r"\.agent_plans/|\b(?:RV-\d+|[GSP]\d+)\b|\b[\w./-]+\.[\w]+:\d+\b")
PATH = re.compile(r"(?<![\w:/])(?:\.{1,2}/|/|[\w.-]+/)[\w./-]+")


def section_hash(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def section_conflict(remote: str, desired: str, previous_hash: str | None) -> bool:
    return remote != desired and ((bool(previous_hash) and section_hash(remote) != previous_hash) or (not previous_hash and bool(remote)))


def has_leak(text: str) -> bool:
    without_urls = re.sub(r"https?://\S+", "", text)
    return bool(LEAK.search(text) or INTERNAL.search(without_urls) or PATH.search(without_urls))


def validate_tracker(text: str) -> list[str]:
    errors = []
    required = {"Contexto": ("Ferramenta", "Projeto", "Repositório", "Pasta", "Marcador"),
                "Vínculos": ("Story",), "Autorização": ("Rotina", "Escopo", "Evidência"),
                "Estado observado": ("Hash da seção",), "Log": ()}
    for heading, fields in required.items():
        if not re.search(r"^## " + re.escape(heading) + r"\s*$", text, re.M):
            errors.append(f"seção ausente: {heading}")
        body = _section(text, heading)
        for field in fields:
            if not re.search(r"^- " + re.escape(field) + r":\s*\S", body, re.M):
                errors.append(f"campo ausente: {heading}/{field}")
    auth = _section(text, "Autorização")
    if re.search(r"^- Rotina: concedida\s*$", auth, re.M):
        for field in ("Escopo", "Evidência"):
            if re.search(r"^- " + field + r":\s*(?:—|-|pendente)\s*$", auth, re.M):
                errors.append(f"autorização sem {field.lower()}")
    elif not re.search(r"^- Rotina: não concedida\s*$", auth, re.M):
        errors.append("autorização inválida")
    return errors


def _section(text: str, name: str) -> str:
    match = re.search(r"^## " + re.escape(name) + r"\s*\n(.*?)(?=^## |\Z)", text, re.M | re.S)
    return match.group(1) if match else ""


def _rows(text: str) -> list[list[str]]:
    rows = [line.strip().strip("|").split("|") for line in text.splitlines() if line.strip().startswith("|")]
    return [[cell.strip() for cell in row] for row in rows[2:]]


def local_events(spec: str, progress: str, converged: bool = False) -> list[str]:
    if not re.search(r"^Status:\s*aprovado(?:\s|·|$)", spec, re.M):
        return []
    readiness = _rows(_section(progress, "Prontidão"))
    required = {"check_spec.py limpo", "Status aprovado", "Sem marcador pendente", "Árvore limpa"}
    if not required.issubset({row[0] for row in readiness}) or any(len(row) < 2 or row[1] != "ok" for row in readiness):
        return []
    events = ["início"]
    escalations = _section(progress, "Escaladas e decisões")
    blocks = re.split(r"(?=^### Escalada \d+\s*$)", escalations, flags=re.M)
    pending = False
    seen_escalations: set[str] = set()
    for block in blocks:
        match = re.search(r"^### Escalada (\d+)\s*$", block, re.M)
        if not match:
            if block.strip() and block.strip() != "Nenhuma.":
                pending = True  # legado ou formato desconhecido: não supor decisão
            continue
        number = match.group(1)
        if number in seen_escalations:
            raise ValueError(f"escalada duplicada: {number}")
        seen_escalations.add(number)
        decision = re.search(r"^Decisão:\s*(.+)$", block, re.M)
        unresolved = not decision or decision.group(1).strip() == "pendente"
        pending |= unresolved
        gate = re.search(r"^Gatilho:\s*([^·\n]+)", block, re.M)
        external = (gate and re.search(r"\b(?:S1|S3)\b", gate.group(1))) or re.search(r"^Dependência externa:\s*sim\s*$", block, re.M | re.I)
        if external:
            events.append(f"impedimento {number}")
            if not unresolved:
                events.append(f"decisão {number}")
    tasks = _rows(_section(progress, "Tarefas"))
    expected = set(re.findall(r"^### (T\d+)\b", _section(spec, "Tarefas"), re.M))
    observed = [row[0] for row in tasks if row]
    if converged and expected and set(observed) == expected and len(observed) == len(expected) and all(len(row) > 1 and row[1] == "concluída" for row in tasks) and not pending:
        events.append("entrega")
    return events


def missing_events(events: list[str], comments: list[str], marker: str) -> list[str]:
    footers = {match.group(1).strip() for comment in comments
               for match in re.finditer(r"^— fluxo: (.+?)\s*$", comment, re.M)}
    return [event for event in events if f"{marker} {event}" not in footers]


def reconcile(desired: dict, remote: dict, previous_hash: str | None) -> dict:
    """Compara estado desejado e leitura remota, sem executar alterações."""
    for name, obj, fields in (("desejado", desired, {"section": str, "status": str, "blocked": bool, "events": list, "marker": str}),
                              ("remoto", remote, {"section": str, "status": str, "blocked": bool, "comments": list})):
        if not isinstance(obj, dict) or any(not isinstance(obj.get(key), kind) for key, kind in fields.items()):
            raise ValueError(f"estado {name} incompleto ou inválido")
    if not desired["marker"] or not all(isinstance(x, str) for x in desired["events"] + remote["comments"]):
        raise ValueError("marcador, eventos ou comentários inválidos")
    section = ("igual" if desired["section"] == remote["section"] else
               "conflito" if section_conflict(remote["section"], desired["section"], previous_hash) else "alterar")
    return {"section": section, "status": desired["status"] != remote["status"],
            "blocked": desired["blocked"] != remote["blocked"],
            "events": missing_events(desired["events"], remote["comments"], desired["marker"])}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)
    events = sub.add_parser("events")
    events.add_argument("spec", type=Path)
    events.add_argument("progress", type=Path)
    events.add_argument("--converged", action="store_true", help="somente após check_run.py converge sair limpo")
    events.add_argument("--comments", type=Path, help="JSON: lista de textos lidos do remoto")
    events.add_argument("--marker", help="marcador estável da tarefa, obrigatório com --comments")
    leak = sub.add_parser("leak")
    leak.add_argument("file", type=Path)
    tracker = sub.add_parser("validate")
    tracker.add_argument("file", type=Path)
    diff = sub.add_parser("diff")
    diff.add_argument("file", type=Path, help="JSON com desired, remote e previous_hash")
    args = parser.parse_args()
    try:
        if args.command == "leak":
            found = has_leak(args.file.read_text(encoding="utf-8"))
            print("vazamento" if found else "limpo")
            return int(found)
        if args.command == "validate":
            errors = validate_tracker(args.file.read_text(encoding="utf-8"))
            print("\n".join(errors) if errors else "limpo")
            return int(bool(errors))
        if args.command == "diff":
            data = json.loads(args.file.read_text(encoding="utf-8"))
            if not isinstance(data, dict) or not isinstance(data.get("previous_hash"), (str, type(None))):
                raise ValueError("JSON de comparação inválido")
            print(json.dumps(reconcile(data.get("desired"), data.get("remote"), data.get("previous_hash")), ensure_ascii=False))
            return 0
        result = local_events(args.spec.read_text(encoding="utf-8"), args.progress.read_text(encoding="utf-8"), args.converged)
        if args.comments:
            if not args.marker or not re.fullmatch(r"fluxo-[a-f0-9]{64}", args.marker):
                raise ValueError("--comments exige --marker fluxo-<sha256>")
            comments = json.loads(args.comments.read_text(encoding="utf-8"))
            if not isinstance(comments, list) or not all(isinstance(c, str) for c in comments):
                raise ValueError("comentários devem ser uma lista de textos")
            result = missing_events(result, comments, args.marker)
        print(json.dumps(result, ensure_ascii=False))
        return 0
    except (OSError, UnicodeError, ValueError) as exc:
        print(f"erro: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    sys.exit(main())
