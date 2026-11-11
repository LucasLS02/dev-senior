#!/usr/bin/env python3
"""Confere o formato de um findings.md e, com um gabarito, pontua os achados.

Uso: python3 tests/score_findings.py <findings.md> [--root DIR]
         [--expected TSV] [--expect-coverage CAMINHO]...

Sai 0 com o formato limpo e, havendo gabarito, recall >= 0,8 sem isca
confirmada; sai 1 nos demais casos. O formato está em
skills/review-diff/references/achados.md.
"""
from __future__ import annotations  # roda no python3 3.9 do macOS

import argparse
import re
import sys
from collections import Counter
from pathlib import Path

REQUIRED = ("id", "lente", "severidade", "local", "problema", "viola", "evidência",
            "impacto", "verificação", "correção", "gatilho", "status")
# (nome no contrato, chave no dict do achado, valores aceitos)
CHECKED = (
    ("lente", "lente", {"requisito", "correção", "testes", "conformidade",
                        "segurança", "desempenho", "manutenção"}),
    ("severidade", "severidade", {"crítico", "alto", "médio", "baixo"}),
    ("veredito", "veredito", {"confirmado", "refutado", "plausível"}),
    ("método", "metodo", {"teste", "reprodução", "inspeção"}),
    ("status", "status", {"aberto", "corrigido", "escalado", "registrado"}),
)
MIN_RECALL = 0.8
# Achado mais largo que isso não casa com o gabarito: cobre tanto código que
# não prova ter achado o problema. Vai para "largos", para julgamento humano.
MAX_SPAN = 10

# ponytail: regex no lugar de parser YAML; o contrato fixa mapas de uma linha.
BLOCK = re.compile(r"^```yaml\n(.*?)^```", re.M | re.S)
KEY = re.compile(r"^([^\s:#][^:]*):(.*)$")
LOCATION = re.compile(r"[\w./-]*[A-Za-z][\w./-]*:\d+")
COVERAGE = re.compile(r"^## Cobertura\s*$", re.M)
Place = tuple[str, int, int]


def _fields(body: str) -> dict[str, str]:
    """Campos de topo de um bloco; linhas indentadas continuam o campo anterior."""
    fields: dict[str, str] = {}
    key = None
    for line in body.splitlines():
        match = KEY.match(line)
        if match:
            key = match.group(1).strip()
            fields[key] = match.group(2).strip()
        elif key and line.strip():
            fields[key] += "\n" + line.strip()
    return fields


def _get(mapping: str, name: str) -> str | None:
    match = re.search(rf"{name}:\s*([^,}}]+)", mapping)
    return match.group(1).strip() if match else None


def _lines(spec: str | None) -> tuple[int | None, int | None]:
    match = re.fullmatch(r"(\d+)(?:\s*-\s*(\d+))?", (spec or "").strip())
    if not match:
        return None, None
    start = int(match.group(1))
    return start, int(match.group(2) or start)


def parse_findings(text: str) -> list[dict]:
    findings = []
    for body in BLOCK.findall(text):
        fields = _fields(body)
        local, check = fields.get("local", ""), fields.get("verificação", "")
        inicio, fim = _lines(_get(local, "linhas"))
        findings.append({
            "id": fields.get("id"),
            "lente": fields.get("lente"),
            "severidade": fields.get("severidade"),
            "arquivo": _get(local, "arquivo"),
            "inicio": inicio,
            "fim": fim,
            "veredito": _get(check, "veredito"),
            "metodo": _get(check, "método"),
            "status": fields.get("status"),
            "evidencia": fields.get("evidência", ""),
            "campos": fields,
        })
    return findings


