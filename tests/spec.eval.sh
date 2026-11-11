#!/usr/bin/env bash
# Avalia a skill spec na fixture com histórico (modo spec). Modos: clara (brief
# completo: a spec precisa achar reuso e padrões), ambigua (o brief usa um termo
# que nada define: a spec precisa deixar [PRECISA DECISÃO]) e rapida (pedido
# direto, sem brief). Roda um agente de verdade: custa tokens. O diretório
# temporário fica para inspeção.
set -euo pipefail

repo="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
case "${1:-}" in
  clara)
    slug=aviso-exportacao title="Aviso por SMS quando a exportação terminar"
    rule="avisando a operação"
    prompt="Use a skill spec neste repositório. O brief aprovado está em .agent_plans/$slug/brief.md."
    ;;
  ambigua)
    slug=aviso-elegiveis title="Aviso por SMS só para clientes elegíveis"
    rule="avisando a operação só quando o cliente for elegível"
    prompt="Use a skill spec neste repositório. O brief aprovado está em .agent_plans/$slug/brief.md."
    ;;
  rapida)
    slug=""
    prompt="Use a skill spec neste repositório. Pedido direto, sem brief: trocar o separador do CSV de exportação de vírgula para ponto e vírgula."
    ;;
  *)
    echo "uso: $0 clara|ambigua|rapida" >&2
    exit 2
    ;;
esac

tmp=$(mktemp -d)
echo "diretório: $tmp"
"$repo/tests/make-docs-fixture.sh" "$tmp/repo" spec
cd "$tmp/repo"

if [ -n "$slug" ]; then
  mkdir -p ".agent_plans/$slug"
  cat > ".agent_plans/$slug/brief.md" <<EOF
# Brief: $title
Status: aprovado · Origem: card-101 · Modo: padrão

## Problema
A operação não sabe quando o CSV de pedidos de um cliente ficou pronto e
consulta a pasta de tempos em tempos.

## Pedido vs. necessidade
Pedido: mandar um SMS. Necessidade: saber que o arquivo está pronto, sem ficar
olhando.

## Apetite
Pequeno: meio dia.

## Referências de mercado
| Fonte | Como resolve | O que aproveitar |
| --- | --- | --- |
| — | — | — |

## Opções consideradas
| Opção | Prós | Contras | Veredito |
| --- | --- | --- | --- |
| Não fazer | Sem custo | A operação segue consultando a pasta | Descartada |
| Resolver sem código | Checagem manual agendada | Não elimina a espera | Descartada |
| Aviso pelo canal que já existe | Sem dependência nova | Depende de o canal entregar | Recomendada |

## Recomendação
Ao fim da exportação CSV de um cliente, enviar uma mensagem pelo canal de SMS
que já existe, $rule. O nome do arquivo, que a mensagem cita, passa a ser
\`<nome do cliente normalizado: sem acento, minúsculo, com hífens>-<AAAA-MM-DD em UTC>.csv\`.

## Fora de escopo
Gravar o CSV em disco e a pasta de destino (já resolvidos fora deste código),
e-mail, retentativa, histórico de avisos.

## Riscos e armadilhas
Nenhum conhecido.

## Perguntas em aberto
Nenhuma.
EOF
fi

rc=0
"$repo/tests/run-agent.sh" "$tmp/repo" "$prompt" > "$tmp/agent.log" 2>&1 || rc=$?
if [ "$rc" != 0 ]; then
  echo "resultado: falhou (o agente saiu com código $rc; veja $tmp/agent.log)"
  exit 1
fi

fail=0
check() {  # check <descrição> <comando...>
  local what=$1
  shift
  if "$@" >/dev/null 2>&1; then echo "ok: $what"; else echo "FALHOU: $what"; fail=1; fi
}
has() { grep -qiE "$2" <<<"$1"; }  # has <texto> <regex>
finish() { [ "$fail" = 0 ] && echo "resultado: passou" || echo "resultado: falhou"; exit "$fail"; }

spec=$(ls .agent_plans/*/spec.md 2>/dev/null | head -1 || true)
check "nenhum commit novo" test "$(git rev-list --count HEAD)" = 8
check "só .agent_plans/ novo" test "$(git status --porcelain)" = "?? .agent_plans/"
check "spec.md existe" test -n "$spec"
[ -n "$spec" ] || finish
check "Status: rascunho" grep -q '^Status: rascunho' "$spec"

section() { awk -v h="## $1" '$0==h {p=1; next} /^## / {p=0} p' "$spec"; }
validator="$repo/skills/spec/scripts/check_spec.py"
case "$1" in
  clara)
    check "check_spec.py limpo" python3 "$validator" "$spec" .
    check "Reuso cita app/text.py com Reusar" has "$(section Reuso)" 'app/text\.py.*reusar'
    check "Reuso registra o termo slug" has "$(section Reuso)" 'slug'
    check "Padrões cita AGENTS.md:linha" has "$(section "Padrões aplicáveis")" 'AGENTS\.md:[0-9]'
    check "Referências cita app/export.py:linha" has "$(section "Referências no código")" 'app/export\.py:[0-9]'
    check "Referências cita app/handlers/" has "$(section "Referências no código")" 'app/handlers/'
    check "matriz tem nome de cliente vazio" has "$(section "Matriz de casos")" 'vazi'
    check "matriz menciona dispatch" has "$(section "Matriz de casos")" 'dispatch'
    check "orçamento sem dependência nova" grep -q 'dependências novas 0' "$spec"
    check "Pronto quando roda unittest" grep -q 'Pronto quando:.*python3 -m unittest' "$spec"
    check "no máximo 150 linhas" test "$(wc -l < "$spec")" -le 150
    ;;
  ambigua)
    out=$(python3 "$validator" "$spec" . || true)
    check "validador só reclama de marcador pendente" \
      test -n "$out" -a -z "$(grep -v 'marcador pendente' <<<"$out" || true)"
    check "um marcador menciona o termo indefinido" grep -qi 'PRECISA DECISÃO[^]]*eleg' "$spec"
    ;;
  rapida)
    check "check_spec.py limpo" python3 "$validator" "$spec" .
    check "Modo: rápido" grep -q 'Modo: rápido' "$spec"
    check "Brief: —" grep -q 'Brief: —' "$spec"
    check "app/export.py em Permitido" has "$(section Escopo)" 'Permitido:.*app/export\.py'
    check "no máximo 50 linhas" test "$(wc -l < "$spec")" -le 50
    ;;
esac
finish
