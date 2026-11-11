---
name: codebase-agent-docs
description: >-
  Use quando for preciso criar ou auditar a documentação de agentes de um repositório
  (AGENTS.md raiz como roteador, AGENTS.md por pasta, docs/agents/, o REVIEW.md que o
  review-diff lê e o mapa de reuso); só escreve o que foi aprovado numa tabela de
  candidatos com evidência. Disparos: "criar docs de agente", "configurar AGENTS.md",
  "auditar a documentação de agentes", "create agent docs", "/agent-docs".
metadata:
  opencode/slash: "true"
---

# Documentação de agentes

Monta um sistema de **roteador e folhas**: um arquivo que o agente lê primeiro
e um conjunto plano de folhas que ele só abre quando a tarefa pede. O objetivo
não é completude: é que o agente leia o conjunto inteiro sem gastar contexto e
que cada linha seja um fato que ele não acharia com `grep`.

## O modelo

```text
AGENTS.md                ← roteador. Nenhum procedimento. Só tabelas e links.
 ├─ ## Índice de tópicos → docs/agents/*.md      (assunto)
 └─ ## Guias por pasta   → <pasta>/AGENTS.md     (lugar)
REVIEW.md                ← o que o review procura neste repositório
docs/agents/*.md         ← folhas. Quase nenhum link entre elas.
```

O roteador liga um nível para baixo. Fato que duas folhas precisam é
**duplicado**, nunca ligado de uma folha à outra.

## Modo

| Situação | Modo | O que faz |
|---|---|---|
| Sem `AGENTS.md` na raiz | `criar` | Gera o conjunto a partir dos candidatos aprovados |
| Com `AGENTS.md` na raiz | `auditar` | Propõe correções; nunca regenera um arquivo inteiro |

## Limites

| Arquivo | Limite |
|---|---|
| `AGENTS.md` da raiz | 120 linhas; nenhum procedimento |
| `AGENTS.md` de pasta | 75 linhas, 3 a 6 seções `##` |
| `docs/agents/*.md` | 140 linhas; no máximo 1 link |
| `docs/agents/recipes/*.md` | 160 linhas |
| `REVIEW.md` | 80 linhas |

Seção com cerca de 11 linhas (20 no máximo), dois níveis de título, nunca
`###`, e uma armadilha por seção `##`.

O `scripts/check_docs.py` desta pasta reprova limite estourado, título `###`,
link quebrado, tópico fora do índice e caminho citado que não existe. A skill
só termina com ele limpo. Arquivo que passa do limite vira um tópico novo no
índice; crescer o roteador é sempre a correção errada.

## Teste de admissão

Antes de escrever uma linha, pergunte: **o `grep` responderia isso?** Se sim,
fica de fora. Entram os fatos invisíveis ou caros de derivar:

- **Ordem:** ordem de registro, "crie a migração antes do serviço".
- **Falha silenciosa:** "sem isso, a auditoria é pulada; não há aviso".
- **Espaço negativo:** o que apagar, o que não existe, o que o produto não faz.
- **Configuração fora do padrão:** fila em threads, não prefork; porta **8432**.
- **Peculiaridade de teste:** fixture que pula tabela, diferença de dialeto.
- **Padrão que o código esconde**, e comportamento que parece bug e não é.

Ficam de fora: assinaturas, listas de parâmetros, payloads de exemplo,
explicação do framework, visão geral do produto, tabela de stack, histórico,
roadmap. Um fato de stack que surpreende vira armadilha.

**Evidência.** Cada armadilha, linha de reuso, prioridade de review e arquivo
protegido cita a fonte entre crases, que o `check_docs.py` confere:
(fonte: `<commit>`) ou (fonte: `<arquivo:linha>`). Sem evidência, não entra.

## Fase 1: análise

Nunca leia o repositório inteiro no contexto principal. Com delegação a
subagents, um subagent por frente, e guarde só os relatórios. Sem delegação,
as frentes em sequência, guardando só o resumo de cada uma.

| Frente | Lê | Devolve |
|---|---|---|
| 1. Produto e stack | README, manifesto, versões do lockfile | o que o produto não faz; cada escolha fora do padrão |
| 2. Arquitetura | árvore até 3 níveis, ponto de entrada, registro de rotas ou módulos | camadas, ligações automáticas, ordem de registro |
| 3. Unidade exemplar | a unidade que mais se repete (módulo, pasta de feature, pacote) | a estrutura interna e o papel de cada arquivo |
| 4. Armadilhas | `git log --grep='^fix'` com corpo e diff, setup dos testes, CI, `.env.example` | armadilhas candidatas; **a frente mais valiosa**: cada commit de correção é uma armadilha em que alguém já caiu |
| 5. Protegidos | `.gitignore`, arquivos gerados e o gerador, migrações, segredos, lockfiles | o que nunca se edita à mão, nunca se commita ou só muda com cuidado |
| 6. Convenções e comandos | config de lint, últimos 50 assuntos de commit, template de PR, comandos de teste e validação | regras de lint, exemplos reais de commit e, para cada comando, o que ele prova |
| 7. Reuso | módulos utilitários, commits que removeram cópia (`git log -i --grep='reuse\|duplic\|extract'`), contagem de chamadores (`git grep -c`) | helpers que já foram recriados ou têm três chamadores ou mais |
| 8. Histórico de review | `gh pr list --state merged --limit 30` e os comentários de review de cada PR | o que os revisores apontam repetidamente |

