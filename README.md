# dev-senior

Skills pessoais para o fluxo de desenvolvimento com agentes: refinar a
necessidade, especificar, implementar, revisar, tratar o review e commitar.
Funcionam em qualquer ferramenta que leia `SKILL.md` (Claude Code, Codex,
OpenCode, Antigravity).

## Skills

Nove skills, cada uma numa pasta autocontida em `skills/`. Dizem o que o agente
deve fazer, não como a ferramenta funciona, e por isso rodam em qualquer uma.

| Skill | O que faz | Entrada → saída |
|---|---|---|
| `refine` | Questiona o pedido antes de especificar: separa o que foi pedido do que resolve de fato, compara opções e recomenda. Para um bug, faz o diagnóstico (reproduzir, causa raiz, comportamento atual × esperado). Para e espera aprovação. | card, descrição ou conversa → `.agent_plans/<pasta>/brief.md` |
| `spec` | Investiga o código, decide o que reusar e escreve critérios de aceite executáveis (cada um com o comando que o prova) e tarefas. Valida com `check_spec.py` e para para aprovação. Aceita um pedido pequeno e claro sem brief. | brief aprovado → `spec.md` |
| `implement` | Executa a spec de ponta a ponta: confere a prontidão, escreve o teste antes do código, verifica cada critério, mede a qualidade, chama o `review-diff` e corrige o que não tem gatilho de parada. Para nos gatilhos (escopo, segurança, teste removido…) e escalona. Não commita. | `spec.md` → código, `progress.md` e plano de commits |
| `review-diff` | Revisa um diff (intervalo de commits ou árvore de trabalho) e só grava achados verificados. É o motor de revisão das outras skills e também serve sozinha antes de commitar. | diff → `findings.md` |
| `smart-commit` | Agrupa as mudanças em commits atômicos (Conventional Commits), respeita a convenção do repositório, checa segurança e apresenta o plano antes de executar. Não faz push. | árvore alterada → commits |
| `open-pr` | Reverifica cada critério na árvore commitada, monta a descrição da PR com a evidência de cada um e valida com `check_pr.py`. Só com ordem escrita empurra a branch e abre a PR em rascunho. Nunca `--force`, nunca merge. | commits + `spec.md` → `pr.md` e PR |
| `pr-review` | Revisa a PR de outra pessoa no GitHub, com comentários inline validados. | PR alheia → review com comentários |
| `pr-feedback` | Trata os comentários que a sua PR recebeu: avalia, corrige o que procede, rebate com argumento o que não procede e responde na PR. Também corrige os achados de um `findings.md`. | comentários ou `findings.md` → correções e respostas |
| `codebase-agent-docs` | Cria ou audita a documentação de agentes do repositório (`AGENTS.md` raiz como roteador, por pasta, `docs/agents/`, o `REVIEW.md` que o `review-diff` lê e o mapa de reuso). Só escreve o que foi aprovado numa tabela de candidatos com evidência. | repositório → docs de agente |

## Fluxo de trabalho

```text
pedido ─┬─ funcionalidade ─ refine ─ brief.md ─┐
        ├─ bug ─ refine (diagnóstico) ─────────┤
        └─ mudança rápida ─────────────────────┤
                                               ▼
                         spec ─ spec.md ─ APROVAÇÃO
                                               ▼
   implement ─ review-diff ─ correções ─ plano de commits ─ APROVAÇÃO
                                               ▼
                       smart-commit ─ commits ─ ORDEM ESCRITA ─ open-pr
                                                                  │
   PR recebe comentários ─ pr-feedback ◄──────────────────────────┘

   PR de outra pessoa ─ pr-review          docs de agente do repo ─ codebase-agent-docs
```

1. **Entenda o pedido** (`refine`). Funcionalidade vira um brief; bug vira um
   diagnóstico. Um pedido pequeno e claro pula esta etapa.
2. **Especifique** (`spec`). Você lê e aprova a spec: a partir daqui os critérios
   de aceite são o contrato.
