# Etapa 2: melhorias do `codebase-agent-docs`

> **Para agentes:** SUB-SKILL OBRIGATÓRIA: use superpowers:subagent-driven-development
> (recomendado) ou superpowers:executing-plans para executar este plano tarefa a
> tarefa. Os passos usam checkbox (`- [ ]`) para acompanhamento.

**Objetivo:** a skill `codebase-agent-docs` passa a gerar o que o fluxo precisa
(`REVIEW.md`, tabela de comandos de verificação, mapa de reuso), detecta
sozinha se cria ou audita, só escreve o que o humano aprovou numa tabela de
candidatos com evidência e só termina com um script de limites limpo.

**Arquitetura:** a skill continua só de instruções, mais um script em
`scripts/check_docs.py` (Python, só biblioteca padrão) que reprova os limites e
as citações quebradas. A análise termina num arquivo de candidatos em
`.agent_plans/agent-docs/candidatos.md`, que é a parada de aprovação. A prova
de que funciona é uma avaliação no mesmo molde da etapa 1: um repositório de
teste com histórico em que armadilhas, reuso e arquivo gerado foram plantados
em commits, um agente rodando sem interação e checagens sobre o resultado.

**Tecnologia:** Markdown no padrão Agent Skills, Python 3.9+ só com biblioteca
padrão, Bash, git, `claude -p` e `codex exec` nas avaliações.

**Spec:** `docs/2026-11-10-fluxo-de-skills-design.md`, seções 3, 5 (IDs
estáveis, `arquivo:linha`), 6.8 e 7 a 9 só no que a skill alimenta.

## Restrições globais

- Texto das skills em português; identificadores, comandos e caminhos como
  aparecem no código.
- A skill descreve capacidades, nunca a API de uma ferramenta: "com delegação,
  um subagent por frente; sem ela, as frentes em sequência".
- Nenhuma skill instala ferramenta; o script usa só a biblioteca padrão e roda
  no `python3` 3.9 do macOS.
- Commits sem atribuição de IA, mensagens em en-US, pelo `smart-commit`, com
  parada para aprovação. Push nunca.
- `SKILL.md` com no máximo 200 linhas (hoje tem 174 e ganha dois modos).
- A skill nunca regenera por cima de documentação existente: no modo auditoria
  só propõe correções.
- Nada é escrito nos arquivos de documentação do projeto antes da aprovação da
  tabela de candidatos, salvo quando quem chama dá aprovação prévia explícita.

## Decisões deste plano

- **Onde ficam as novas saídas.** `REVIEW.md` na raiz (é onde o `review-diff`
  procura); a tabela de comandos de verificação no `AGENTS.md` raiz, no lugar
  do bloco "Setup & commands"; o mapa de reuso em `docs/agents/reuse.md`.