- A frente 6 roda cada comando de verificação que não precisa de serviço
  externo e anota o que ele prova. Comando que precisa de banco, fila ou
  variável de ambiente não roda: entra como "precisa de <o quê>".
- Sem `gh` ou sem remoto GitHub, a frente 8 registra "sem histórico de review",
  e as prioridades do `REVIEW.md` saem dos commits de correção.
- Detecte o idioma da documentação pelo README e pelos últimos 50 commits.
  Escreva no idioma dominante; identificadores, comandos e caminhos ficam como
  no repositório.

## Parada: candidatos

Grave `.agent_plans/agent-docs/candidatos.md`:

```markdown
# Candidatos · modo <criar | auditar>

| ID | Tipo | Afirmação | Evidência | Consequência | Destino |
| --- | --- | --- | --- | --- | --- |
| C-01 | armadilha | <o fato, contrastivo> | `<commit>` ou `<arquivo:linha>` | <o que quebra, e se é silencioso> | `docs/agents/gotchas.md` |
```

Tipos: `armadilha`, `reuso`, `protegido`, `review`, `comando`, `regra`.

No modo `auditar`, acrescente `## Correções propostas`, uma linha por correção
com ID `K-01`…, arquivo, problema e o texto novo:

- cada erro do `check_docs.py`, com a mensagem copiada literalmente;
- caminhos e símbolos citados que não existem mais (confira cada símbolo com
  busca no código);
- o que falta: `REVIEW.md`, a tabela de comandos, o mapa de reuso, armadilhas
  novas da frente 4.

**PARE** e peça aprovação por ID ("aprovo C-01 a C-07 e K-02"). Com aprovação
prévia explícita de quem chamou, siga só com os candidatos que têm evidência e
registre isso no topo do arquivo.

## Fase 2: geração

Só o que foi aprovado. Os esqueletos estão em `references/templates.md`.

**Modo `criar`**, folhas antes da raiz, porque o índice só é honesto quando as
folhas existem:

1. Tópicos em `docs/agents/`: sempre `gotchas.md`, `dont-touch.md`, `tests.md`,
   `code-style.md`, `commits-prs.md`, `workflow.md`; `reuse.md` com um reuso
   aprovado; `<unidade>-anatomy.md`, `development.md` e um tópico por
   subsistema que já mordeu alguém duas vezes, quando houver. Todo conteúdo
   sai de candidatos aprovados (tipos `regra` e `comando` incluídos), nunca de
   suposição. Seção vazia é pior que arquivo ausente.
1. Receitas em `docs/agents/recipes/`, para tarefa repetida mais de duas vezes,
   com várias etapas em ordem fixa e um passo que falha em silêncio.
1. `AGENTS.md` por pasta, para cada camada estrutural real.
1. `REVIEW.md`.
1. `AGENTS.md` da raiz por último.

**Modo `auditar`:** aplique só as correções aprovadas, editando o trecho em
cada arquivo existente. Nunca regenere um arquivo inteiro e nunca reescreva
texto que alguém escreveu à mão.

## Fase 3: validação

```bash
python3 <pasta desta skill>/scripts/check_docs.py <raiz do repositório>
```

Repita até a saída ser `limpo`. Depois confira lendo:

- [ ] A raiz não tem passo a passo, só tabelas e links
- [ ] Todo tópico está no índice, e nada no índice deixa de existir
- [ ] Toda armadilha diz a consequência, não só a regra
- [ ] Todo fato traz a fonte
- [ ] Cada receita é uma lista numerada que termina nos comandos reais de validação e teste

## Regras de escrita

- **Armadilha em três tempos, nesta ordem:** título `##` afirmativo; o
  mecanismo com o símbolo exato; a consequência, frisando o **silêncio**; a
  correção no imperativo; a fonte. Se a falha faz barulho, não é armadilha.
- **Contraste:** "X, não Y" ("UUID v7, não UUID v4"). Nomear o errado ajuda o
  agente a reconhecer o próprio erro.
- **Negrito no token surpreendente, nunca na regra inteira:** a porta
  `**8432**`, o `**antes**` da escrita.
- **Toda proibição com o motivo.**
- **Imperativo, sem "você", "deveria" ou "considere".**
- **Tabela para fatos enumeráveis, prosa para fatos causais.**
- **Só exemplos reais**, tirados do histórico e de arquivos que existem.
- **Anatomia descreve o estado-alvo; receita descreve o procedimento.** Nunca
  misture.
- Caminhos e símbolos entre crases, relativos à raiz ou à pasta do guia. Use
  `arquivo:NNN` só quando o fato mora numa linha difícil de achar.
- Arquivo que não existe no repositório (exemplo, convenção, arquivo a criar)
  vai como placeholder `<...>` ou fora de crases: o `check_docs.py` cobra todo
  caminho entre crases que comece num item real.
- Listas numeradas com `1.` em todos os itens.

## Conflito entre doc e código

Escreva uma vez, na raiz:

> Quando este arquivo e o código discordarem, **confie no código**. Este
> arquivo descreve a intenção; o código é a verdade. Corrija a documentação
> junto com qualquer mudança de código.

O inverso só serve em repositório guiado por spec. Junto, a tabela de fontes
de verdade: 3 a 7 linhas ligando uma pergunta ao arquivo que a define. Padrões
vistos em produção, em inglês: `references/lessons-learned.md`.