def check_format(text: str, findings: list[dict], root: Path | None) -> list[str]:
    errors = []
    if not COVERAGE.search(text):
        errors.append("arquivo: falta a seção ## Cobertura")
    seen = set()
    for n, f in enumerate(findings, 1):
        tag = f["id"] or f"bloco {n}"
        missing = [k for k in REQUIRED if k not in f["campos"]]
        if missing:
            errors.append(f"{tag}: faltam os campos {', '.join(missing)}")
        if not re.fullmatch(r"RV-\d{3}", f["id"] or ""):
            errors.append(f"{tag}: id fora do formato RV-000")
        elif f["id"] in seen:
            errors.append(f"{tag}: id repetido")
        seen.add(f["id"])
        for name, key, allowed in CHECKED:
            if f[key] not in allowed:
                errors.append(f"{tag}: {name} '{f[key]}' fora do contrato")
        if not LOCATION.search(f["evidencia"]):
            errors.append(f"{tag}: evidência sem arquivo:linha")
        if not f["arquivo"] or f["inicio"] is None:
            errors.append(f"{tag}: local sem arquivo ou linhas")
        elif root is not None:
            path = root / f["arquivo"]
            if not path.is_file():
                errors.append(f"{tag}: {f['arquivo']} não existe")
            elif f["fim"] > len(path.read_text().splitlines()):
                errors.append(f"{tag}: linhas além do fim de {f['arquivo']}")
    return errors


def parse_expected(text: str) -> list[dict]:
    expected = []
    for line in text.splitlines():
        if not line.strip() or line.startswith("#"):
            continue
        cols = line.split("\t")
        if len(cols) < 3 or cols[1] not in {"plantado", "isca"}:
            raise ValueError(f"linha do gabarito inválida: {line!r}")
        places: list[Place] = []
        for loc in cols[2].split("|"):
            arquivo, _, spec = loc.rpartition(":")
            inicio, fim = _lines(spec)
            if not arquivo or inicio is None or fim is None:
                raise ValueError(f"local inválido no gabarito: {loc!r}")
            places.append((arquivo, inicio, fim))
        expected.append({"id": cols[0], "tipo": cols[1], "locais": places})
    return expected


def _hits(finding: dict, places: list[Place]) -> bool:
    return any(finding["arquivo"] == arquivo
               and finding["inicio"] <= fim and inicio <= finding["fim"]
               for arquivo, inicio, fim in places)


def score(findings: list[dict], expected: list[dict]) -> dict:
    located = [f for f in findings
               if f["veredito"] == "confirmado" and f["inicio"] is not None]
    wide = [f["id"] for f in located if f["fim"] - f["inicio"] + 1 > MAX_SPAN]
    confirmed = [f for f in located if f["id"] not in wide]
    planted = [e for e in expected if e["tipo"] == "plantado"]
    found, missed, bait_hits, duplicates, matched = 0, [], [], {}, set()
    for e in expected:
        if e["tipo"] == "isca":
            # largo também conta: a tolerância de largura é só para a recall
            if any(_hits(f, e["locais"]) for f in located):
                bait_hits.append(e["id"])
            continue
        hits = [f["id"] for f in confirmed if _hits(f, e["locais"])]
        matched.update(hits)
        if hits:
            found += 1
            if len(hits) > 1:
                duplicates[e["id"]] = len(hits)
        else:
            missed.append(e["id"])
    return {
        "recall": found / len(planted) if planted else 1.0,
        "missed": missed,
        "bait_hits": bait_hits,
        "unmatched": [f["id"] for f in confirmed if f["id"] not in matched],
        "duplicates": duplicates,
        "wide": wide,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("findings", type=Path)
    parser.add_argument("--root", type=Path)
    parser.add_argument("--expected", type=Path)
    parser.add_argument("--expect-coverage", action="append", default=[],
                        metavar="CAMINHO")
    args = parser.parse_args()

    if not args.findings.is_file():
        print(f"resultado: falhou ({args.findings} não existe)")
        return 1
    text = args.findings.read_text()
    findings = parse_findings(text)
    errors = check_format(text, findings, args.root)
    coverage = COVERAGE.search(text)
    section = text[coverage.end():] if coverage else ""
    errors += [f"cobertura: não cita {c}"
               for c in args.expect_coverage if c not in section]

    verdicts = Counter(f["veredito"] for f in findings)
    print(f"achados: {len(findings)} {dict(verdicts)}")
    for error in errors:
        print(f"formato: {error}")
    ok = not errors
    if args.expected:
        r = score(findings, parse_expected(args.expected.read_text()))
        print(f"recall: {r['recall']:.2f}  perdidos: {r['missed']}")
        print(f"iscas confirmadas: {r['bait_hits']}  sem par: {r['unmatched']}"
              f"  duplicados: {r['duplicates']}  largos: {r['wide']}")
        ok = ok and r["recall"] >= MIN_RECALL and not r["bait_hits"]
    print(f"resultado: {'passou' if ok else 'falhou'}")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
