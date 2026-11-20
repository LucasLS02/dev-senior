#!/usr/bin/env python3
"""Simulador isolado de gh para avaliação de track; estado em TRACK_GH_STATE."""
import json
import os
import sys
from pathlib import Path

state_path = Path(os.environ["TRACK_GH_STATE"])
state = json.loads(state_path.read_text()) if state_path.exists() else {"issues": [], "calls": []}
args = sys.argv[1:]
state["calls"].append(args)


def option(name, default=None):
    return args[args.index(name) + 1] if name in args and args.index(name) + 1 < len(args) else default


def body():
    path = option("--body-file", option("-F"))
    return Path(path).read_text() if path else option("--body", option("-b", ""))


def save():
    state_path.write_text(json.dumps(state, ensure_ascii=False))


def item():
    for arg in args[2:]:
        if arg.startswith("-"):
            continue
        idx = args.index(arg)
        if idx > 0 and args[idx - 1] in ("-R", "--repo", "--json", "-F", "--body-file", "-b", "--body", "-t", "--title", "--add-label", "--remove-label"):
            continue
        target = arg.rstrip("/").split("/")[-1]
        for i in state["issues"]:
            if str(i["number"]) == target or i["url"].rstrip("/").endswith(f"/issues/{target}"):
                return i
    target = args[2].rstrip("/").split("/")[-1]
    return next(i for i in state["issues"] if str(i["number"]) == target)


try:
    if "--help" in args or "-h" in args:
        print("--parent --add-blocked-by --body-file")
    elif args[:1] == ["version"] or "--version" in args:
        print("gh version 2.65.0 (simulado)")
    elif args[:2] == ["auth", "status"]:
        print("Autenticado (simulado)")
    elif args[:2] == ["repo", "view"]:
        print(json.dumps({"nameWithOwner": "example/project", "url": "https://github.com/example/project"}))
    elif args[:2] == ["label", "list"]:
        print(json.dumps([{"name": name, "description": ""} for name in ("em andamento", "em review", "bloqueado")]))
    elif args[:2] == ["issue", "list"]:
        print(json.dumps(state["issues"], ensure_ascii=False))
    elif args[:2] == ["issue", "view"]:
        print(json.dumps(item(), ensure_ascii=False))
    elif args[:2] == ["issue", "create"]:
        number = len(state["issues"]) + 1
        issue = {"number": number, "url": f"https://github.com/example/project/issues/{number}",
                 "title": option("--title", option("-t", "")), "body": body(), "labels": [], "comments": []}
        state["issues"].append(issue)
        print(issue["url"])
    elif args[:2] == ["issue", "edit"]:
        issue = item()
        if any(flag in args for flag in ("--body-file", "-F", "--body", "-b")):
            issue["body"] = body()
        for i, arg in enumerate(args[:-1]):
            if arg in ("--add-label", "-l"):
                name = args[i + 1]
                issue["labels"] = [label for label in issue["labels"] if label["name"] != name]
                issue["labels"].append({"name": name})
            elif arg in ("--remove-label",):
                name = args[i + 1]
                issue["labels"] = [label for label in issue["labels"] if label["name"] != name]
        print(issue["url"])
    elif args[:2] == ["issue", "comment"]:
        issue = item()
        issue["comments"].append({"body": body()})
        print(issue["url"] + "#issuecomment-1")
    elif args[:2] == ["pr", "view"]:
        print(json.dumps({"url": "https://github.com/example/project/pull/1"}))
    else:
        raise ValueError("comando simulado não implementado: " + " ".join(args))
except (ValueError, StopIteration, OSError, IndexError) as exc:
    print(f"gh falso: {exc}", file=sys.stderr)
    save()
    sys.exit(1)
save()
