# Esqueletos

Um esqueleto por arquivo do sistema. Não dependem de stack: preencha a partir
dos candidatos aprovados, nunca de suposição.

Escreva a prosa no idioma dominante do projeto (detectado na fase 1). Títulos,
código, comandos e caminhos ficam como no repositório. Os títulos abaixo estão
em português; traduza se a prosa do projeto não for, e mantenha a tradução
igual em todos os arquivos.

Placeholders: `<nome>` singular, `<nomes>` plural, `<Nome>` PascalCase,
`<unidade>` a unidade de código que mais se repete no repositório.

Quando houver evidência de acompanhamento remoto, ofereça como candidata para o
`AGENTS.md` da raiz a seção abaixo; só a escreva após aprovação do humano e com
valores verificados no projeto:

```markdown
## Acompanhamento de projeto
- Ferramenta: <ferramenta> · Acesso: <CLI ou MCP> · Projeto: <projeto>
- Tipos: spec → <tipo> · brief → <tipo opcional>
- Status: em andamento = <status> · em review = <status>
```

---

## `AGENTS.md` da raiz

Até 120 linhas. Tabelas e links, quase nenhuma prosa de ligação. **Nenhum
procedimento mora aqui.** Sem visão geral do produto e sem tabela de stack: um
fato de stack que surpreende vai para `gotchas.md` com a fonte.

````markdown
# <Projeto> — guia de navegação para agentes

## Comandos

| Comando | O que prova | Precisa de |
| --- | --- | --- |
| `<comando de teste>` | <o que passa a valer quando ele passa> | — |
| `<comando de validação>` | <lint, tipos, formato> | — |
| `<comando de integração>` | <o que ele cobre a mais> | `<VARIÁVEL>`, <serviço> |

Só entra comando que rodou na análise, ou que diz do que precisa para rodar.

## Ligação que o código não mostra

<Opcional. O único fato de ligação que o agente não infere, por exemplo a
ordem de registro, com a consequência em uma frase e a fonte.>

## Índice de tópicos

| Arquivo | O que cobre |
| --- | --- |
| [docs/agents/workflow.md](docs/agents/workflow.md) | <uma linha> |
| [docs/agents/gotchas.md](docs/agents/gotchas.md) | Invariantes e armadilhas não óbvias |
| [docs/agents/dont-touch.md](docs/agents/dont-touch.md) | Gerados, segredos, configuração protegida |
| [docs/agents/reuse.md](docs/agents/reuse.md) | O que já existe antes de criar algo |
| [docs/agents/<unidade>-anatomy.md](docs/agents/<unidade>-anatomy.md) | Estrutura canônica de <unidade> |
| [docs/agents/tests.md](docs/agents/tests.md) | <uma linha> |
| [docs/agents/code-style.md](docs/agents/code-style.md) | <uma linha> |
| [docs/agents/commits-prs.md](docs/agents/commits-prs.md) | <uma linha> |
| [docs/agents/recipes/<verbo>-<nome>.md](docs/agents/recipes/<verbo>-<nome>.md) | Passo a passo: <o que produz> |

Linhas de receita começam com `Passo a passo:`, para o agente distinguir uma
referência de um roteiro sem abrir o arquivo. O `REVIEW.md` não entra no
índice: o `review-diff` o procura pelo nome.

## Guias por pasta

- [<pasta>/AGENTS.md](<pasta>/AGENTS.md) — <o que é esta camada>

## Fontes de verdade

| Assunto | Onde está definido |
| --- | --- |
| Schema | `<caminho>` |
| Regras de negócio | `<caminho>` |

De 3 a 7 linhas. Aponte o arquivo que *define* o fato, não o que o descreve.

## Conflito entre este arquivo e o código

Quando este arquivo e o código discordarem, **confie no código**. Este arquivo
descreve a intenção; o código é a verdade. Corrija a documentação junto com
qualquer mudança de código.
````

---

## `REVIEW.md`

Até 80 linhas, na raiz. É o que o `review-diff` lê para saber o que procurar;
a skill de review define como procurar.

````markdown
# Review

## Prioridades

1. <categoria>: <o que procurar aqui, concreto> (fonte: `<PR, commit ou arquivo:linha>`)
1. <categoria>: <...> (fonte: `<...>`)

## Não é achado aqui

- <padrão que um revisor de fora marcaria e que este repositório aceita> — <por quê> (fonte: `<...>`)

## Regras que o review confere

| Regra | Onde está |
| --- | --- |
| <regra> | `<AGENTS.md ou docs/agents/<arquivo>.md>` |
````

As prioridades saem do histórico de review (o que os revisores apontam
repetidamente) e, sem ele, dos commits de correção. Sem histórico de review,
escreva isso numa linha abaixo do título.

---

## `AGENTS.md` de pasta

Até 75 linhas, de 3 a 6 seções `##`. Três funções: inventário do que mora
aqui, convenção de nomes local e as uma ou duas armadilhas desta pasta.