- **O que sai da raiz.** A visão geral do produto e a tabela de stack deixam de
  ser geradas por padrão. Um fato de stack que surpreende ("fila em threads,
  não prefork") vira armadilha com evidência, não linha de tabela.
- **Evidência por fato.** Cada armadilha, linha do mapa de reuso, prioridade do
  `REVIEW.md` e arquivo protegido cita de onde veio: commit (`abc1234`) ou
  `arquivo:linha`. É o que torna a auditoria possível depois.
- **Uma parada, um arquivo.** Os dois modos gravam
  `.agent_plans/agent-docs/candidatos.md`: tabela de candidatos com IDs `C-01`…
  e, na auditoria, as correções propostas. O humano aprova por ID, de uma vez.
- **Nova frente de análise: histórico de review.** Comentários de review das
  últimas PRs mergeadas, quando houver `gh` e remoto GitHub; sem eles, as
  prioridades do `REVIEW.md` saem dos commits de correção e a seção diz isso.
- **Idioma.** `SKILL.md` e `references/templates.md` são reescritos em
  português, porque mudam quase inteiros. `references/lessons-learned.md` fica
  em inglês por enquanto: não muda nesta etapa e é leitura de apoio.
- **Script dentro da skill, teste fora.** `scripts/check_docs.py` é usado pela
  skill em tempo de execução; o teste fica em `tests/check_docs_test.py`.

## Fora deste plano

- Poda por uso (seção nunca citada por uma spec): depende da skill `spec`.
- Tradução de `references/lessons-learned.md`.
- Medição de ganho: no final, como decidido em 2026-11-11.
- Conferir que commits citados como evidência existem: o script confere só
  caminhos e linhas.

## Foco de revisão

1. **Repositório sem remoto GitHub ou sem `gh`.** A frente de histórico de
   review não pode travar nem inventar comentários; o `REVIEW.md` sai dos
   commits de correção e diz isso. Teste: a fixture não tem remoto; o modo
   `escrita` exige o `REVIEW.md`.
1. **`AGENTS.md` já existe e foi editado à mão.** A skill não pode regenerar
   por cima. Teste: modo `auditoria` exige o `AGENTS.md` byte a byte igual e a
   citação quebrada apontada em `candidatos.md`.
1. **Falso positivo do `check_docs.py` travando o fim da skill.** Placeholder
   (`<name>/x.py`), comando entre crases (`make run`) e caminho de outro
   projeto não podem reprovar. Teste: `test_ignores_placeholders_and_commands`
   na Tarefa 1.
1. **Comando de verificação que precisa de serviço externo.** Não pode ser
   rodado nem omitido em silêncio: entra na tabela com o que precisa. Teste: a
   fixture tem testes de integração que pedem `DATABASE_URL`; o modo `escrita`
   exige `DATABASE_URL` no `AGENTS.md`.
1. **Arquivo gerado.** Precisa ir para a lista de protegidos com o comando que
   o gera. Teste: o modo `escrita` exige `app/schema_gen.py` em
   `docs/agents/dont-touch.md`.

---

## Pré-requisito: branch

Criar o branch `etapa-2-codebase-agent-docs` a partir de `main`.

### Tarefa 1: `check_docs.py`

**Arquivos:**

- Criar: `skills/codebase-agent-docs/scripts/check_docs.py`
- Teste: `tests/check_docs_test.py`

**Interfaces:**

- Produz:
  - CLI: `python3 skills/codebase-agent-docs/scripts/check_docs.py [raiz]`
    (padrão: diretório atual). Imprime um erro por linha no formato
    `<arquivo>: <problema>` e sai 1 se houver algum; sai 0 com a linha
    `limpo`.
  - `check(root: Path) -> list[str]`.

Regras, com os valores exatos:

| Alvo | Regra |
|---|---|
| `AGENTS.md` da raiz | existe; até 120 linhas |
| `AGENTS.md` de qualquer outra pasta | até 75 linhas |
| `docs/agents/*.md` | até 140 linhas; até 1 link markdown (`](`) |
| `docs/agents/recipes/*.md` | até 160 linhas |
| `REVIEW.md` | até 80 linhas |
| Todos os acima | nenhum título `### ` fora de bloco de código; nenhum link markdown relativo para alvo inexistente |
| `docs/agents/**/*.md` | cada um aparece num link do `AGENTS.md` da raiz |
| Crases em todos os acima | `caminho` cujo primeiro segmento existe na raiz e que não existe é erro; `caminho:N` com N maior que o número de linhas é erro |

Pastas ignoradas na busca por `AGENTS.md`: `.git`, `.agent_plans`,
`node_modules`, `vendor`, `.venv`, `dist`, `build`. Token entre crases com
espaço, `<`, `*`, `$` ou `://` não é caminho.

- [ ] **Passo 1: escrever os testes que falham** em `tests/check_docs_test.py`
  (unittest). Um helper `make(files: dict[str, str]) -> Path` monta a árvore
  num diretório temporário. O import vem de
  `skills/codebase-agent-docs/scripts/`, inserido no `sys.path`.

```python
def test_clean_set_passes(self):            # raiz 10 linhas com link para docs/agents/a.md, a.md 20 linhas
    self.assertEqual(check(root), [])
def test_missing_root_is_error(self):        # erro contém "AGENTS.md"
def test_root_over_120_lines_is_error(self): # 121 linhas
def test_dir_guide_over_75_lines_is_error(self)
def test_topic_over_140_lines_is_error(self)
def test_topic_with_two_links_is_error(self)
def test_h3_outside_code_is_error(self):     # "### x" fora de cerca; o mesmo dentro de cerca não é erro
def test_broken_relative_link_is_error(self)
def test_topic_not_in_root_index_is_error(self)
def test_cited_path_that_does_not_exist_is_error(self):  # `app/velho.py` com app/ existente
def test_cited_line_beyond_file_is_error(self):           # `app/a.py:9` com a.py de 3 linhas
def test_ignores_placeholders_and_commands(self):
    # `<name>/x.py`, `make run`, `src/x.py` sem src/, `https://x.io/a`, `*.md` → nenhum erro
```

- [ ] **Passo 2: rodar e ver falhar**

  `python3 -m unittest discover -s tests -p '*_test.py'` → FAIL nos testes
  novos (`ModuleNotFoundError: check_docs`).

- [ ] **Passo 3: implementar `check_docs.py`** com `from __future__ import
  annotations`, `pathlib` e `re`.

- [ ] **Passo 4: rodar e ver passar**

  O mesmo comando, com `python3` e com `/usr/bin/python3` → `OK`.

- [ ] **Passo 5:** `ruff check --select E,F,W,B,UP --target-version py39` nos
  dois arquivos → limpo.

### Tarefa 2: fixture com histórico, avaliação e RED

**Arquivos:**

- Criar: `tests/make-docs-fixture.sh`, `tests/codebase-agent-docs.eval.sh`
- Criar: `docs/medicoes/2026-11-etapa-2.md`
- Modificar: `README.md` (seção "Avaliações": uma linha para a avaliação nova)

**Interfaces:**

- Consome: `tests/run-agent.sh` (etapa 1) e `check_docs.py` (Tarefa 1).
- Produz:
  - `tests/make-docs-fixture.sh <destino> criar|auditar`: repositório Python
    pequeno, sem remoto, com o histórico abaixo, um commit por linha, todos
    com `git -c user.name=fixture -c user.email=fixture@example.invalid`.
    Em `auditar`, um último commit com um `AGENTS.md` escrito à mão.
  - `tests/codebase-agent-docs.eval.sh aprovacao|escrita|auditoria`.

Histórico plantado:

| # | Mensagem do commit | O que muda | O que planta |
|---|---|---|---|
| 1 | `chore: initial structure` | `app/text.py` com `slugify`; `app/handlers/__init__.py` com `HANDLERS = {"email": send_email}`; `app/handlers/email.py`; `app/export.py`; `.env.example`; `tests/` com unittest; `tests/integration/test_db.py` que pula sem `DATABASE_URL`; `.gitignore` com `__pycache__/` | — |
| 2 | `feat: add csv export` | `app/export.py` ganha `_slug` local igual ao `slugify` | — |
| 3 | `fix: use UTC timestamps in export` | `datetime.now()` → `datetime.now(timezone.utc)` | armadilha A1: hora local desloca a exportação sem erro |
| 4 | `fix: register sms handler in HANDLERS` | `app/handlers/sms.py` já existia; entra em `HANDLERS` | armadilha A2: handler fora de `HANDLERS` é ignorado sem aviso |
| 5 | `refactor: reuse slugify from app.text in export` | remove `_slug`, importa `slugify` | reuso R1: `slugify` em `app/text.py` |
| 6 | `fix: keep totals in integer cents` | `float` em reais → `int` em centavos | armadilha A3: dinheiro em `float` acumula erro de arredondamento sem erro |
| 7 | `chore: add generated schema` | `scripts/gen_schema.py` e `app/schema_gen.py` com cabeçalho `# Gerado por scripts/gen_schema.py. Não editar.` | protegido P1 |
| 8 (só `auditar`) | `docs: add agent guide` | `AGENTS.md` de 30 linhas, escrito à mão, que cita `app/legacy_export.py` (não existe) e contém a frase `Regra da casa: revisar com a Ana antes de mexer em HANDLERS.` | citação quebrada e texto à mão |

Prompts (texto exato, porque são entrada de teste):

| Modo | Fixture | Prompt |
|---|---|---|
| `aprovacao` | `criar` | `Use a skill codebase-agent-docs neste repositório.` |
| `escrita` | `criar` | `Use a skill codebase-agent-docs neste repositório. Aprovação prévia: escreva todos os candidatos que tiverem evidência; não pare para perguntar.` |
| `auditoria` | `auditar` | `Use a skill codebase-agent-docs neste repositório.` |

Checagens (cada uma imprime `ok:` ou `FALHOU:`; o script sai 1 se alguma
falhar; código de saída do agente diferente de 0 reprova antes):

| Modo | Checagem |
|---|---|
| todos | nenhum commit novo |
| `aprovacao` | `git status --porcelain` só com `?? .agent_plans/` |
| `aprovacao` | `.agent_plans/agent-docs/candidatos.md` existe e tem linhas com `C-01` |
| `aprovacao` | `candidatos.md` traz A1, A2 e A3 (para cada uma, o hash curto do commit 3, 4 ou 6, ou a palavra `UTC`, `HANDLERS` ou `centavos`/`cents`) e `slugify` |
| `escrita` | `check_docs.py` sai 0 na fixture |
| `escrita` | existem `AGENTS.md`, `REVIEW.md` e `docs/agents/reuse.md` |
| `escrita` | `docs/agents/gotchas.md` traz A1, A2 e A3 (mesmo critério do modo `aprovacao`) e ao menos 3 linhas com `fonte:` |
| `escrita` | `docs/agents/reuse.md` contém `slugify` |
| `escrita` | `docs/agents/dont-touch.md` contém `app/schema_gen.py` |
| `escrita` | `AGENTS.md` contém `python3 -m unittest` e `DATABASE_URL` |
| `auditoria` | `AGENTS.md` byte a byte igual ao do commit 8 |
| `auditoria` | `candidatos.md` cita `app/legacy_export.py` |

- [ ] **Passo 1: escrever `tests/make-docs-fixture.sh`** com os arquivos em
  heredoc, commit a commit.

- [ ] **Passo 2: conferir a fixture**

  ```bash
  d=$(mktemp -d); tests/make-docs-fixture.sh "$d/c" criar && git -C "$d/c" log --oneline | wc -l && (cd "$d/c" && python3 -m unittest discover -s tests)
  tests/make-docs-fixture.sh "$d/a" auditar && git -C "$d/a" log --oneline | wc -l
  ```

  Esperado: `7`, os testes passam (o de integração pula) e `8`.

- [ ] **Passo 3: escrever `tests/codebase-agent-docs.eval.sh`** e a linha do
  README. O log do agente fica fora do repositório da fixture, como na etapa 1.

- [ ] **Passo 4: rodar a RED com a skill atual**

  `tests/codebase-agent-docs.eval.sh aprovacao`, `escrita` e `auditoria`.
  Esperado: os três falham (a skill atual não grava `candidatos.md`, não gera
  `REVIEW.md` nem `reuse.md` e não distingue auditoria). Registre em
  `docs/medicoes/2026-11-etapa-2.md` o que falhou em cada modo. Se algum modo
  passar, o teste não discrimina: registre e ajuste o teste antes da Tarefa 3.

### Tarefa 3: reescrever a skill

**Arquivos:**

- Modificar: `skills/codebase-agent-docs/SKILL.md` (reescrita em português)
- Modificar: `skills/codebase-agent-docs/references/templates.md` (reescrita
  em português)

**Interfaces:**

- Consome: `check_docs.py` (Tarefa 1) e a avaliação (Tarefa 2).
- Produz, para o fluxo: `REVIEW.md` (lido pelo `review-diff`), a tabela de
  comandos do `AGENTS.md` raiz e `docs/agents/reuse.md` (lidos pela `spec`).

O `SKILL.md` contém, nesta ordem:

1. **`description`** em português, com os disparos atuais e "auditar a
   documentação de agentes".
1. **O modelo:** roteador e folhas, como hoje.
1. **Modo:** sem `AGENTS.md` na raiz, `criar`; com ele, `auditar`. O modo vai
   no topo de `candidatos.md`.
1. **Limites:** a tabela de hoje, com a frase "o `scripts/check_docs.py`
   reprova; a skill só termina com ele limpo".
1. **Teste de admissão:** o de hoje, mais: cada fato cita a evidência
   (commit ou `arquivo:linha`); sem evidência, não entra.
1. **Fase 1, análise.** As seis frentes de hoje e uma sétima, histórico de
   review (`gh pr list --state merged --limit 30` e os comentários de review de
   cada uma; sem `gh` ou sem remoto GitHub, registrar e seguir). Com
   delegação, um subagent por frente; sem delegação, as frentes em sequência.
   A frente de comandos roda cada comando de verificação que não precisa de
   serviço externo e anota o que ele prova; o que precisa de serviço entra
   como "não executado: precisa de <serviço>".
1. **Parada: candidatos.** Grava `.agent_plans/agent-docs/candidatos.md` com
   a tabela `ID · tipo (armadilha, reuso, protegido, review, comando) ·
   afirmação · evidência · consequência · destino` e, na auditoria, a seção
   "Correções propostas" (saída do `check_docs.py`, caminhos e símbolos
   citados que não existem mais, o que falta: `REVIEW.md`, tabela de
   comandos, mapa de reuso). Para e
   pede aprovação por ID. Com aprovação prévia explícita de quem chamou, segue
   com os candidatos que têm evidência.
1. **Fase 2, geração** (só o aprovado). Criar: folhas antes da raiz, como hoje,
   mais `REVIEW.md` e `docs/agents/reuse.md`. Auditar: só as correções
   aprovadas, editando os arquivos existentes; nunca regenerar um arquivo
   inteiro.
1. **Fase 3, validação:** `python3 <pasta da skill>/scripts/check_docs.py`
   até ficar limpo, mais a lista de checagem por leitura de hoje.
1. **Regras de escrita e conflito entre doc e código:** as de hoje, traduzidas.

O `templates.md` reescrito:

- **`AGENTS.md` raiz:** sai "What this product does" e a tabela "Stack";
  "Setup & commands" vira `## Comandos` com a tabela `Comando · O que prova ·
  Precisa de`; ficam o índice de tópicos, os guias por pasta, as fontes de
  verdade e o conflito; "Architecture" vira `## Ligação que o código não
  mostra`, opcional, só com evidência.
- **`REVIEW.md` novo:** `## Prioridades` (lista numerada, cada item com o que
  procurar e a evidência), `## Não é achado aqui` (padrão aceito que um
  revisor de fora marcaria, com o motivo) e `## Regras que o review confere`
  (tabela `Regra · Onde está`).
- **`reuse.md` novo:** tabela `Precisa de · Use · Onde · Evidência`; admissão:
  helper que já foi recriado (commit de refatoração ou correção) ou com três
  chamadores ou mais.
- **`gotchas.md` e `dont-touch.md`:** cada entrada termina com `(fonte:
  <commit ou arquivo:linha>)`.
- Os demais esqueletos (pasta, workflow, anatomia, tests, code-style,
  commits-prs, development, subsistema, receita) traduzidos sem mudar a
  forma.

- [ ] **Passo 1: reescrever o `SKILL.md` e o `templates.md`.**

- [ ] **Passo 2: checagens estáticas**

  `wc -l skills/codebase-agent-docs/SKILL.md` → ≤ 200.
  `grep -rniE 'Task tool|Agent tool|subagent_type|dispatch' skills/codebase-agent-docs` → nada.

- [ ] **Passo 3: rodar a GREEN**

  `tests/codebase-agent-docs.eval.sh aprovacao`, `escrita` e `auditoria`
  (podem rodar em paralelo) → os três saem 0. Registre na medição.

- [ ] **Passo 4: portabilidade**

  `AGENT=codex tests/codebase-agent-docs.eval.sh escrita`. Registre o
  resultado; não bloqueia a tarefa.

- [ ] **Passo 5: corrigir as falhas**

  Mesma regra da etapa 1: ler `agent.log` e os arquivos gerados, corrigir o
  texto da skill (a fixture e as checagens só mudam se o erro estiver nelas),
  no máximo 3 rodadas; depois, parar e mostrar ao Lucas.

## Commit

Plano único de commits, separado por tarefa, antes da revisão final, como na
etapa 1.
