---
name: smart-commit
description: Analisa mudanças em repositórios git e cria commits atômicos seguindo Conventional Commits 1.0. Descobre convenções do repositório, agrupa arquivos por contexto lógico, detecta a língua do projeto, valida segurança pré-commit e apresenta plano consolidado para aprovação antes de executar. Triggers: "commit", "commitar", "fazer commit", "smart commit", "/commit".
---

# Smart Commit

Skill operacional para criar commits atômicos, conformes com Conventional Commits 1.0, respeitando convenções locais do repositório e regras de segurança. Não faz push, não amenda, não bypassa hooks.

## Hierarquia de regras

Quando regras conflitam, vence a primeira que se aplicar:

1. **Configuração explícita do repositório** — `commitlint.config.*`, `.gitmessage`, `CONTRIBUTING.md`, `AGENTS.md`, `CLAUDE.md`
2. **Esta skill** — regras descritas abaixo
3. **Conventional Commits 1.0** — comportamento padrão

## Pipeline (9 etapas obrigatórias e ordenadas)

```
Discovery → Language → Safety Gate → Analyze → Group → Draft → Approve → Execute → Summary
```

Cada etapa tem entrada, saída e condição de falha. Se uma etapa falhar, parar e reportar — não pular nem assumir.

---

### 1. Configuration Discovery

Ler, se existirem:

- `commitlint.config.{js,cjs,mjs,ts}`, `.commitlintrc{,.json,.yaml,.yml}`
- `.gitmessage` (template de commit)
- `CONTRIBUTING.md`, `.github/CONTRIBUTING.md`, `AGENTS.md`, `CLAUDE.md`
- `.husky/commit-msg`, `.git/hooks/commit-msg`

Extrair:

- **Limite de subject** (default: 50 soft / 72 hard)
- **Types permitidos** (default: tabela na etapa 6)
- **Scopes permitidos** — do config explícito OU inferidos do histórico
- **Língua da mensagem**, se declarada

Inferir vocabulário de scopes do histórico:

```bash
git log --pretty='%s' -n 50 | grep -oE '^[a-z]+\(([^)]+)\)' | sort | uniq -c | sort -rn
```

### 2. Language Detection

A língua das mensagens de commit é **sempre inferida do histórico do repositório via git log**, salvo configuração explícita em contrário.

Procedimento obrigatório:

1. **Analisar git log (primário)** — Executar e processar:
   ```bash
   git log --pretty='%s' -n 30
   ```
   Detectar o idioma dominante usando heurísticas lexicais:
   - **Palavras pt-BR:** `adiciona/remove/corrige/altera/atualiza/cria/implementa/ajusta/melhora/substitui/refatora/inclui/extrai/renomeia/move/trata/gerencia/configura`, `para/de/em/com/por/sem/entre`, artigos, preposições
   - **Palavras en-US:** `add/remove/fix/update/create/implement/adjust/improve/replace/refactor/include/extract/rename/move/handle/manage/setup`, articles, prepositions
   - **Acentos:** presença de `á/â/ã/à/é/ê/í/ó/ô/õ/ú/ç` → forte indicador de pt-BR
   - Contar ocorrências de cada grupo; >70% define o idioma
   - Opcional: usar `python3 -c "from langdetect import detect; print(detect('...'))"` se o módulo estiver disponível
2. **Override explícito** — Somente se `AGENTS.md`, `CLAUDE.md`, `.gitmessage` ou `commitlint` declarar idioma de forma explícita e inequívoca, usar o declarado (com registro no sumário)
3. **Ambíguo (<70% de uma língua) ou repo vazio** — perguntar ao usuário via `AskUserQuestion` oferecendo: `pt-BR`, `en-US`, `Outro (especificar)`

A resposta vale para a sessão atual. Não persistir em arquivos do repositório sem permissão explícita.

Registrar a língua detectada no sumário final (etapa 9) para visibilidade.

### 3. Pre-commit Safety Gate

Antes de qualquer `git add`, varrer working tree e index.

**Bloquear (abortar com aviso):**

