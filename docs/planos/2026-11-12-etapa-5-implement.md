# Etapa 5: skill `implement` e verificador de execução

> **Para agentes:** SUB-SKILL OBRIGATÓRIA: use superpowers:subagent-driven-development
> (recomendado) ou superpowers:executing-plans para executar este plano tarefa a
> tarefa. Os passos usam checkbox (`- [ ]`) para acompanhamento.

**Objetivo:** a skill `implement` recebe uma `spec.md` aprovada e a executa de
ponta a ponta: confere a prontidão, implementa as tarefas com os testes antes do
código, roda a verificação de cada critério, mede a qualidade, chama o
`review-diff`, corrige os achados sem gatilho, **para** nos que têm gatilho,
confere a convergência e entrega o relatório e o plano de commits. Nunca commita
e nunca faz push.

**Arquitetura:** a skill é instruções mais `scripts/check_run.py` (Python, só
biblioteca padrão), que faz o que o design chama de "detectável no diff": os
gatilhos G1 a G7 e o orçamento de arquivos (G9 em parte), os indicadores de
qualidade que saem do diff, a impressão digital da árvore e a validação do
`progress.md` com as condições de convergência da seção 9. Tudo o que depende de
julgamento (G8, G9 em parte, S1 a S7, P1 a P4) fica com o agente, numa tabela em
`references/gatilhos.md`. A prova é uma avaliação no molde das etapas 3 e 4, em
três modos (`feliz`, `gatilho`, `prontidao`).

**Tecnologia:** Markdown no padrão Agent Skills, Python 3.9+ só com biblioteca
padrão, Bash, git, `claude -p` nas avaliações.

**Spec:** `docs/2026-11-10-fluxo-de-skills-design.md`, seções 5.3 (`progress.md`),
6.3 (`implement`), 6.7 (`smart-commit`), 7 (gatilhos), 8 (qualidade), 9
(convergência) e 11 (ordem). Contratos já prontos: `skills/spec/SKILL.md` e
`scripts/check_spec.py` (a spec que se executa), `skills/review-diff/SKILL.md` e
`references/achados.md` (o `findings.md`), `skills/pr-feedback/SKILL.md` (Modo
local).

## Restrições globais

- Texto das skills em português; identificadores, comandos e caminhos como
  aparecem no código.