3. **Implemente** (`implement`). O agente trabalha sozinho até o fim ou até um
   gatilho de parada; devolve um relatório e um plano de commits.
4. **Commite** (`smart-commit`), depois de você aprovar o plano.
5. **Abra a PR** (`open-pr`), só quando você mandar por escrito. Aprovar a spec
   ou o plano de commits não vale como ordem de push.
6. **Trate o review** (`pr-feedback`) quando a PR receber comentários.

Há quatro paradas humanas: o brief, a spec, o plano de commits e a ordem de
push. O agente nunca cruza nenhuma delas sozinho. As skills conversam por
arquivos em `.agent_plans/<pasta>/` (`brief.md`, `spec.md`, `progress.md`,
`findings.md`, `pr.md`), cada um com um validador em Python quando o formato
importa.

Fora do fluxo principal: `pr-review` para revisar a PR de outra pessoa,
`review-diff` avulso para revisar suas mudanças antes de commitar, e
`codebase-agent-docs` para preparar um repositório para os agentes (o
`REVIEW.md` e o mapa de reuso que ela cria alimentam o `review-diff`; a `spec` lê os `docs/agents/` e o `REVIEW.md`).

## Estrutura

```text
skills/<nome>/SKILL.md   uma pasta por skill, autocontida
docs/                    desenho do fluxo e decisões
install.sh               liga as skills nas pastas das ferramentas
tests/                   conferência do install.sh e avaliações das skills
```

## Instalação

```bash
./install.sh
```

Cria um link para cada skill em `~/.agents/skills`, `~/.claude/skills`,
`~/.claude-work/skills`, `~/.codex/skills`, `~/.config/opencode/skills` e
`~/.gemini/config/skills` (Antigravity), nas ferramentas que existirem na máquina. Uma pasta
real com o mesmo nome nunca é sobrescrita: o script avisa e segue.

Este repositório é a fonte única. Edite as skills aqui, nunca nas pastas das
ferramentas.

## Permissões de comandos

`permissions/rules.py` é a lista única do que o agente roda sem pedir
(navegação, leitura de git e gh, testes e lint de cada stack, alvos de `make`
medidos) e do que continua perguntando (`rm`, `git commit`, `git push`,
`terraform apply`…). `permissions/gh_api_guard.py` é um hook do Claude Code que
faz `gh api` de escrita pedir aprovação e deixa a leitura passar.

```bash
python3 permissions/apply.py --dry-run   # mostra o que mudaria
python3 permissions/apply.py             # grava, com cópia em ~/.Trash
```

Mescla, sem apagar o que já existe, em Claude (pessoal e work), Codex, OpenCode
e Antigravity, e pode rodar de novo depois de editar a lista.

## Avaliações

```bash
python3 -m unittest discover -s tests -p '*_test.py'   # pontuador, sem agente
bash tests/check-review-run.test.sh                     # verificador do repo, sem agente
tests/review-diff.eval.sh commit                        # base | commit | arvore | vazio
AGENT=codex tests/review-diff.eval.sh commit            # mesma avaliação no Codex
tests/codebase-agent-docs.eval.sh escrita               # aprovacao | escrita | auditoria
tests/spec.eval.sh clara                                # clara | ambigua | rapida
tests/refine.eval.sh funcionalidade                     # funcionalidade | vaga | bug | descartada | rapida
tests/implement.eval.sh feliz                          # feliz | gatilho | prontidao
tests/open-pr.eval.sh sem-ordem                      # sem-ordem | com-ordem | falha
```

As avaliações `*.eval.sh` montam um repositório de teste com problemas
plantados (`tests/fixture/`), rodam um agente de verdade e pontuam o
`findings.md` contra o gabarito: custam tokens. Os resultados ficam em
`docs/medicoes/`.

## Desenho

O fluxo completo, os contratos entre as skills e as decisões tomadas estão em
[docs/2026-11-10-fluxo-de-skills-design.md](docs/2026-11-10-fluxo-de-skills-design.md).
