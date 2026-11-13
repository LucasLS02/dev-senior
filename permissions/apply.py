#!/usr/bin/env python3
"""Grava as listas de rules.py nos arquivos de cada ferramenta, com cópia de segurança.

Uso: python3 permissions/apply.py [--dry-run]

Mescla sem apagar o que já existe e pode rodar de novo: Claude pessoal e work
(settings.json), Codex (rules/dev-senior.rules), OpenCode (opencode.jsonc) e
Antigravity (antigravity-cli/settings.json). Só biblioteca padrão; roda no
python3 3.9 do macOS.
"""
from __future__ import annotations

import copy
import json
import re
import shutil
import sys
import time
from pathlib import Path

import rules

HOME = Path.home()
HOOK = Path(__file__).with_name("gh_api_guard.py")
GH_API_WRITE_FLAGS = (" -f", " -F", " -X", " --method", " --field", " --raw-field", " --input")
GH_API_FLAG_PATTERNS = ["gh api * -f *", "gh api * -F *", "gh api * -X *", "gh api * --method *",
                        "gh api * --field *", "gh api * --raw-field *", "gh api * --input *"]
BEGIN, END = "// dev-senior:begin", "// dev-senior:end"
ANCHOR = '"rm *": "deny"'


def _union(current: list[str], new: list[str]) -> list[str]:
    return current + [x for x in new if x not in current]


def merge_claude(settings: dict, hook_command: str) -> dict:
    out = copy.deepcopy(settings)
    perms = out.setdefault("permissions", {})
    perms["allow"] = _union(perms.get("allow", []), [f"Bash({c}:*)" for c in rules.ALL])
    pre = out.setdefault("hooks", {}).setdefault("PreToolUse", [])
    if hook_command not in json.dumps(pre):
        pre.append({"matcher": "Bash", "hooks": [{"type": "command", "command": hook_command}]})
    return out


def merge_antigravity(settings: dict) -> dict:
    out = copy.deepcopy(settings)
    perms = out.setdefault("permissions", {})
    perms["allow"] = _union(perms.get("allow", []), [f"command({c})" for c in rules.ALL])
    write = "command(regex:gh api .*(" + "|".join(GH_API_WRITE_FLAGS) + ").*)"
    perms["ask"] = _union(perms.get("ask", []), [write])
    return out


def codex_rules() -> str:
    def row(cmd: str, decision: str) -> str:
        pattern = ", ".join(json.dumps(t) for t in cmd.split())
        return f'prefix_rule(pattern=[{pattern}], decision="{decision}")'
    lines = [row(c, "allow") for c in rules.ALL if c != "gh api"]
    return "\n".join(lines + [row("gh api", "prompt") + "  # o Codex não tem hook"]) + "\n"


def _opencode_block(existing: str) -> list[str]:
    entries: dict[str, str] = {}
    for cmd in rules.ALL:
        entries[cmd] = entries[f"{cmd} *"] = "allow"
    for cmd in rules.ASK:
        if cmd != "rm":  # o opencode.jsonc já nega `rm *`
            entries[cmd] = entries[f"{cmd} *"] = "ask"
    entries.update({p: "ask" for p in GH_API_FLAG_PATTERNS})
    lines = [f'      "{k}": "{v}",' for k, v in entries.items() if f'"{k}":' not in existing]
    return [f"      {BEGIN}", *lines, f"      {END}"]


def merge_opencode(text: str) -> str:
    pattern = re.compile(rf"^ *{re.escape(BEGIN)}.*?^ *{re.escape(END)}\n", re.M | re.S)
    bare = pattern.sub("", text)
    block = "\n".join(_opencode_block(bare)) + "\n"
    if pattern.search(text):
        return pattern.sub(lambda _: block, text, count=1)
    at = bare.find(ANCHOR)
    if at < 0:
        raise ValueError(f"opencode.jsonc sem a linha {ANCHOR}: não sei onde inserir")
    start = bare.rfind("\n", 0, at) + 1
    return bare[:start] + block + bare[start:]


def _write(path: Path, text: str) -> None:
    tmp = path.with_name(path.name + ".tmp")
    tmp.write_text(text, encoding="utf-8")
    tmp.replace(path)


def _json_edit(path: Path, fn) -> tuple[str, str]:
    old = path.read_text(encoding="utf-8")
    return old, json.dumps(fn(json.loads(old)), indent=2, ensure_ascii=False) + "\n"


def main(argv: list[str]) -> int:
    dry = "--dry-run" in argv
    hook = f"python3 {HOOK}"
    jobs = [
        (HOME / ".claude/settings.json", lambda p: _json_edit(p, lambda d: merge_claude(d, hook))),
        (HOME / ".claude-work/settings.json", lambda p: _json_edit(p, lambda d: merge_claude(d, hook))),
        (HOME / ".gemini/antigravity-cli/settings.json", lambda p: _json_edit(p, merge_antigravity)),
        (HOME / ".config/opencode/opencode.jsonc",
         lambda p: (p.read_text(encoding="utf-8"), merge_opencode(p.read_text(encoding="utf-8")))),
        (HOME / ".codex/rules/dev-senior.rules",
         lambda p: (p.read_text(encoding="utf-8") if p.exists() else "", codex_rules())),
    ]
    backup = HOME / ".Trash" / f"permissions-backup-{time.strftime('%Y%m%d-%H%M%S')}"
    for path, build in jobs:
        try:
            old, new = build(path)
        except (OSError, ValueError) as exc:
            print(f"ERRO {path}: {exc}", file=sys.stderr)
            return 1
        print(f"{'igual    ' if old == new else 'muda     '}{path}")
        if dry or old == new:
            continue
        if path.exists():
            (backup / path.relative_to(HOME)).parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(path, backup / path.relative_to(HOME))
        _write(path, new)
    if not dry:
        print(f"cópias de segurança em {backup}")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