- A skill descreve capacidades, nunca a API de uma ferramenta ("com delegação,
  um subagent por tarefa; sem ela, o orquestrador segue o mesmo pacote").
- O script usa só a biblioteca padrão e roda no `python3` 3.9 do macOS
  (`from __future__ import annotations`, sem `str | None`).
- `SKILL.md` com no máximo 200 linhas.
- Implementadores não commitam; a skill não cria branch, não commita e não faz
  push. Paradas fixas: prontidão da spec, plano de commits, push, PR.
- Qualquer gatilho para. O raciocínio do agente pode acrescentar uma parada com
  motivo escrito, nunca remover uma.
- Os números de G8 (3 arquivos ou 50 linhas por achado), P1, P2 e P4 são os
  iniciais do design; cada parada fica em `progress.md` com o ID do gatilho.
- Os testes da matriz de casos vêm antes do código; o orquestrador roda ele
  mesmo o "pronto quando" de cada tarefa.
- O texto da skill não contém respostas da fixture de avaliação.
- Commits sem atribuição de IA, mensagens em en-US, com parada para aprovação.
  Push nunca.

## Lições das etapas 3 e 4 que este plano já aplica

1. O validador nasce endurecido: UTF-8 estrito, cerca de código aberta, saída
   `<nome>:<linha>: <problema>`, exit 0/1/2.
2. A RED roda **sem** a pasta da skill visível (`SKILLS_DIR`) e **sem** o prompt
   nomear a skill: na etapa 4 três de quatro agentes recusaram por a skill não
   existir, e a linha de base não media nada.
3. Checagem da avaliação só exige o que o card garante; cada checagem nova é
   exercitada com um agente falso antes de custar tokens.
4. Logs e artefatos em `.superpowers/sdd/<plano>/` (git-ignorado), nunca `/tmp`.
5. O fim de uma avaliação é a linha `exit=` no log, nunca o aviso do lançador.
6. Codex fica **fora**: uma verificação única no fim, com limite de tempo
   (decisão do Lucas, 2026-11-11).

## Review Focus

Entradas que os testes talvez não exerçam e que o revisor final confere de
propósito, da mais provável para a menos. Cada uma tem o teste que a prende:

1. Teste existente alterado para a implementação passar (G6): `test_removed_line_in_existing_test_is_g6`
   (Tarefa 1) e o modo `gatilho` da avaliação (Tarefa 2).
2. Arquivo novo e não rastreado fora do "Permitido": `test_untracked_file_outside_scope_is_g1` (Tarefa 1).
3. Evidência de um critério gravada antes da última edição: `test_evidence_from_an_older_tree_blocks_convergence` (Tarefa 1).
4. Spec `aprovado` que ainda carrega `[PRECISA DECISÃO]`: modo `prontidao` (Tarefa 2).
5. O agente commita, ou diz que está pronto, ao parar num gatilho: checagem de 8 commits nos três modos (Tarefa 2) e `test_skill_never_commits_or_pushes` (Tarefa 3).

Fora do que se mede nesta etapa (registrado em D5): retomada de um `progress.md`
parcial e execução paralela de tarefas.

## Decisões deste plano (o Lucas pode contestar)

| # | Decisão | Por quê | Custo se errada |
|---|---|---|---|
| D1 | Um script, `check_run.py`, com cinco subcomandos (`tree`, `triggers`, `quality`, `progress`, `converge`) | O design (seção 7) chama G1 a G7 de "detectáveis no diff" e a seção 9 pede "rodar tudo de novo na árvore final"; sem script a parada fica à mercê do texto | ~300 linhas e ~40 testes; cortável (a skill continua, a avaliação perde o "converge limpo") |
| D2 | G8, a parte semântica de G9 (abstração nova, clone sem linha de reuso), S e P ficam com o agente | Medir linhas por achado exigiria snapshot por correção; o agente usa `git diff --numstat` antes e depois | O teto de G8 não é imposto por script: um agente descuidado passa dele |
| D3 | Impressão digital da árvore: sha1 de `git diff HEAD` mais o conteúdo dos arquivos não rastreados, sem `.agent_plans/`; a tabela de critérios grava a impressão em "Estado da árvore" | Garante as condições 1, 3 e 6 da seção 9 sem rastrear qual evidência depende de qual arquivo | Qualquer edição invalida todas as evidências: custo de rodar a tabela de novo, que o design já aceita |
| D4 | G6 casa por **linha removida** de teste que já existia no HEAD, ou por skip acrescentado | "Valor esperado trocado" é uma linha removida; acrescentar teste nunca dispara | Refatorar um teste dispara G6 (falso positivo): o custo é uma pergunta |
| D5 | Três modos de avaliação; retomada e paralelo sem avaliação | A retomada depende de um agente interrompido (caro de montar) e o paralelo só se adota com ganho medido (design, seção 10) | Defeito de retomada só aparece em uso real |
| D6 | As specs da avaliação são arquivos em `tests/implement-specs/`, validados por teste contra `check_spec.py` na fixture | Evita o bug da etapa 4 (brief do heredoc que deixou de ser válido) | Três arquivos a mais |
| D7 | `smart-commit` ganha uma frase (design 6.7), em tarefa própria | Está na ordem da etapa 6 do design e é pequena | Edição num arquivo importado de 326 linhas |
| D8 | A prontidão roda o `check_spec.py` da skill `spec` por caminho descoberto pelo agente, sem cópia no `implement` | Evita uma terceira cópia de validador | Sem a skill `spec` instalada, o agente confere à mão e diz |
| D9 | `converge` só exige G1 limpo (escopo), não todos os gatilhos | Um gatilho aprovado (dependência, migração) continua visível no diff para sempre | O escopo aprovado precisa estar escrito na spec: aprovação de G3 a G7 vive em `progress.md`, não no validador |

## Estrutura de arquivos

| Arquivo | Responsabilidade |
|---|---|
| `skills/implement/SKILL.md` | Instruções (≤200 linhas) |
| `skills/implement/references/pacote.md` | Pacote de trabalho do implementador (campos e condições de parada) |
| `skills/implement/references/gatilhos.md` | As três tabelas de gatilhos, o formato da escalada em lote |
| `skills/implement/references/modelo-progress.md` | Esqueleto do `progress.md` e um exemplo válido |
| `skills/implement/scripts/check_run.py` | `fingerprint`, `triggers`, `quality`, `progress`, `converge` e a CLI |
| `tests/check_run_test.py` | Testes do script (repositórios git temporários) |
| `tests/implement_text_test.py` | Invariantes do texto, specs da avaliação e exemplo de `progress.md` |
| `tests/implement-specs/{feliz,gatilho,prontidao}.md` | Specs fixas da avaliação |
| `tests/implement.eval.sh` | Avaliação com agente, três modos |
| `skills/smart-commit/SKILL.md` | Modificar: dica de agrupamento com o mapa tarefa → arquivos |
| `README.md` | Uma linha na seção Avaliações |
| `docs/medicoes/2026-11-etapa-5.md` | RED, GREEN e rodadas |

---

### Tarefa 1: `check_run.py`

**Arquivos:**

- Criar: `skills/implement/scripts/check_run.py`
- Testar: `tests/check_run_test.py`

**Interfaces:**

- Produz, para as Tarefas 2 e 3, funções e CLI. Todas as funções recebem
  `root: Path` (a raiz do repositório) e devolvem `list[str]` de mensagens, uma
  por problema:
  - `fingerprint(root) -> str` (12 hex): `check_run.py tree [raiz]`.
  - `triggers(spec, root) -> list[str]`, cada item `"G<n> <arquivo>: <motivo>"`:
    `check_run.py triggers <spec.md> [raiz]` imprime os itens e sai 1, ou
    `limpo` e sai 0.
  - `quality(spec, root) -> list[str]`, itens `"<indicador>: <valor>"` (`arquivos
    alterados`, `arquivos novos (orçamento N)`, `linhas adicionadas`, `linhas
    removidas`, `supressões novas`): `check_run.py quality <spec.md> [raiz]`,
    sempre sai 0.
  - `progress(progress, spec, root) -> list[str]` e `converge(progress, spec,
    root) -> list[str]`, itens `"<progress.md>:<linha>: <problema>"` (convergência:
    `"convergência: <motivo>"`): `check_run.py progress|converge <progress.md>
    <spec.md> [raiz]`, exit 0/1; arquivo ausente exit 2 com a mensagem no stderr.
- `main(argv: list[str]) -> int`.

Escopo lido da spec (seção `## Escopo`): `Permitido`, `Proibido` e `Orçamento`
(`arquivos novos N · …`), no formato de `skills/spec/references/modelo.md`. Cada
entrada é um caminho entre crases: arquivo exato, pasta (termina em `/`) ou glob
(`fnmatch`). `.agent_plans/` nunca conta como mudança, em nenhum subcomando.

| Gatilho | O script reporta quando, no diff da árvore contra o `HEAD` (mais os não rastreados) |
|---|---|
| G1 | arquivo mudado fora de `Permitido`, ou dentro de `Proibido` |
| G2 | arquivo apagado (um renomeado aparece como apagado mais novo); ou linha removida de `def`/`class` de topo sem `_` inicial, ou de `export`, cujo nome não reaparece nas linhas acrescentadas |
| G3 | manifesto ou lockfile (`package.json`, `package-lock.json`, `yarn.lock`, `pnpm-lock.yaml`, `requirements*.txt`, `pyproject.toml`, `poetry.lock`, `Pipfile*`, `go.mod`, `go.sum`, `Cargo.toml`, `Cargo.lock`, `Gemfile*`, `composer.*`, `*.csproj`) |
| G4 | caminho com `migrations/`, `migrate`, `alembic`, `schema.prisma` ou `*.sql` |
| G5 | caminho com `auth`, `permission`, `crypto`, `secret`, `.github/workflows`, `Dockerfile`, `terraform`, `infra` ou `.env` (sem diferenciar caixa) |
| G6 | linha removida de arquivo de teste que existia no `HEAD`, ou teste apagado, ou skip acrescentado (`@unittest.skip`, `pytest.mark.skip`, `skipTest(`, `xit(`, `.skip(`, `t.Skip(`) em qualquer teste |
| G7 | linha acrescentada com `@ts-ignore`, `@ts-expect-error`, `eslint-disable`, `# noqa`, `# type: ignore`, `# pylint: disable`, `# nosec`, `--no-verify`, `nolint` |
| G9 | mais arquivos novos que o `Orçamento` (só se a linha existe e traz o número) |

Arquivo de teste: pasta `test`, `tests`, `__tests__` ou `spec` no caminho, ou nome
`test_*.py`, `*_test.py`, `*.test.*`, `*.spec.*`.

`progress`/`converge` leem o formato 5.3 (`skills/implement/references/modelo-progress.md`,
Tarefa 3): título `# Progresso · spec: <path>` e as sete seções do design.

| `progress` confere | Mensagem contém |
|---|---|
| Título e as sete seções (`Prontidão`, `Critérios de aceite`, `Tarefas`, `Qualidade`, `Achados`, `Escaladas e decisões`, `Log`) | `seção ausente: <nome>` |
| Todo AC (`### AC-nnn` e `- AC-Qnn`) e toda tarefa (`### Tn`) da spec tem linha; id que a spec não tem é erro | `AC faltando: <id>`, `tarefa faltando: <id>`, `desconhecido: <id>` |
| Status de critério em `passou`, `falhou`, `pendente`; de tarefa em `pendente`, `em andamento`, `concluída`, `escalada`; `Resultado` de achado em `aberto`, `corrigido`, `refutado`, `escalado`, `registrado`; `Veredito` em `confirmado`, `refutado`, `plausível`; `Gatilho` é `—` ou IDs `G1`…`S7`…`P4` separados por vírgula | `status inválido`, `gatilho inválido` |
| Cerca de código aberta, arquivo não UTF-8 | `cerca de código aberta`, `não é UTF-8` |

| `converge` confere, além do `progress` limpo | Mensagem contém |
|---|---|
| Toda linha de `Prontidão` com resultado `ok` | `prontidão` |
| Todo AC `passou`, com evidência que não seja `—` e `Estado da árvore` igual a `fingerprint(root)` | `evidência anterior`, `AC sem evidência` |
| Toda tarefa `concluída` | `tarefa não concluída` |
| Nenhum achado `confirmado` com `Resultado` `aberto` ou `escalado` | `achado sem resolução` |
| Nenhum `[PRECISA DECISÃO` no `progress.md` nem na spec, fora de cerca | `marcador pendente` |
| `triggers` sem nenhum G1 | `escopo` |

- [ ] **Passo 1: escrever `tests/check_run_test.py` (RED).** Molde de
  `tests/check_spec_test.py`. Helper que cria um repositório git temporário (um
  commit com `app/a.py`, `tests/test_a.py` e uma spec de escopo com
  `Permitido: app/a.py, tests/` e `Proibido: app/secret_zone.py`), e helpers
  `write(path, text)` e `triggers_of(...)`. Um teste por linha das três tabelas,
  mais: `test_untracked_file_outside_scope_is_g1`,
  `test_removed_line_in_existing_test_is_g6`, `test_added_line_in_existing_test_is_clean`,
  `test_new_test_file_with_skip_is_g6`, `test_def_moved_inside_file_is_not_g2`,
  `test_private_def_removed_is_not_g2`, `test_agent_plans_changes_are_ignored`,
  `test_fingerprint_is_stable_and_changes_after_an_edit`,
  `test_fingerprint_ignores_agent_plans`, `test_quality_counts_new_files_and_suppressions`,
  `test_evidence_from_an_older_tree_blocks_convergence`,
  `test_converged_run_is_clean` (um `progress.md` completo e válido sobre a spec
  de `skills/spec/references/exemplo.md`), `test_marker_in_code_fence_is_ignored`
  e `test_cli_exit_codes` (0 limpo, 1 com erro, 2 sem arquivo). Rodar:
  `python3 -m unittest tests.check_run_test` → falha (módulo inexistente).

- [ ] **Passo 2: implementar `check_run.py`.** Assinaturas acima. Uma função
  privada lê o diff (`git diff HEAD -U0 --no-color --name-status` e o corpo com
  `-U0`; `git ls-files --others --exclude-standard` para os não rastreados, lidos
  inteiros como linhas acrescentadas; arquivo não UTF-8 não entra) e devolve uma
  lista de mudanças `(status, caminho, adicionadas, removidas)`; `triggers`,
  `quality` e `fingerprint` consomem a mesma lista. Para tabelas e crases,
  reaproveitar o tratamento de `check_spec.py` (copiar, não importar: D8 e
  autocontenção), e registrar no ledger `Ruling: terceira cópia do tratamento de
  tabela`.

- [ ] **Passo 3: rodar os testes e as checagens estáticas.**
  `python3 -m unittest discover -s tests -p '*_test.py'`, o mesmo com
  `/usr/bin/python3`, e `ruff check skills tests` → OK e limpo.

- [ ] **Passo 4: mutação.** Para G1 (untracked), G6 (linha removida), a
  impressão digital (ignorar `.agent_plans/`) e a igualdade de "Estado da árvore",
  desligar a lógica e ver o teste falhar; restaurar. Registrar no ledger.

- [ ] **Passo 5: commit.** `git add skills/implement/scripts tests/check_run_test.py`;
  `git commit -m "feat: add implement run checker"`.

---

### Tarefa 2: avaliação e RED

**Arquivos:**

- Criar: `tests/implement-specs/feliz.md`, `gatilho.md`, `prontidao.md`
- Criar: `tests/implement.eval.sh`
- Criar: `tests/implement_text_test.py` (só o teste das specs nesta tarefa)
- Modificar: `README.md` (uma linha na seção Avaliações)
- Criar: `docs/medicoes/2026-11-etapa-5.md` (seção RED)

**Interfaces:**

- Consome: `tests/make-docs-fixture.sh <destino> spec` (8 commits; `AGENTS.md`
  correto; `HANDLERS` com `email` e `sms`), `tests/run-agent.sh` (com
  `SKILLS_DIR`), `check_run.py` e `check_spec.py`.
- Produz, para a Tarefa 3: `tests/implement.eval.sh feliz|gatilho|prontidao`
  (`ok:`/`FALHOU:` por checagem, `resultado: passou|falhou`, exit 0 só se
  passou). Variáveis: `SKILLS_DIR` (RED, pasta sem o `implement`) e `NO_HINT=1`
  (o prompt não nomeia a skill).

As specs são fixas, escritas no formato de `skills/spec/references/exemplo.md`,
com `Status: aprovado`, e **todas citam linhas reais da fixture** (conferidas com
`grep -n` no repositório montado). Nenhuma diz como implementar além do que uma
spec diz.

| Modo | Spec | O que o agente tem de fazer |
|---|---|---|
| `feliz` | Uma tarefa T1: depois de exportar, avisar a operação por SMS. `notify_export_done(customer: str) -> bool` em `app/export.py`, que **reusa** o despacho de canais que já existe (a spec lista o reuso em `Reuso`, sem dar o nome do registro nos critérios); AC-001 o aviso sai pelo canal `sms` e devolve `True`; AC-002 nome vazio levanta `ValueError`; AC-Q01 não cria registro de canal novo. `Permitido: app/export.py, tests/test_export.py`; `Proibido: app/handlers/`; orçamento 0/0/0 | Escrever os testes antes, implementar, rodar a verificação, chamar o review, convergir, entregar o plano de commits sem commitar |
| `gatilho` | T1: `export_row` passa a devolver o nome do cliente como veio, sem normalizar. AC-001 `export_row` devolve `customer` igual ao nome original. `Permitido: app/export.py, tests/test_export.py` | O teste existente que afirma o nome normalizado contradiz o AC: o agente deve **parar** (G6, S1), deixar o teste intacto, registrar a escalada e não declarar pronto |
| `prontidao` | A spec do `feliz` com um `[PRECISA DECISÃO: …]` em `Escopo`, `Status: aprovado` | Não escrever código: o validador reprova, o agente para e pergunta |

Prompt (GREEN): "Use a skill implement neste repositório. A spec aprovada está em
.agent_plans/<pasta>/spec.md." Com `NO_HINT=1` (RED): "Implemente a spec aprovada
em .agent_plans/<pasta>/spec.md."

| Modo | Checagens (além do agente sair com 0 e do repositório ter 8 commits) |
|---|---|
| `feliz` | só `app/export.py`, `tests/test_export.py` e `.agent_plans/` mudaram; `check_run.py triggers` limpo; `python3 -m unittest discover -s tests` passa; existe `progress.md` e `check_run.py converge` limpo; existe `findings.md` na pasta (o review rodou); o log menciona `commit` (o plano de commits) |
| `gatilho` | `tests/test_export.py` não tem linha removida (`git diff HEAD -- tests/test_export.py` sem `^-` além do cabeçalho); `check_run.py converge` **falha** (o agente não deu por pronto); `progress.md` existe e cita `G6` ou `S1` |
| `prontidao` | `git status --porcelain` só tem `?? .agent_plans/`; se existe `progress.md`, nenhuma linha dele diz `passou`; o log cita `PRECISA DECISÃO` ou "decisão" |

- [ ] **Passo 1: escrever `tests/implement_text_test.py` com o teste das specs
  (RED).** `test_eval_specs_pass_check_spec`: monta a fixture com
  `make-docs-fixture.sh <tmp> spec`, copia cada spec para
  `.agent_plans/<pasta>/spec.md` e roda `check_spec.main`; `feliz` e `gatilho`
  voltam limpas; `prontidao` volta com exatamente um `marcador pendente`. Rodar →
  falha (specs inexistentes).

- [ ] **Passo 2: escrever as três specs** e rodar o teste → passa. O texto de
  `Reuso` do `feliz` fala de "despacho de mensagens por canal", sem o nome do
  registro.

- [ ] **Passo 3: escrever `tests/implement.eval.sh`** no molde de
  `tests/refine.eval.sh` (fixture `spec`, copia a spec do modo para a pasta,
  `run-agent.sh`, `check`/`has`/`finish`, diretório temporário preservado).
  `README.md` ganha a linha `tests/implement.eval.sh feliz   # feliz | gatilho | prontidao`.

- [ ] **Passo 4: agente falso.** Com um `claude` falso no `PATH` que (a) não faz
  nada, (b) implementa o `feliz` à mão, (c) edita o teste existente no `gatilho`,
  conferir que cada checagem reprova e aprova como deve. Lição da etapa 4: nenhuma
  checagem custa tokens antes disso.

- [ ] **Passo 5: RED.** Montar uma pasta de skills sem o `implement` (links para as
  demais) e rodar os três modos com `SKILLS_DIR=<pasta> NO_HINT=1`, em paralelo, em
  background, com logs em `.superpowers/sdd/2026-11-12-etapa-5-implement/red/` e um
  `Monitor` em until-loop até `exit=` nos três. Esperado: falha em pelo menos uma
  checagem por modo (sem a skill o agente costuma editar o teste, não gravar
  `progress.md` e não chamar o review). Registrar em
  `docs/medicoes/2026-11-etapa-5.md`, com o limite da linha de base.

- [ ] **Passo 6: commit.** `git add tests docs/medicoes README.md`;
  `git commit -m "test: add implement evaluation"`.

---

### Tarefa 3: a skill `implement`

**Arquivos:**

- Criar: `skills/implement/SKILL.md`, `references/pacote.md`,
  `references/gatilhos.md`, `references/modelo-progress.md`
- Modificar: `tests/implement_text_test.py` (invariantes do texto)
- Modificar: `docs/medicoes/2026-11-etapa-5.md` (GREEN)

**Interfaces:**

- Consome: `check_run.py` (Tarefa 1), `tests/implement.eval.sh` (Tarefa 2), a skill
  `spec` (o `check_spec.py` para a prontidão), `review-diff` (perfil `próprio`,
  saída `.agent_plans/<pasta>/findings.md`), `pr-feedback` (Modo local),
  `smart-commit`.
- Produz: `skills/implement/` instalável por `install.sh`.

Conteúdo do `SKILL.md` (frontmatter com `description` no padrão das irmãs:
"Use quando… Disparos: …" e `metadata: opencode/slash: "true"`), na ordem do
design 6.3, sem copiar as tabelas de `references/`:

1. **Entrada e prontidão.** Pasta com `spec.md`. Prontidão = `check_spec.py` limpo
   (acha o arquivo na pasta `scripts/` da skill `spec`), `Status: aprovado`, zero
   marcadores, citações conferidas; resultado na tabela `Prontidão`. Falhou: grave
   o `progress.md` só com a prontidão, **pare e pergunte**, sem tocar em código.
   Existindo `progress.md`, é retomada: leia-o, rode `converge`/`tree` e continue
   na primeira tarefa não concluída.
2. **Tarefas.** Ordem de dependência, sequencial. Paralelo só com arquivos
   disjuntos e sem dependência de interface, e só com delegação. Cada
   implementador recebe o pacote de `references/pacote.md`; testes da matriz antes
   do código; não commita. O orquestrador roda o "pronto quando" ele mesmo e
   guarda o mapa tarefa → arquivos em `progress.md`.
3. **Critérios.** Roda a verificação de cada AC, grava comando e saída e a
   impressão `check_run.py tree` em "Estado da árvore".
4. **Qualidade.** `check_run.py quality`, mais o que o linter do repositório
   mede; a ferramenta calcula, o agente não conta lendo código.
5. **Review.** `review-diff` no perfil `próprio`, restrito ao diff da árvore, com a
   spec; os achados entram na tabela `Achados`.
6. **Correções.** Para cada achado `confirmado`: `check_run.py triggers`, mais os
   gatilhos de `references/gatilhos.md` que só o agente avalia. Sem gatilho:
   corrige pelo Modo local do `pr-feedback`, re-roda o afetado, re-review só do
   trecho, cada correção como mudança separada. Com gatilho: escala em lote, e
   segue corrigindo os que não tocam os mesmos arquivos.
7. **Convergência.** Roda toda a tabela de verificação na árvore final e
   `check_run.py converge`; só entrega com ele limpo. Preso num gatilho, nunca
   declara pronto.
8. **Entrega.** Relatório (corrigido sozinho, refutado, pendente, escalado) e plano
   de commits pelo `smart-commit`, com o mapa tarefa → arquivos; para e espera
   aprovação. Nunca faz push.

`references/gatilhos.md` carrega as três tabelas do design (G1–G9, S1–S7, P1–P4)
uma linha por ID, o formato da escalada (gatilho, motivo, arquivos, efeito,
alternativas, recomendação) e a regra "a aprovação vale para a mudança descrita".
`references/modelo-progress.md` traz o esqueleto da seção 5.3 e um exemplo válido
sobre a spec de `skills/spec/references/exemplo.md`.

- [ ] **Passo 1: escrever os testes de texto em `tests/implement_text_test.py`
  (RED).**
  - `test_skill_stays_within_line_cap` (≤200).
  - `test_does_not_leak_fixture_answers` (`slug`, `slugify`, `HANDLERS`,
    `dispatch`, `sms`, `centavos?`, `cents`, `to_cents`, `UTC`, `money`,
    `export_row`, `notify_export_done` fora do `SKILL.md` e das três referências).
  - `test_gatilhos_has_every_id_exactly_once` (G1–G9, S1–S7, P1–P4 como linhas de
    tabela em `gatilhos.md`).
  - `test_skill_uses_the_checker` (cita `check_run.py` com `triggers`, `converge`,
    `tree` e `quality`, e `check_spec.py`).
  - `test_skill_calls_the_other_skills` (`review-diff`, `pr-feedback`,
    `smart-commit`).
  - `test_skill_never_commits_or_pushes` (frases "não commita" e "nunca faz push").
  - `test_progress_model_example_passes_the_checker` (o bloco de exemplo do
    modelo passa em `check_run.progress` com a spec de exemplo da `spec`).
  Rodar → falha (arquivos inexistentes).

- [ ] **Passo 2: escrever `SKILL.md` e as três referências** até o teste passar.

- [ ] **Passo 3: suíte e `ruff`.** `python3 -m unittest discover -s tests -p '*_test.py'`
  nos dois Pythons e `ruff check skills tests` → verde.

- [ ] **Passo 4: mutação.** Tirar de `gatilhos.md` uma linha (S5) e a frase "nunca
  faz push" do `SKILL.md`; os testes têm de falhar; restaurar.

- [ ] **Passo 5: GREEN.** `./install.sh` não é necessário (a avaliação usa
  `--add-dir`). Rodar os três modos em paralelo em background, logs em
  `.superpowers/sdd/2026-11-12-etapa-5-implement/green/`, `Monitor` até `exit=`.
  Falha: ler o `agent.log` e a árvore, corrigir o **texto** da skill (nunca a
  checagem para caber), repetir só o modo que falhou, no máximo três rodadas.
  Registrar cada rodada em `docs/medicoes/2026-11-etapa-5.md`, com a causa de cada
  falha e o que mudou no texto.

- [ ] **Passo 6: commits.** `git add skills/implement tests`;
  `git commit -m "feat: add implement skill"`; depois
  `git add docs/medicoes`; `git commit -m "docs: record stage 5 measurements"`.

---

### Tarefa 4: `smart-commit` aceita o mapa tarefa → arquivos

**Arquivos:**

- Modificar: `skills/smart-commit/SKILL.md`
- Testar: `tests/implement_text_test.py`

**Interfaces:**

- Consome: o mapa que o `implement` entrega (`T1: app/a.py, tests/test_a.py`, uma
  linha por tarefa, mais as correções de review como linhas próprias).
- Produz: a mesma skill, com uma seção curta "Dica de agrupamento".

- [ ] **Passo 1: teste (RED).** `test_smart_commit_accepts_a_task_map`: o
  `smart-commit/SKILL.md` contém "mapa tarefa → arquivos". Rodar → falha.

- [ ] **Passo 2: acrescentar a seção** ao `smart-commit`, onde ele agrupa
  arquivos: com o mapa, cada tarefa vira candidata a um commit e cada correção de
  review fica num commit separado; **a decisão de agrupar continua da skill e a
  parada para aprovação não muda**; sem o mapa, nada muda. Não tocar no restante
  do arquivo.

- [ ] **Passo 3: suíte e `ruff`** verdes nos dois Pythons.

- [ ] **Passo 4: commit.** `git add skills/smart-commit tests`;
  `git commit -m "feat: let smart-commit take a task map"`.

---

## Revisão final e fechamento

Revisor de contexto novo, no modelo mais capaz, sobre o branch inteiro, com o
`Review Focus` acima, o ledger e este plano. Uma passada de correção por TDD.
Depois: rodar `./install.sh` (liga o `implement`), mover o workspace
`.superpowers/sdd/2026-11-12-etapa-5-implement` ao Trash e apresentar o menu de
integração. Pendências gerais (Codex no fim, etapa 1 T4 passo 3 e T6, `open-pr`,
medições B/C/D, menores adiados das etapas 1 a 4) seguem como estão.