| Padrão | Razão |
|---|---|
| `.env`, `.env.*` | Variáveis sensíveis |
| `*.key`, `*.pem`, `*.p12`, `*.pfx` | Chaves privadas |
| `id_rsa*`, `id_ed25519*` | Chaves SSH |
| `credentials*`, `secrets*`, `service-account*.json` | Credenciais |
| `.npmrc`, `.pypirc` com tokens | Tokens de registry |
| Arquivos > 1 MB ou binários não-rastreados | Inflam o repositório |
| Marcadores de conflito (`<<<<<<<`, `=======`, `>>>>>>>`) | Merge não resolvido |

Se um arquivo bloqueado é legítimo (ex: `.env.example`), exigir confirmação explícita do usuário, identificando o arquivo e a razão.

### 4. Analyze Changes

```bash
git status --porcelain=v1
git diff --stat
git diff                # working tree não-staged
git diff --cached       # staged
```

Para arquivos com hunks heterogêneos (mais de um contexto no mesmo arquivo), planejar uso de `git add -p` para separação em nível de hunk.

### 5. Atomic Grouping

**Heurísticas, em ordem:**

1. **Mesma entidade de domínio** → 1 commit
   - ex: `User` model + schema + migration + repository + teste
2. **Mesmo type + mesmo escopo lógico** → 1 commit
   - ex: 3 arquivos de docs do módulo `auth` → `docs(auth):`
3. **Imports cruzados** → vão juntos
   - se A importa B e ambos mudaram, mesmo commit
4. **Types diferentes nunca misturam**
   - `feat` + `chore` = 2 commits, mesmo dentro do mesmo arquivo (usar `git add -p`)
5. **Refactor + feature na mesma área** → 2 commits, refactor primeiro
6. **Testes acompanham o código que testam** → mesmo commit que a feature/fix
   - exceto quando o teste cobre código pré-existente: vira commit `test(...)` separado

**Princípio negativo:** se o subject precisa de "and" / "também" / "e", o commit não é atômico. Dividir.

### 6. Draft Messages

#### Formato (Conventional Commits 1.0)

```
<type>(<scope>)<!>: <subject>

<body>

<footer>
```

- `<scope>` é opcional — incluir quando agrega clareza
- `<!>` indica breaking change (também declarar em footer `BREAKING CHANGE:`)
- linha em branco separa subject, body e footer

#### Types

| Type | Uso |
|---|---|
| `feat` | Nova funcionalidade visível ao usuário |
| `fix` | Correção de bug |
| `docs` | Apenas documentação |
| `style` | Formatação, sem mudança de lógica |
| `refactor` | Mudança interna sem alterar comportamento |
| `perf` | Melhoria de performance |
| `test` | Testes adicionados ou corrigidos |
| `build` | Build system ou dependências |
| `ci` | Pipelines CI/CD |
| `chore` | Manutenção (quando não cabe acima) |
| `revert` | Reverte commit anterior |

#### Regras de subject

- ≤ 50 chars (soft) / ≤ 72 chars (hard)
- modo imperativo: `add`, `fix`, `remove` — nunca `added` / `adds` / `adding`
- minúsculas após `: `
- sem ponto final
- descreve **a mudança**, não **o arquivo**

#### Regras de body

- linha em branco antes do body
- wrap em 72 chars por linha
- explica **porquê**, não **o quê** (o diff já mostra o quê)
- pode ter múltiplos parágrafos
- omitir quando o subject é autoexplicativo

#### Footer (trailers)

Suportado:

- `BREAKING CHANGE: <descrição>` — obrigatório quando há `!` no type
- `Refs: #123`, `Closes: #123`, `Fixes: #123`
- `Co-authored-by: Nome <email>` — apenas quando o usuário solicitar explicitamente
- Trailers customizados configurados pelo repositório

**Não adicionar trailer indicando assistência de IA.** Mensagens são autoria do usuário, salvo solicitação explícita em contrário.

### 7. Present Consolidated Plan

Apresentar TODOS os commits propostos antes de executar qualquer um. Formato:

```
Plano de commits (3 commits propostos)
Língua: pt-BR  |  Scopes detectados no repo: [auth, api, ui]

[1/3] feat(auth): adicionar suporte a refresh token JWT
      Arquivos:
        - src/auth/jwt.ts
        - src/auth/refresh.ts
        - tests/auth/refresh.test.ts
      Body:
        Renova o token de acesso automaticamente antes da expiração
        para evitar logout forçado durante sessões ativas.

[2/3] test(auth): cobrir cenários de expiração de token
      Arquivos:
        - tests/auth/expiration.test.ts

[3/3] docs(auth): documentar fluxo de refresh token
      Arquivos:
        - docs/auth.md

Aprovar plano completo? [s / n / editar <n> / reagrupar]
```

Aguardar aprovação do batch inteiro. Se o usuário pedir edição de um item, refazer somente o commit indicado e reapresentar o plano completo.

### 8. Execute

Para cada commit aprovado, em ordem:

```bash
git add <arquivos-explícitos>      # NUNCA "git add ." nem "git add -A"
git commit -F <message-file>        # heredoc/arquivo preserva formatação
```

Para arquivos com hunks heterogêneos, usar `git add -p` direcionado.

**Tratamento de falha de hook:**

- Se `pre-commit` ou `commit-msg` falhar → investigar a causa, **não** usar `--no-verify`
- Reportar erro ao usuário, sugerir correção, reabrir aprovação
- Após corrigir, refazer `git add` + `git commit` — **não** usar `--amend`, criar novo commit

### 9. Final Summary

```bash
git log --oneline -n <N-commits-criados>
git status
```

Sugerir (sem executar):

- `git push origin <branch>` se houver upstream configurado
- Abertura de PR, se aplicável ao fluxo do repositório

---

## Operações proibidas por padrão

| Operação | Razão |
|---|---|
| `git add .` / `git add -A` | Pode incluir arquivos sensíveis ou indesejados |
| `git commit --no-verify` | Bypassa hooks de qualidade e segurança |
| `git commit --amend` em commit publicado | Reescreve história remota |
| `git push` (qualquer variação) | Skill é local-only |
| `git reset --hard` | Destrói trabalho |
| `git rebase -i` | Exige interação humana |

Executar qualquer item acima exige solicitação explícita e específica do usuário, com escopo restrito ao que foi pedido.

## Red flags (recusar e refazer)

| Sinal | Ação |
|---|---|
| Subject vago (`update`, `wip`, `fix`, `changes`) | Recusar, pedir contexto |
| Subject > 72 chars | Reformular |
| Type/scope incompatível com o diff | Reclassificar |
| Body parafraseia o diff | Reescrever explicando o porquê, ou remover |
| Mensagem em língua diferente da definida na etapa 2 | Traduzir |
| Arquivos sem relação lógica no mesmo commit | Dividir |
| Commit que "precisa de and/também" | Dividir |

## Anti-padrões

- **Kitchen-sink commit:** múltiplos contextos juntos
- **Mensagem genérica:** `chore: misc updates`
- **Body redundante:** repete o subject em prosa
- **Scope inventado:** não usado em outros commits do repo
- **Imperativo errado:** `added X`, `fixing Y`, `updates Z`
- **Ponto final no subject**
- **Linha em branco ausente** entre subject e body

## Exemplos canônicos

### feat com body

```
feat(auth): adicionar refresh token JWT

Renova o token de acesso automaticamente antes da expiração para
evitar logout forçado durante sessões ativas. O refresh ocorre
quando restam menos de 5 minutos de validade.
```

### fix com footer de issue

```
fix(api): tratar resposta nula do gateway de pagamento

O gateway ocasionalmente retorna null para transações pendentes.
Adicionado guard antes de acessar campos da resposta.

Closes: #482
```

### Breaking change

```
feat(api)!: remover endpoint /v1/users em favor de /v2/users

O endpoint v1 não suporta paginação e nunca foi versionado.
Clientes devem migrar para /v2/users, que aceita os mesmos filtros
e adiciona controle de cursor.

BREAKING CHANGE: GET /v1/users foi removido. Migre para /v2/users.
Refs: #310
```

### refactor sem body (subject autoexplicativo)

```
refactor(users): extrair validação para módulo dedicado
```

### revert

```
revert: feat(auth): adicionar refresh token JWT

Reverte o commit a1b2c3d. Causou loop de renovação em sessões
sem refresh_token persistido.

Refs: #517
```