Nunca repita da raiz: comandos, índice, fontes de verdade, conflito. Nunca
ligue para o guia de outra pasta. Os títulos não podem colidir com os da raiz.

````markdown
# <pasta>/ — <Papel>

<Parágrafo de abertura opcional. Permitido aqui; na raiz, não.>

## <Inventário: "Camadas" / "Serviços" / "Módulos">

| <Coisa> | <Uma oração cada> |
| --- | --- |
| `<nome>` | <o que é, distinguindo dos vizinhos> |

## <Convenção de nomes local>

<O padrão e um exemplo real de nome correto.>

## <A armadilha local>

<Mecanismo → consequência → imperativo. Negrito no token surpreendente.>
(fonte: `<commit ou arquivo:linha>`)
````

Caminhos citados aqui podem ser relativos à própria pasta.

---

## `workflow.md`

40 a 50 linhas. As regras que o agente segue antes de tocar em qualquer coisa.

````markdown
# Fluxo de trabalho

## Estratégia de modelo

<Opcional. Só se o repositório já declara qual modelo ou esforço usar (config
ou guia existente), com a fonte; nunca por suposição.>

- <tipo de tarefa> → <modelo>, <esforço> (fonte: `<arquivo:linha>`)

## Regras de trabalho

1. Leia os arquivos relevantes antes de afirmar qualquer coisa sobre o código.
1. <regra>
1. <regra — nunca commitar sem aprovação>
1. <regra — nunca fazer push, merge ou reescrever histórico sem aprovação>
1. <regras do projeto por último>

## <Modelo mental do pipeline>

```text
<ASCII do fluxo de dados em execução, se o projeto tiver um>
```
````

Imperativos numerados, uma situação cada. Menos de 6 e o agente perde casos;
mais de 20 e ele para de ler com atenção.

---

## `gotchas.md`

Até 140 linhas, uma `##` por armadilha, cerca de 6 linhas cada, sem
introdução, sem `###`.

````markdown
# Armadilhas

## <Afirmação, ou `X, não Y`>

<O mecanismo, com o símbolo exato.> <A consequência — diga que falha em
silêncio, sem aviso, quando for verdade.> <A correção: "Nunca X." / "Use Y.">
(fonte: `<commit ou arquivo:linha>`)
````

| Estilo de título | Exemplo |
|---|---|
| Regra contrastiva | `## UUID v7, não UUID v4` |
| Propriedade | `` ## `auth_data` é criptografado `` |
| Comportamento surpreendente | `` ## `make run` sempre reconstrói `` |
| Símbolo contra símbolo | `` ## `a.field` vs `b.field` `` |

Admissão: um desenvolvedor sênior razoável erraria isso, **e** o erro é
silencioso. Falha que faz barulho se ensina sozinha.

---

## `dont-touch.md`

Cerca de 45 linhas, quase só tabelas. Categorize pelo **motivo** de não mexer:
o veredito vai no título, o motivo numa coluna, a fonte na última.

````markdown
# Não mexer

## Gerados — nunca editar à mão

| Arquivo | Gerador | Regra | Fonte |
| --- | --- | --- | --- |
| `<caminho>` | `<comando>` | <regra e como regenerar> | `<arquivo:linha>` |

## Segredos — nunca commitar

| Arquivo | O que guarda | Fonte |
| --- | --- | --- |
| `<caminho>` | <conteúdo> | `.gitignore` |

Nunca commite nem registre em log o conteúdo deles.

## Configuração protegida — mudar com cuidado

| Arquivo | Risco | Fonte |
| --- | --- | --- |

## Arquivos mantidos à mão que precisam acompanhar mudanças

| Arquivo | O que quebra em silêncio se ficar para trás | Fonte |
| --- | --- | --- |
````

A quarta categoria é a que a maioria esquece. Um arquivo pode aparecer em
duas.

---

## `reuse.md`

Até 140 linhas. Responde "isso já existe?" antes de alguém criar.

````markdown
# Reuso

| Precisa de | Use | Onde | Fonte |
| --- | --- | --- | --- |
| <necessidade, em palavras de quem procura> | `<símbolo>` | `<caminho>` | `<commit>` ou <n> chamadores |
````

Admissão: helper que já foi recriado (commit de refatoração ou correção que
removeu a cópia) ou com três chamadores ou mais. Escreva a coluna "Precisa de"
com as palavras que alguém buscaria ("formatar data por extenso", "validar
CPF"), não com o nome do símbolo.

---

## `<unidade>-anatomy.md`

Cerca de 140 linhas. Toda base de código tem uma unidade que se repete: módulo
de domínio, pasta de feature, pacote, recurso. Dê o nome dela ao arquivo.

````markdown
# Anatomia de <unidade>

Toda <unidade> em `<caminho>/<nome>/` tem esta estrutura interna.

```text
<caminho>/<nome>/
  <arquivo>     # <papel> (<classe base ou contrato que implementa>)
  tests/
    <padrão>    # <o que cobrem>
```

## <arquivo>

```<linguagem>
<esqueleto mínimo que compila, imports reais, `...` no lugar do corpo,
 comentários com o porquê>
```

Regras:

- <o que o esqueleto não mostra>
- <um limite: o que nunca aparece neste arquivo>
````

Nunca ponha checklist ou procedimento aqui: este arquivo descreve o
estado-alvo; o procedimento vai numa receita. Se a estrutura não está em todas
as unidades, diga: "Status: <n> de <m> unidades seguem esta estrutura; ela é o
alvo, não o estado atual."

---

## `tests.md`

Cerca de 100 linhas. Taxonomia primeiro, julgamentos por último.

````markdown
# Testes

## Tipos de teste

| Tipo | Padrão de arquivo | Precisa de | Roda com |
| --- | --- | --- | --- |
| Unidade | `<padrão>` | <deps> | `<comando>` |
| Integração | `<padrão>` | <deps> | `<comando>` |

## <Fixtures / factories>

<O idioma do projeto, com um trecho real e o arquivo de exemplo:
"Veja `<arquivo de teste real>`".>

## Escrevendo testes

1. <no que fazer asserção>
1. <o que não testar>

## <Lição aprendida>

<Em forma de armadilha, com a fonte.>
````

---

## `code-style.md`

Cerca de 50 linhas.

````markdown
# Estilo de código

## Linter e formatador

<Ferramenta, caminho da config, o que difere do padrão, o comando.>

## Idioma

<Idioma dos identificadores, da prosa e das mensagens de commit.>

## Nomes

| Coisa | Convenção | Exemplo |
| --- | --- | --- |
| <tipo> | <regra> | `<exemplo real do repositório>` |

## Comentários

<Quando o comentário é obrigatório e quando é ruído.>
````

---

## `commits-prs.md`

Cerca de 50 linhas, terminando num checklist.

````markdown
# Commits e PRs

## <Convenção de commit>

| Tipo | Uso |
| --- | --- |
| `feat` | <…> |

```text
<de três a cinco assuntos reais tirados do histórico deste repositório>
```

## Branches

<Padrão e um exemplo real.>

## Hooks de pre-commit

<O que roda. Não pule com `--no-verify`: corrija o problema.>

## Checklist de PR

- [ ] `<comando de validação>` passa
- [ ] `<comando de teste>` passa
- [ ] <portão do projeto>
````

---

## `development.md`

Cerca de 75 linhas. Blocos de comando para copiar e tabelas de duas colunas.
Encolhe para poucas linhas quando tudo é padrão; isso é sucesso, não lacuna.

````markdown
# Desenvolvimento

## Setup inicial

```bash
<comandos, cada um com a parte não óbvia num comentário>
```

## <Portas fora do padrão>

| Serviço | Porta | Observação |
| --- | --- | --- |
| <nome> | **<porta>** | Não <a porta que todos assumiriam> |

## Variáveis de ambiente

| Variável | O que quebra sem ela |
| --- | --- |
| `<VAR>` | <...> |
````

---

## Tópico de subsistema

Um por subsistema que o agente erraria lendo só o código (autenticação,
deploy, jobs em background, uma integração difícil). Admissão: **já mordeu
alguém duas vezes.**

````markdown
# <Subsistema>

## Peças

<Um parágrafo: as partes e como se ligam.>

## <Fluxo>

1. <passo na sequência de execução>

## <Como declarar ou usar no código>

```<linguagem>
<o menor exemplo real>
```

## <Comportamento nos testes>

<Desligado, mockado ou real, e a armadilha de supor o contrário.>
````

---

## Receita

60 a 160 linhas, 6 a 13 passos. Roteiro, não referência.

````markdown
# Receita: <ação no imperativo>

## Pré-requisitos

- <estado necessário>

## 1. <Verbo no imperativo>

```bash
<comando para copiar, completo, sem "veja acima">
```

<Uma a três linhas com a regra ou o porquê, depois do código.>

## 2. <Verbo no imperativo>

```<linguagem>
<trecho com imports completos, placeholders `<nome>`, `...` no trabalho real>
```

<O modo de falha no ponto em que acontece, em negrito: "Sem isso, <ferramenta>
**não detecta** o novo <coisa>.">

## <n>. Rodar a validação

```bash
<comando de validação>
<comando de teste>
```

## <Operação inversa perigosa>

<Trecho sem número, por exemplo desfazer. A proibição: "Nunca <faça isso> em
ambiente compartilhado ou de produção.">
````

Regras das receitas:

- Passos são títulos `##` numerados que começam com verbo.
- A verificação é o passo final, não um campo de cada passo.
- O código vai na receita; não aponte um exemplo para copiar.
- Duplique passos que se repetem entre receitas em vez de ligar uma à outra.
- Sem tabelas, checkboxes ou emoji dentro de receitas.

Merece receita a tarefa feita mais de duas vezes, **e** com vários arquivos em
ordem fixa, **e** com ao menos um passo que não faz nada em silêncio quando é
pulado.
